"""Build P1 (arithmetic foundations) math questions: 500 T1 + 100 T2.

Generates structured drill questions covering every single-digit fact,
with 5 phrasings per fact, then runs validate_rewrite gate suite and
saves only PASS / SOFT_WARN to proposals/v2_audit/_math_p1_output.json.

T1 patterns:
  - Times tables 1-12 (with 5 phrasings each)
  - Addition within 20 (5 phrasings)
  - Subtraction within 20
  - Doubles
  - Halves
  - Make-a-ten bridging
  - Counting on
  - Skip counting
  - Missing addend
  - Fact families
  - Number bonds to 10
  - Even/odd

T2 patterns (multi-digit + named trick in context):
  - Multi-digit addition w/ carry
  - Multi-digit subtraction w/ borrow
  - Multi-digit × single-digit
  - Long division (small)
  - Place-value warm-ups
  - Divisibility-rule warm-ups
"""
from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

random.seed(42)  # determinism

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _format_int(n: int) -> str:
    """Format integer with unicode minus."""
    if n < 0:
        return f"−{abs(n)}"
    return str(n)


def _shuffle_choices(answer: int, distractors: list[int]) -> list[str]:
    """Return the 4 choices in randomized order, formatted as strings."""
    all_nums = [answer] + distractors
    # Dedupe (in case of accidental duplicates)
    seen = set()
    unique = []
    for n in all_nums:
        if n not in seen:
            seen.add(n)
            unique.append(n)
    # Pad if we lost any distractors (rare — bump by ±1, ±2)
    while len(unique) < 4:
        for delta in (1, -1, 2, -2, 3, -3, 5, -5):
            candidate = answer + delta
            if candidate not in seen and candidate != answer:
                seen.add(candidate)
                unique.append(candidate)
                if len(unique) >= 4:
                    break
        else:
            break
    random.shuffle(unique)
    return [_format_int(n) for n in unique[:4]]


def make_q(tier: int, question: str, answer: int, distractors: list[int], context: str) -> dict:
    """Build a question dict with shuffled choices."""
    choices = _shuffle_choices(answer, distractors)
    ans_str = _format_int(answer)
    # Make sure answer is in choices
    if ans_str not in choices:
        choices[-1] = ans_str
        random.shuffle(choices)
    return {
        "tier": tier,
        "question": question,
        "answer": ans_str,
        "choices": choices,
        "context": context,
    }


# --------------------------------------------------------------------------
# T1: Times tables drill (1-12)
# --------------------------------------------------------------------------

# Phrasings for "a × b" — vary across the bank to keep play fresh.
# We use 5 phrasings per fact: bare, reversed, "What is", groups-of, dot-form.
TIMES_PHRASINGS = [
    "{a} × {b} = ?",
    "{b} × {a} = ?",
    "What is {a} times {b}?",
    "{a} groups of {b} = ?",
    "{a} · {b} = ?",
]

# Common-error distractor pool for times tables:
# - Adjacent fact (a × b ± a or ± b)
# - Square confusion (a², b²)
# - Off-by-one in the product
# - Common mis-recall


def _times_table_distractors(a: int, b: int, answer: int) -> list[int]:
    """Return 3 distractors modeling common errors for a × b = answer."""
    pool: list[int] = []
    # Adjacent multiplication facts
    if a >= 2:
        pool.append((a - 1) * b)
    if b >= 2:
        pool.append(a * (b - 1))
    pool.append((a + 1) * b)
    pool.append(a * (b + 1))
    # Square confusions
    pool.append(a * a)
    pool.append(b * b)
    # Off-by-one (carrying error)
    pool.append(answer + 1)
    pool.append(answer - 1)
    # Sum confusion (kid forgot × and added)
    pool.append(a + b)
    # Dedupe + remove answer + remove negatives
    seen = {answer}
    out: list[int] = []
    for d in pool:
        if d in seen or d <= 0:
            continue
        seen.add(d)
        out.append(d)
    # Need at least 3, but also keep same order of magnitude (within 3x)
    out = [d for d in out if d >= max(1, answer // 3) and d <= answer * 3]
    random.shuffle(out)
    return out[:3] if len(out) >= 3 else out + [answer + 2, answer + 3, answer - 2][:3 - len(out)]


def gen_times_tables() -> list[dict]:
    """Generate times-tables drill questions, 1-12, 5 phrasings each.

    12 × 12 = 144 facts × 5 phrasings = 720 max. We sample down to ~360.
    """
    qs: list[dict] = []
    facts = []
    for a in range(1, 13):
        for b in range(1, 13):
            facts.append((a, b))
    # For each (a, b), pick how many phrasings (3-5 depending on coverage)
    for a, b in facts:
        answer = a * b
        # Skip if too trivial (a=1 or b=1) — emit fewer
        n_phrasings = 5 if (a >= 2 and b >= 2) else 3
        chosen = random.sample(TIMES_PHRASINGS, n_phrasings)
        for stem_tmpl in chosen:
            stem = stem_tmpl.format(a=a, b=b)
            distractors = _times_table_distractors(a, b, answer)
            # Context — vary across phrasings to keep diverse
            ctx_variants = [
                (f"Times-table fact: {a} × {b} = {answer}. Memorize the multiplication "
                 f"table — automatic recall is the foundation of all mental math."),
                (f"Times-table drill: {a} × {b} = {answer}. The {a} times table and the "
                 f"{b} times table both lead here — multiplication is commutative."),
                (f"Memorize: {a} × {b} = {answer}. Adjacent facts ({a} × {b-1 if b>1 else b+1} "
                 f"and {a+1 if a<12 else a-1} × {b}) live nearby — don't confuse them."),
                (f"Times-table fact: {a} × {b} = {answer}. Skip-counting by {a}: "
                 f"{', '.join(str(a*i) for i in range(1, min(b+1, 6)))}... reaches {answer} at step {b}."),
                (f"Times-table fact: {a} × {b} = {b} × {a} = {answer}. The commutative "
                 f"property of multiplication means order doesn't change the product."),
            ]
            ctx = random.choice(ctx_variants)
            qs.append(make_q(1, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T1: Addition within 20
# --------------------------------------------------------------------------

ADD_PHRASINGS = [
    "{a} + {b} = ?",
    "{b} + {a} = ?",
    "What is {a} plus {b}?",
    "Sum of {a} and {b} = ?",
    "Add {a} + {b}.",
]


def _addition_distractors(a: int, b: int, answer: int) -> list[int]:
    pool = [
        answer + 1, answer - 1, answer + 2, answer - 2,
        a + b + 10,  # carry-confused
        abs(a - b),  # subtracted instead
        a * b if a * b != answer and a * b < 30 else answer + 3,
    ]
    seen = {answer}
    out = []
    for d in pool:
        if d in seen or d < 0:
            continue
        seen.add(d)
        out.append(d)
    return out[:3]


def gen_addition_within_20() -> list[dict]:
    qs: list[dict] = []
    # All (a, b) pairs with a + b <= 20 and a, b in 1..10
    facts = []
    for a in range(1, 11):
        for b in range(1, 11):
            if a + b <= 20:
                facts.append((a, b))
    for a, b in facts:
        answer = a + b
        n_phrasings = 4 if (a >= 2 or b >= 2) else 2
        chosen = random.sample(ADD_PHRASINGS, min(n_phrasings, len(ADD_PHRASINGS)))
        for stem_tmpl in chosen:
            stem = stem_tmpl.format(a=a, b=b)
            distractors = _addition_distractors(a, b, answer)
            # Decide trick to teach in context
            if answer == 10:
                ctx = (f"Number bond to 10: {a} + {b} = 10. Pairs that make 10 are the "
                       f"foundation of mental addition — memorize: 1+9, 2+8, 3+7, 4+6, 5+5.")
            elif a + b > 10 and (a == b):
                ctx = (f"Doubles fact: {a} + {b} = {answer}. Doubles 1-10 are foundational; "
                       f"once you know doubles, near-doubles ({a}+{b+1}) come fast.")
            elif a + b > 10 and a != 10 and b != 10:
                # Make-a-ten bridging (only if neither is already 10)
                gap = 10 - max(a, b)
                rest = min(a, b) - gap
                ctx = (f"Make-a-ten trick: {max(a,b)} + {gap} = 10, then 10 + {rest} = {answer}. "
                       f"Bridge through 10 to add fast — split the smaller number to fill the ten.")
            elif a == 10 or b == 10:
                # Adding to 10 — no bridging needed, just place-value
                other = b if a == 10 else a
                ctx = (f"Place-value addition: 10 + {other} = {answer}. When one number is "
                       f"already 10, the answer keeps the 1 in the tens place and adds {other} "
                       f"in the ones. This is the foundation for the make-a-ten bridging trick.")
            else:
                ctx = (f"Counting on: start at {max(a,b)} and count up {min(a,b)} more. "
                       f"For small sums under 10, counting-on is faster than memorizing — "
                       f"but {a} + {b} = {answer} is also a fact family worth knowing.")
            qs.append(make_q(1, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T1: Subtraction within 20
# --------------------------------------------------------------------------

SUB_PHRASINGS = [
    "{a} − {b} = ?",
    "What is {a} minus {b}?",
    "Subtract: {a} − {b}.",
    "{a} take away {b} = ?",
    "Difference: {a} − {b} = ?",
]


def _subtraction_distractors(a: int, b: int, answer: int) -> list[int]:
    pool = [
        answer + 1, answer - 1, answer + 2, answer - 2,
        a + b,  # added instead
        b - a if b > a else a - b - 1,  # swapped
    ]
    seen = {answer}
    out = []
    for d in pool:
        if d in seen or d < 0:
            continue
        seen.add(d)
        out.append(d)
    return out[:3]


def gen_subtraction_within_20() -> list[dict]:
    qs: list[dict] = []
    facts = []
    for a in range(2, 21):
        for b in range(1, min(a, 11)):
            facts.append((a, b))
    for a, b in facts:
        answer = a - b
        n_phrasings = 3
        chosen = random.sample(SUB_PHRASINGS, n_phrasings)
        for stem_tmpl in chosen:
            stem = stem_tmpl.format(a=a, b=b)
            distractors = _subtraction_distractors(a, b, answer)
            # Trick in context
            if a > 10 and b > (a - 10):
                # Bridging-back-through-ten subtraction
                ctx = (f"Subtraction bridging: {a} − {b} = {a} − {a-10} − {b-(a-10)} = "
                       f"10 − {b-(a-10)} = {answer}. Break the subtrahend to land on 10, then subtract the rest.")
            elif a == b * 2:
                ctx = (f"Halves and doubles: since {b} + {b} = {a}, then {a} − {b} = {b}. "
                       f"Doubles facts work in reverse — subtracting half gives the other half.")
            else:
                ctx = (f"Fact families: {a} − {b} = {answer} and {b} + {answer} = {a} encode the same fact. "
                       f"Subtraction is the inverse of addition.")
            qs.append(make_q(1, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T1: Doubles
# --------------------------------------------------------------------------


def gen_doubles() -> list[dict]:
    qs: list[dict] = []
    phrasings = [
        "Double {a} = ?",
        "{a} + {a} = ?",
        "2 × {a} = ?",
        "What is double {a}?",
    ]
    for a in range(1, 13):
        answer = a * 2
        for stem_tmpl in phrasings:
            stem = stem_tmpl.format(a=a)
            distractors = [answer - 1, answer + 1, answer + 2, a + 1, a - 1]
            distractors = [d for d in distractors if d > 0 and d != answer][:3]
            ctx = (f"Doubles fact: {a} + {a} = {answer}. Doubles 1-12 are foundational; "
                   f"once you know them, near-doubles ({a}+{a+1}={answer+1}) come fast. "
                   f"Doubling is also halving in reverse.")
            qs.append(make_q(1, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T1: Halves
# --------------------------------------------------------------------------


def gen_halves() -> list[dict]:
    qs: list[dict] = []
    phrasings = [
        "Half of {a} = ?",
        "{a} ÷ 2 = ?",
        "What is half of {a}?",
        "{a} / 2 = ?",
    ]
    for a in range(2, 25, 2):
        answer = a // 2
        for stem_tmpl in phrasings:
            stem = stem_tmpl.format(a=a)
            distractors = [answer - 1, answer + 1, answer + 2, a - 1]
            distractors = [d for d in distractors if d > 0 and d != answer][:3]
            ctx = (f"Halving fact: half of {a} = {answer} (because {answer} + {answer} = {a}). "
                   f"Halving and doubling are inverse mental moves. To halve quickly: "
                   f"think of the doubles fact that gives {a}.")
            qs.append(make_q(1, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T1: Make-a-ten (explicit bridging questions)
# --------------------------------------------------------------------------


def gen_make_a_ten() -> list[dict]:
    qs: list[dict] = []
    phrasings = [
        "{a} + {b} = ?",
        "What is {a} + {b}?",
        "Bridge: {a} + {b} = ?",
    ]
    # Make-a-ten pairs: a + b > 10, a in 5..9, b in 2..9
    pairs = [(8, 5), (8, 6), (8, 7), (9, 4), (9, 5), (9, 6), (9, 7), (9, 8),
             (7, 5), (7, 6), (7, 4), (6, 5), (6, 7), (6, 8), (5, 7), (5, 8)]
    for a, b in pairs:
        answer = a + b
        gap = 10 - a
        rest = b - gap
        for stem_tmpl in phrasings:
            stem = stem_tmpl.format(a=a, b=b)
            distractors = [answer - 1, answer + 1, answer - 2, 10 + (b - gap - 1)]
            distractors = [d for d in distractors if d > 0 and d != answer][:3]
            ctx = (f"Make-a-ten trick: {a} + {gap} = 10, then 10 + {rest} = {answer}. "
                   f"Split the {b} into {gap} + {rest} so you can bridge through 10. "
                   f"Crossing the ten cleanly is the most important mental-addition move.")
            qs.append(make_q(1, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T1: Counting on
# --------------------------------------------------------------------------


def gen_counting_on() -> list[dict]:
    qs: list[dict] = []
    # Small additions where counting-on is natural (b ≤ 3)
    for a in range(2, 19):
        for b in range(1, 4):
            if a + b <= 20:
                answer = a + b
                phrasings = [
                    f"Count on from {a}: add {b}.",
                    f"{a} + {b} = ?",
                    f"Start at {a}, count up {b}. Result?",
                ]
                for stem in phrasings:
                    if len(stem) > 50:
                        continue
                    distractors = [answer + 1, answer - 1, answer + 2, a]
                    distractors = [d for d in distractors if d > 0 and d != answer][:3]
                    ctx = (f"Counting on: start at {a}, count up {b} → "
                           f"{', '.join(str(a + i) for i in range(1, b + 1))}. "
                           f"For small additions, counting on is faster than memorizing the fact.")
                    qs.append(make_q(1, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T1: Skip counting
# --------------------------------------------------------------------------


def gen_skip_counting() -> list[dict]:
    qs: list[dict] = []
    # Skip count by n: ..., next?
    skip_facts = [
        (2, [2, 4, 6, 8], 10),
        (2, [4, 6, 8, 10], 12),
        (2, [6, 8, 10, 12], 14),
        (3, [3, 6, 9, 12], 15),
        (3, [6, 9, 12, 15], 18),
        (3, [9, 12, 15, 18], 21),
        (4, [4, 8, 12, 16], 20),
        (4, [8, 12, 16, 20], 24),
        (5, [5, 10, 15, 20], 25),
        (5, [10, 15, 20, 25], 30),
        (5, [15, 20, 25, 30], 35),
        (6, [6, 12, 18, 24], 30),
        (6, [12, 18, 24, 30], 36),
        (7, [7, 14, 21, 28], 35),
        (8, [8, 16, 24, 32], 40),
        (9, [9, 18, 27, 36], 45),
        (10, [10, 20, 30, 40], 50),
        (10, [20, 30, 40, 50], 60),
        (11, [11, 22, 33, 44], 55),
        (12, [12, 24, 36, 48], 60),
    ]
    for step, seq, nxt in skip_facts:
        seq_str = ", ".join(str(x) for x in seq)
        stem = f"{seq_str}, ? — what comes next?"
        if len(stem) > 50:
            stem = f"{seq_str}, ?"
        distractors = [nxt + 1, nxt - 1, nxt + step, nxt - step]
        distractors = [d for d in distractors if d > 0 and d != nxt][:3]
        ctx = (f"Skip counting by {step}s: each step adds {step}. The sequence is "
               f"{step}, {2*step}, {3*step}, {4*step}, {5*step}, ... Skip counting "
               f"is the bridge between counting and multiplication ({step} × n).")
        qs.append(make_q(1, stem, nxt, distractors, ctx))
        # Also: shorter phrasing
        stem2 = f"Next: {seq_str}, ?"
        if len(stem2) <= 50:
            qs.append(make_q(1, stem2, nxt, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T1: Missing addend (5 + ? = 12)
# --------------------------------------------------------------------------


def gen_missing_addend() -> list[dict]:
    qs: list[dict] = []
    facts = []
    for total in range(5, 21):
        for known in range(1, total):
            missing = total - known
            if missing >= 1:
                facts.append((known, missing, total))
    random.shuffle(facts)
    facts = facts[:80]
    for known, missing, total in facts:
        phrasings = [
            f"{known} + ? = {total}",
            f"? + {known} = {total}",
            f"What plus {known} = {total}?",
        ]
        for stem in phrasings:
            if len(stem) > 50:
                continue
            distractors = [missing + 1, missing - 1, missing + 2, known]
            distractors = [d for d in distractors if d > 0 and d != missing][:3]
            ctx = (f"Missing addend: {known} + ? = {total} means ? = {total} − {known} = {missing}. "
                   f"Subtraction is the inverse of addition. Fact family: "
                   f"{known} + {missing} = {total}, {missing} + {known} = {total}, "
                   f"{total} − {known} = {missing}.")
            qs.append(make_q(1, stem, missing, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T1: Number bonds to 10
# --------------------------------------------------------------------------


def gen_number_bonds() -> list[dict]:
    qs: list[dict] = []
    bonds = [(1, 9), (2, 8), (3, 7), (4, 6), (5, 5), (6, 4), (7, 3), (8, 2), (9, 1)]
    for known, missing in bonds:
        phrasings = [
            f"{known} + ? = 10",
            f"What pairs with {known} to make 10?",
            f"{known} and ? make 10.",
            f"Bond to 10: {known} + ? = ?",
        ]
        for stem in phrasings:
            if len(stem) > 50:
                continue
            distractors = [missing + 1, missing - 1, 10 + known, known]
            distractors = [d for d in distractors if d > 0 and d != missing][:3]
            ctx = (f"Number bonds to 10: {known} + {missing} = 10. Memorize all "
                   f"bond-to-10 pairs (1+9, 2+8, 3+7, 4+6, 5+5) — they power the "
                   f"make-a-ten trick for all addition above 10.")
            qs.append(make_q(1, stem, missing, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T1: Fact families
# --------------------------------------------------------------------------


def gen_fact_families() -> list[dict]:
    qs: list[dict] = []
    families = [
        (3, 4, 7), (4, 5, 9), (5, 6, 11), (6, 7, 13), (7, 8, 15), (8, 9, 17),
        (2, 7, 9), (3, 5, 8), (4, 7, 11), (5, 8, 13), (6, 9, 15), (2, 9, 11),
        (3, 8, 11), (4, 9, 13), (5, 9, 14), (6, 8, 14), (7, 9, 16), (2, 5, 7),
    ]
    for a, b, c in families:
        # If a + b = c, then c − b = a
        phrasings = [
            f"If {a} + {b} = {c}, then {c} − {b} = ?",
            f"{a} + {b} = {c}. So {c} − {a} = ?",
        ]
        for stem in phrasings:
            if len(stem) > 50:
                continue
            # Answer depends on phrasing
            if f"− {b}" in stem:
                answer = a
            else:
                answer = b
            distractors = [answer + 1, answer - 1, c, a + b + 1]
            distractors = [d for d in distractors if d > 0 and d != answer][:3]
            ctx = (f"Fact family: {a} + {b} = {c}, {b} + {a} = {c}, {c} − {a} = {b}, "
                   f"{c} − {b} = {a} all encode the same fact. Three numbers, four equations — "
                   f"learn the family and you know inverse-op subtraction for free.")
            qs.append(make_q(1, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T1: Even / odd
# --------------------------------------------------------------------------


def gen_even_odd() -> list[dict]:
    qs: list[dict] = []
    for n in range(1, 25):
        if n % 2 == 0:
            answer_str = "even"
            wrong = "odd"
        else:
            answer_str = "odd"
            wrong = "even"
        stem = f"Is {n} even or odd?"
        ans = 1 if answer_str == "even" else 0
        wrong_val = 0 if answer_str == "even" else 1
        # We need integer choices — but answer is a word. Use yes/no via "even"/"odd" wrap.
        # Skip: this needs string choices. We'll build manually.
        choices = ["even", "odd", "neither", "both"]
        random.shuffle(choices)
        ctx = (f"Even / odd recognition: {n} is {answer_str}. Even numbers end in "
               f"0, 2, 4, 6, or 8 (divisible by 2). Odd numbers end in 1, 3, 5, 7, or 9.")
        q = {
            "tier": 1,
            "question": stem,
            "answer": answer_str,
            "choices": choices,
            "context": ctx,
        }
        qs.append(q)
    return qs


# --------------------------------------------------------------------------
# T1: Halves of larger evens (extending the halves coverage)
# --------------------------------------------------------------------------


def gen_extended_halves() -> list[dict]:
    qs: list[dict] = []
    for a in [16, 18, 20, 22, 24]:
        answer = a // 2
        phrasings = [
            f"Half of {a} = ?",
            f"What is half of {a}?",
            f"{a} ÷ 2 = ?",
        ]
        for stem in phrasings:
            if len(stem) > 50:
                continue
            distractors = [answer - 1, answer + 1, answer + 2, a - answer + 1]
            distractors = [d for d in distractors if d > 0 and d != answer][:3]
            ctx = (f"Halving: half of {a} = {answer} (because {answer} + {answer} = {a}). "
                   f"Halving is doubling in reverse. For {a}, think of the doubles fact "
                   f"that pairs {answer} with itself.")
            qs.append(make_q(1, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T2: Multi-digit addition with carry
# --------------------------------------------------------------------------

T2_ADD_PAIRS = [
    (234, 156), (345, 178), (456, 289), (567, 234), (678, 145),
    (123, 456), (234, 567), (345, 678), (456, 123), (567, 345),
    (148, 235), (267, 184), (319, 472), (528, 193), (746, 158),
    (382, 419), (293, 528), (471, 369), (584, 217), (635, 278),
    (39, 47), (58, 36), (74, 19), (87, 25), (65, 48),
]


def gen_t2_addition() -> list[dict]:
    qs: list[dict] = []
    for a, b in T2_ADD_PAIRS:
        answer = a + b
        stem = f"{a} + {b} = ?"
        # Carry-error distractors
        if answer >= 100:
            d1 = answer - 100  # forgot to carry hundreds
            d2 = answer + 10   # mis-carried tens
            d3 = answer - 10   # missed tens carry
            d4 = answer - 1    # off-by-one
        else:
            d1 = answer + 10
            d2 = answer - 10
            d3 = answer + 1
            d4 = answer - 1
        distractors = [d for d in [d1, d2, d3, d4] if d > 0 and d != answer][:3]
        # Context names the trick
        hundreds_a = (a // 100) * 100
        tens_a = (a // 10 % 10) * 10
        ones_a = a % 10
        hundreds_b = (b // 100) * 100
        tens_b = (b // 10 % 10) * 10
        ones_b = b % 10
        if a >= 100 or b >= 100:
            ctx = (f"Add-by-place-value trick: break each number into hundreds + tens + ones "
                   f"and add column by column. {a} + {b} = ({hundreds_a + hundreds_b}) + "
                   f"({tens_a + tens_b}) + ({ones_a + ones_b}) = {answer}. Watch for carries "
                   f"when a column sum exceeds 9.")
        else:
            ctx = (f"Add-by-tens-then-ones trick: {a} + {b} = {a} + {(b//10)*10} + {b%10} = "
                   f"{a + (b//10)*10} + {b%10} = {answer}. Break the second number into "
                   f"place-value chunks to avoid carrying mistakes.")
        qs.append(make_q(2, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T2: Multi-digit subtraction with borrow
# --------------------------------------------------------------------------

T2_SUB_PAIRS = [
    (523, 178), (645, 289), (734, 156), (812, 347), (901, 458),
    (456, 189), (567, 278), (623, 145), (789, 234), (834, 257),
    (321, 145), (438, 169), (519, 263), (627, 348), (715, 269),
    (82, 49), (93, 58), (74, 36), (85, 27), (96, 39),
    (137, 68), (215, 87), (304, 158), (412, 235), (501, 286),
]


def gen_t2_subtraction() -> list[dict]:
    qs: list[dict] = []
    for a, b in T2_SUB_PAIRS:
        answer = a - b
        stem = f"{a} − {b} = ?"
        d1 = answer + 10  # missed borrow
        d2 = answer - 10  # extra borrow
        d3 = answer + 1
        d4 = a - b - 100 if answer > 100 else answer + 100
        distractors = [d for d in [d1, d2, d3, d4] if d > 0 and d != answer][:3]
        # Use add-subtract-the-same trick for round-number subtraction
        # Otherwise borrow trick / column trick
        if a % 10 < b % 10:
            ctx = (f"Borrow shortcut: ones column {a%10} < {b%10} so borrow 1 from the tens. "
                   f"Or use the add-subtract-the-same trick: {a} − {b} = "
                   f"{a + (10 - b%10)} − {b + (10 - b%10)} = {answer}. Both work; "
                   f"the shortcut avoids the borrow entirely.")
        else:
            # Round-to-100 or add-subtract-the-same for clean cases
            ctx = (f"Add-subtract-the-same trick: round the subtrahend up to a clean number, "
                   f"then add the same amount to the minuend. {a} − {b} = {a + (10 - b%10) if b%10 > 0 else a} − "
                   f"{b + (10 - b%10) if b%10 > 0 else b} = {answer}. Inverse-operation check: "
                   f"{answer} + {b} should equal {a}.")
        qs.append(make_q(2, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T2: Multi-digit × single-digit
# --------------------------------------------------------------------------

T2_MUL_PAIRS = [
    (23, 4), (34, 5), (45, 6), (56, 7), (67, 8), (78, 9),
    (12, 8), (15, 7), (18, 6), (24, 9), (36, 5), (42, 4),
    (13, 6), (17, 4), (19, 5), (21, 7), (25, 8), (29, 3),
    (123, 4), (234, 3), (145, 2), (267, 3),
]


def gen_t2_multiplication() -> list[dict]:
    qs: list[dict] = []
    for a, b in T2_MUL_PAIRS:
        answer = a * b
        stem = f"{a} × {b} = ?"
        # Distractors: forgot to carry, dropped a digit, off-by-magnitude-of-b
        d1 = answer - 10
        d2 = answer + 10
        d3 = answer - b
        d4 = answer + b
        distractors = [d for d in [d1, d2, d3, d4] if d > 0 and d != answer][:3]
        # Distributive trick
        tens = (a // 10) * 10
        ones = a % 10
        if a < 100:
            ctx = (f"Distributive property: {a} × {b} = ({tens} + {ones}) × {b} = "
                   f"{tens * b} + {ones * b} = {answer}. Break the multi-digit number "
                   f"into place-value pieces, multiply each, add the partials.")
        else:
            hundreds = (a // 100) * 100
            rest = a - hundreds
            ctx = (f"Distributive property: {a} × {b} = ({hundreds} + {rest}) × {b} = "
                   f"{hundreds * b} + {rest * b} = {answer}. Place-value decomposition "
                   f"makes multi-digit multiplication mental.")
        qs.append(make_q(2, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T2: Long division (small dividends)
# --------------------------------------------------------------------------

T2_DIV_PAIRS = [
    (96, 4), (84, 7), (72, 6), (90, 5), (108, 9),
    (144, 12), (132, 11), (156, 12), (168, 8), (192, 6),
    (210, 7), (225, 9), (256, 8), (288, 9), (324, 6),
    (78, 6), (91, 7), (104, 8), (117, 9), (130, 10),
]


def gen_t2_division() -> list[dict]:
    qs: list[dict] = []
    for a, b in T2_DIV_PAIRS:
        answer = a // b
        stem = f"{a} ÷ {b} = ?"
        d1 = answer + 1
        d2 = answer - 1
        d3 = answer + 2
        d4 = a - b * answer + answer
        distractors = [d for d in [d1, d2, d3, d4] if d > 0 and d != answer][:3]
        ctx = (f"Long-division shortcut: think 'how many times does {b} go into {a}?'. "
               f"{b} × {answer} = {a}, so {a} ÷ {b} = {answer}. Use the inverse-operation "
               f"check: {answer} × {b} should equal {a}. Division is multiplication backwards.")
        qs.append(make_q(2, stem, answer, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T2: Place-value identification
# --------------------------------------------------------------------------


def gen_t2_place_value() -> list[dict]:
    qs: list[dict] = []
    place_facts = [
        (3456, "hundreds", 4),
        (7821, "tens", 2),
        (5093, "ones", 3),
        (4276, "thousands", 4),
        (8154, "hundreds", 1),
        (9367, "tens", 6),
        (2548, "ones", 8),
        (6741, "thousands", 6),
        (1839, "hundreds", 8),
        (5462, "tens", 6),
    ]
    for num, place, digit in place_facts:
        stem = f"What digit is in the {place} place of {num}?"
        if len(stem) > 100:
            continue
        # Distractors: other digits in the number, but constrained to same order of magnitude
        all_digits = [int(c) for c in str(num)]
        # Prefer adjacent digits (digit ± 1, ± 2) for magnitude safety
        adjacent_pool = [(digit + 1) % 10, (digit - 1) % 10, (digit + 2) % 10, (digit - 2) % 10]
        # Build distractors: filter all_digits + adjacent_pool, keep same magnitude
        candidates = list(set(all_digits + adjacent_pool))
        # Keep distractors within same order of magnitude as digit
        # Magnitude check: every distractor must be within 3x of digit (and digit within 3x of distractor)
        if digit == 0:
            candidates = [c for c in candidates if c == 0 or c <= 2]
        elif digit <= 2:
            candidates = [c for c in candidates if c >= 1 and c <= 4]
        else:
            candidates = [c for c in candidates if c >= max(1, digit // 3) and c <= digit * 3]
        distractors = [c for c in candidates if c != digit][:3]
        # Pad if needed with digit ± small offsets
        while len(distractors) < 3:
            for delta in (1, -1, 2, -2):
                cand = digit + delta
                if 0 <= cand <= 9 and cand != digit and cand not in distractors:
                    distractors.append(cand)
                    if len(distractors) >= 3:
                        break
            else:
                break
        # Ensure 3 distractors
        distractors = distractors[:3]
        ctx = (f"Place-value trick: read right-to-left as ones, tens, hundreds, thousands. "
               f"In {num} = {(num//1000)*1000} + {((num//100)%10)*100} + {((num//10)%10)*10} + {num%10}, "
               f"the {place} place holds {digit}. Each place is 10× the place to its right.")
        qs.append(make_q(2, stem, digit, distractors, ctx))
    return qs


# --------------------------------------------------------------------------
# T2: Divisibility-rule warm-ups
# --------------------------------------------------------------------------


def gen_t2_divisibility() -> list[dict]:
    qs: list[dict] = []
    facts = [
        (234, 2, True), (235, 2, False), (567, 3, True), (568, 3, False),
        (440, 4, True), (441, 4, False), (125, 5, True), (124, 5, False),
        (612, 6, True), (613, 6, False), (729, 9, True), (730, 9, False),
        (480, 10, True), (481, 10, False), (132, 3, True), (245, 5, True),
        (156, 4, True), (216, 9, False), (324, 9, True), (180, 6, True),
    ]
    for num, div, is_div in facts:
        stem = f"Is {num} divisible by {div}?"
        if len(stem) > 100:
            continue
        # Word-only choices so shape parity is consistent
        choices = ["yes", "no", "maybe", "depends"]
        random.shuffle(choices)
        ans = "yes" if is_div else "no"
        # Build rule context
        rules = {
            2: "Divisibility by 2: last digit is even (0, 2, 4, 6, 8).",
            3: "Divisibility by 3: the digit sum is divisible by 3.",
            4: "Divisibility by 4: the last two digits form a number divisible by 4.",
            5: "Divisibility by 5: last digit is 0 or 5.",
            6: "Divisibility by 6: number is divisible by both 2 AND 3.",
            9: "Divisibility by 9: the digit sum is divisible by 9.",
            10: "Divisibility by 10: last digit is 0.",
        }
        ctx = (f"{rules.get(div, '')} For {num}: " +
               (f"the test passes — {num} ÷ {div} works cleanly."
                if is_div else f"the test fails — {num} leaves a remainder when divided by {div}."))
        q = {
            "tier": 2,
            "question": stem,
            "answer": ans,
            "choices": choices,
            "context": ctx,
        }
        qs.append(q)
    return qs


# --------------------------------------------------------------------------
# Main: build, validate, save
# --------------------------------------------------------------------------


def main():
    print("Building T1 questions per category...")
    # Build each category separately so we can budget allocation
    cat_t1: dict[str, list[dict]] = {
        "times_tables": gen_times_tables(),
        "addition_within_20": gen_addition_within_20(),
        "subtraction_within_20": gen_subtraction_within_20(),
        "doubles": gen_doubles(),
        "halves": gen_halves(),
        "make_a_ten": gen_make_a_ten(),
        "counting_on": gen_counting_on(),
        "skip_counting": gen_skip_counting(),
        "missing_addend": gen_missing_addend(),
        "number_bonds": gen_number_bonds(),
        "fact_families": gen_fact_families(),
        "even_odd": gen_even_odd(),
        "extended_halves": gen_extended_halves(),
    }
    for cat, qs in cat_t1.items():
        print(f"  {cat}: {len(qs)} candidates")
    t1_questions = []
    for qs in cat_t1.values():
        t1_questions.extend(qs)
    print(f"  Total T1 candidates: {len(t1_questions)}")

    print("Building T2 questions...")
    t2_questions: list[dict] = []
    t2_questions.extend(gen_t2_addition())
    t2_questions.extend(gen_t2_subtraction())
    t2_questions.extend(gen_t2_multiplication())
    t2_questions.extend(gen_t2_division())
    t2_questions.extend(gen_t2_place_value())
    t2_questions.extend(gen_t2_divisibility())
    print(f"  Generated {len(t2_questions)} T2 candidates")

    all_candidates = t1_questions + t2_questions
    print(f"\nTotal candidates: {len(all_candidates)}")

    # Validate
    print("\nValidating...")
    bank: list[dict] = []
    dup, ans = build_bank_indices(bank)
    passed: list[dict] = []
    fail_reasons: dict[str, int] = {}
    fail_examples: dict[str, str] = {}
    seen_pairs: set[tuple[str, str]] = set()  # in-batch dedupe (stem, answer)
    for q in all_candidates:
        # Skip exact duplicates within batch
        pair = (q["question"], q["answer"])
        if pair in seen_pairs:
            continue
        r = validate_rewrite("math", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=None)
        if r["verdict"] in ("PASS", "SOFT_WARN"):
            passed.append(q)
            seen_pairs.add(pair)
        else:
            for g, msg in r["hard_fails"]:
                fail_reasons[g] = fail_reasons.get(g, 0) + 1
                if g not in fail_examples:
                    fail_examples[g] = f"T{q['tier']}: {q['question'][:60]} | {msg[:80]}"

    print(f"\n  PASSED: {len(passed)} / {len(all_candidates)}")
    print(f"  FAILED: {len(all_candidates) - len(passed)}")
    if fail_reasons:
        print(f"\n  Fail breakdown:")
        for g, n in sorted(fail_reasons.items(), key=lambda x: -x[1]):
            ex = fail_examples.get(g, '').encode('ascii', 'replace').decode('ascii')
            print(f"    {g}: {n}  ({ex})")

    # T1 / T2 split in passed
    t1_pass_set = {id(q) for q in passed if q["tier"] == 1}
    t2_pass_set = {id(q) for q in passed if q["tier"] == 2}
    t1_pass = [q for q in passed if q["tier"] == 1]
    t2_pass = [q for q in passed if q["tier"] == 2]
    print(f"\n  T1 passed: {len(t1_pass)}  (target 500)")
    print(f"  T2 passed: {len(t2_pass)}  (target 100)")

    # T1: budget per category. Target 500 split across categories with priority
    # to times-tables (the most-drilled fact set) per framework §10.
    # Budgets sum to ~500 to avoid random trim cutting times-tables coverage.
    cat_budget_t1 = {
        "times_tables": 190,        # 78 unordered facts ≈ 2.4 phrasings each
        "addition_within_20": 75,
        "subtraction_within_20": 55,
        "doubles": 24,              # 12 facts × 2
        "halves": 26,
        "make_a_ten": 32,
        "counting_on": 16,
        "skip_counting": 14,
        "missing_addend": 18,
        "number_bonds": 8,          # 9 facts
        "fact_families": 18,
        "even_odd": 12,
        "extended_halves": 12,
    }
    # Sum = 500 exactly

    # For times-tables specifically: stratify by fact to guarantee coverage.
    def _stratify_times_tables(qs: list[dict], budget: int) -> list[dict]:
        """Group times-tables questions by (a,b) pair and sample evenly so
        every fact appears at least 2x and total ≈ budget."""
        # Extract fact from context: "Times-table fact: a × b = c" or similar
        groups: dict[tuple[int, int], list[dict]] = {}
        for q in qs:
            ctx = q.get("context", "")
            m = re.search(r"(\d+)\s*[×]\s*(\d+)\s*=\s*\d+", ctx)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                key = (min(a, b), max(a, b))
                groups.setdefault(key, []).append(q)
        # All 78 unordered facts (1..12 × 1..12)
        all_facts = [(a, b) for a in range(1, 13) for b in range(a, 13)]
        per_fact = max(1, budget // len(all_facts))
        out: list[dict] = []
        for fact in all_facts:
            qs_for_fact = groups.get(fact, [])
            random.shuffle(qs_for_fact)
            out.extend(qs_for_fact[:per_fact])
        # Top up to budget with extra phrasings
        if len(out) < budget:
            existing = {id(q) for q in out}
            extras = [q for q in qs if id(q) not in existing]
            random.shuffle(extras)
            out.extend(extras[:budget - len(out)])
        return out[:budget]

    import re
    # Sample each category up to its budget from PASSED questions in that category
    final_t1: list[dict] = []
    for cat, qs in cat_t1.items():
        # Keep only ones that passed validation
        passed_in_cat = [q for q in qs if id(q) in t1_pass_set]
        budget = cat_budget_t1.get(cat, 0)
        if cat == "times_tables":
            final_t1.extend(_stratify_times_tables(passed_in_cat, budget))
        else:
            random.shuffle(passed_in_cat)
            final_t1.extend(passed_in_cat[:budget])

    # Top-up to 500 with leftover times-tables (the most-important fact pool)
    if len(final_t1) < 500:
        existing_ids = {id(q) for q in final_t1}
        leftover_times = [q for q in cat_t1["times_tables"]
                          if id(q) in t1_pass_set and id(q) not in existing_ids]
        random.shuffle(leftover_times)
        need = 500 - len(final_t1)
        final_t1.extend(leftover_times[:need])

    # If still short, top up with any remaining passing T1
    if len(final_t1) < 500:
        existing_ids = {id(q) for q in final_t1}
        leftover_any = [q for q in t1_pass if id(q) not in existing_ids]
        random.shuffle(leftover_any)
        need = 500 - len(final_t1)
        final_t1.extend(leftover_any[:need])

    # If over 500 (shouldn't be), trim
    if len(final_t1) > 500:
        random.shuffle(final_t1)
        final_t1 = final_t1[:500]

    t1_pass = final_t1

    # T2: 100 — keep proportional distribution across categories
    if len(t2_pass) > 100:
        random.shuffle(t2_pass)
        t2_pass = t2_pass[:100]

    final = t1_pass + t2_pass
    print(f"\n  Final: {len(final)} (T1={len(t1_pass)}, T2={len(t2_pass)})")

    # Save
    out_path = "proposals/v2_audit/_math_p1_output.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved to {out_path}")

    # Sample 10 for spot-check
    print("\n10-question sample:")
    sample = random.sample(final, min(10, len(final)))
    for i, q in enumerate(sample, 1):
        def _ascii(s): return s.encode('ascii', 'replace').decode('ascii')
        print(f"\n  [{i}] T{q['tier']} {_ascii(q['question'])}")
        print(f"      answer: {_ascii(q['answer'])}")
        print(f"      choices: {[_ascii(c) for c in q['choices']]}")
        print(f"      context: {_ascii(q['context'][:120])}...")


if __name__ == "__main__":
    main()
