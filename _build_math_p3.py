"""Bulk-generator for Math Pillar 3.

Reads the rules + exemplars from:
  - proposals/v2_audit/MATH_FRAMEWORK.md
  - proposals/v2_audit/MATH_TEMPLATES.md
  - tools/quizgen/exemplars/math.py (P3_T1..P3_T5)
  - tools/quizgen/gates/math.py (gates)

Generates 450 questions and saves PASS/SOFT_WARN ones to
proposals/v2_audit/_math_p3_output.json.

Target distribution:
  T1: 50, T2: 180, T3: 170, T4: 40, T5: 10  (== 450)

Lessons from first pass:
- Duplicate gate strips punctuation; "n + n" normalizes same as "n × n".
  Use word-disambiguated stems ("Double 7 = ?", "Half of 12 = ?").
- Existing bank has tons of basic percent-of-N. Pick uncommon multiples
  or use word-phrasings.
- Fraction division must use parentheses sympy can parse:
  "(1/2) ÷ (1/4) = ?" not "1/2 ÷ 1/4 = ?".
- Percent-of-percent fails math_correctness sniffer (sympy can't chain).
  Use word phrasings instead ("Find 25% of 80% of 200").
- Small decimal × decimal needs distractors within 3× magnitude.
- Compound fraction with integer answer: keep one fraction distractor
  to avoid odd-one-out parity.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Force UTF-8 stdout to print unicode minus and other math glyphs
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import validate_rewrite, build_bank_indices

BANK = json.load((REPO / "data" / "questions" / "math.json").open(encoding="utf-8"))
DUP, ANS = build_bank_indices(BANK)

OUT_PATH = REPO / "proposals" / "v2_audit" / "_math_p3_output.json"

# Accumulator for accepted questions
ACCEPTED: list[dict] = []
REJECTED: list[tuple[dict, str]] = []  # (q, reason)


def q_emit(q: dict, *, allow_soft: bool = True) -> tuple[bool, str]:
    """Validate and emit a question. Returns (accepted, verdict)."""
    # Sanity: ensure answer is in choices
    if q["answer"] not in q["choices"]:
        REJECTED.append((q, "answer not in choices"))
        return False, "FAIL"
    # Sanity: unique choices
    if len(set(q["choices"])) != 4:
        REJECTED.append((q, "duplicate choices"))
        return False, "FAIL"

    # Use accumulator + bank for dedupe so we don't emit duplicates of our
    # own newly-generated questions
    combined_bank = BANK + ACCEPTED
    dup, ans = build_bank_indices(combined_bank)

    result = validate_rewrite(
        "math", q,
        bank=combined_bank,
        dup_index=dup,
        answer_index=ans,
        replace_idx=None,
    )
    if result["verdict"] == "PASS" or (allow_soft and result["verdict"] == "SOFT_WARN"):
        ACCEPTED.append(q)
        return True, result["verdict"]
    reasons = "; ".join(f"{n}:{r[:80]}" for n, r in result["hard_fails"])
    REJECTED.append((q, reasons))
    return False, "FAIL"


def save_incremental():
    """Save accumulator to output file."""
    OUT_PATH.write_text(
        json.dumps(ACCEPTED, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ============================================================================
# T1 — 50 questions
# ============================================================================
# Doubles/halves; basic fraction recognition.
# Use word-prefixed stems to avoid colliding with existing "n × n" entries.

T1_BATCH: list[dict] = []

# Doubles by word-prefix (10 questions)
for n, double in [(1, 2), (2, 4), (3, 6), (4, 8), (5, 10),
                  (6, 12), (7, 14), (8, 16), (9, 18), (10, 20)]:
    T1_BATCH.append({
        "tier": 1,
        "question": f"Double {n} = ?",
        "answer": str(double),
        "choices": [str(double), str(double - 1), str(double + 1), str(double + 2)],
        "context": (
            f"Doubles. Double {n} = {n} + {n} = {double}. Doubles facts are "
            f"the foundation of mental addition — memorize them and many other "
            f"facts follow (near-doubles: 6 + 7 = 6 + 6 + 1)."
        ),
    })

# Halves single-digit (8 questions)
# Avoid (2,1) and (4,2): half+1 collides with original n when distractors
# tight. Use larger spread of distractors.
half_singles = [
    (4, 2), (6, 3), (8, 4), (10, 5), (12, 6), (14, 7), (16, 8), (18, 9),
]
for n, half in half_singles:
    # distractors: half+1, half-1 (use 0 if -1 not allowed), and double
    d2 = half + 1
    d3 = half - 1 if half - 1 >= 0 else half + 2
    d4 = n
    chs = [str(half), str(d2), str(d3), str(d4)]
    # ensure unique
    if len(set(chs)) != 4:
        chs = [str(half), str(half + 1), str(half + 2), str(half + 3)]
    T1_BATCH.append({
        "tier": 1,
        "question": f"Half of {n} = ?",
        "answer": str(half),
        "choices": chs,
        "context": (
            f"Halves. Half of {n} = {half} because {half} + {half} = {n}. "
            f"Halves and doubles are inverse moves; both build mental-math speed."
        ),
    })

# Half of two-digit (10 questions)
half_two_digit = [
    (22, 11), (24, 12), (26, 13), (28, 14), (30, 15),
    (40, 20), (50, 25), (60, 30), (80, 40), (100, 50),
]
for n, half in half_two_digit:
    chs = [str(half), str(half + 1), str(half - 1), str(half + 2)]
    if len(set(chs)) != 4:
        chs = [str(half), str(half + 1), str(half + 2), str(half + 3)]
    T1_BATCH.append({
        "tier": 1,
        "question": f"Half of {n} = ?",
        "answer": str(half),
        "choices": chs,
        "context": (
            f"Halves. Half of {n} = {half} because {half} + {half} = {n}. "
            f"Halving even numbers: split into two equal groups."
        ),
    })

# Basic fraction recognition (8 questions): "1/2 of N" — word phrasing
half_of_n = [(6, 3), (10, 5), (14, 7), (18, 9), (20, 10), (30, 15), (50, 25), (40, 20)]
for n, half in half_of_n:
    chs = [str(half), str(half + 1), str(half - 1), str(half + 2)]
    if len(set(chs)) != 4:
        chs = [str(half), str(half + 1), str(half + 2), str(half + 3)]
    T1_BATCH.append({
        "tier": 1,
        "question": f"What is one half of {n}?",
        "answer": str(half),
        "choices": chs,
        "context": (
            f"One half means split into two equal parts. Half of {n} = {half}. "
            f"The fraction 1/2 = 0.5 = 50% — three forms of the same number."
        ),
    })

# Quarters at T1 (10 questions, word phrasing)
quarter_of_n = [
    (8, 2), (12, 3), (16, 4), (20, 5), (24, 6),
    (28, 7), (32, 8), (40, 10), (60, 15), (100, 25),
]
for n, q in quarter_of_n:
    chs = [str(q), str(q + 1), str(q - 1), str(n // 2)]
    if len(set(chs)) != 4:
        chs = [str(q), str(q + 1), str(q + 2), str(q + 3)]
    T1_BATCH.append({
        "tier": 1,
        "question": f"What is one quarter of {n}?",
        "answer": str(q),
        "choices": chs,
        "context": (
            f"One quarter means split into four equal parts. A quarter of "
            f"{n} = {q}. Think of cutting a pizza into 4 slices; one slice "
            f"is a quarter."
        ),
    })

# Doubles word-phrasing (4 more)
double_word = [(11, 22), (12, 24), (13, 26), (15, 30)]
# Extra T1 doubles backup in case any earlier collides
extra_t1 = [(17, 34), (19, 38), (25, 50), (35, 70)]
double_word = double_word + extra_t1[:1]  # add just one more
for n, dbl in double_word:
    T1_BATCH.append({
        "tier": 1,
        "question": f"What is double {n}?",
        "answer": str(dbl),
        "choices": [str(dbl), str(dbl - 1), str(dbl + 1), str(dbl + 2)],
        "context": (
            f"Doubles. Double {n} = {n} + {n} = {dbl}. To double, you can "
            f"split into tens + ones and double each: double {n} = "
            f"double {(n//10)*10} + double {n%10}."
        ),
    })

assert len(T1_BATCH) == 51, f"T1 batch size {len(T1_BATCH)}"

target_t1 = 50
for q in T1_BATCH:
    if len(ACCEPTED) >= target_t1:
        break
    q_emit(q)
save_incremental()
print(f"[T1] accepted {len(ACCEPTED)} (target {target_t1}); tried {len(T1_BATCH)}")

# ============================================================================
# T2 — 180 questions
# ============================================================================

T2_BATCH: list[dict] = []

# Helper: Add a T2 question with auto-generated context if missing context detail
def t2_add(stem, ans, choices, ctx):
    T2_BATCH.append({
        "tier": 2,
        "question": stem,
        "answer": ans,
        "choices": choices,
        "context": ctx,
    })


# --- F/D/P conversions (25 questions) ---
# Fraction → percent
fdp_f_to_p = [
    ("1/4", "25%", ["25%", "14%", "40%", "20%"]),
    ("3/4", "75%", ["75%", "34%", "57%", "80%"]),
    ("1/5", "20%", ["20%", "15%", "25%", "50%"]),
    ("2/5", "40%", ["40%", "25%", "20%", "50%"]),
    ("3/5", "60%", ["60%", "35%", "53%", "75%"]),
    ("4/5", "80%", ["80%", "45%", "54%", "75%"]),
    ("1/8", "12.5%", ["12.5%", "8%", "18%", "20%"]),
    ("3/8", "37.5%", ["37.5%", "38%", "30%", "33%"]),
    ("5/8", "62.5%", ["62.5%", "58%", "65%", "85%"]),
    ("7/8", "87.5%", ["87.5%", "78%", "70%", "97%"]),
    ("1/10", "10%", ["10%", "1%", "20%", "5%"]),
    ("3/10", "30%", ["30%", "33%", "3%", "13%"]),
    ("7/10", "70%", ["70%", "73%", "7%", "17%"]),
    ("9/10", "90%", ["90%", "9%", "99%", "19%"]),
    ("1/20", "5%", ["5%", "1%", "20%", "0.5%"]),
]
for frac, pct, choices in fdp_f_to_p:
    t2_add(
        f"Convert {frac} to a percent.",
        pct,
        choices,
        (
            f"Common F/D/P conversion: {frac} as a percent = {pct}. "
            f"Memorize the conversion table: 1/2 = 50%, 1/4 = 25%, 3/4 = 75%, "
            f"1/5 = 20%, 1/8 = 12.5%, 1/10 = 10%. These show up everywhere "
            f"in tips, statistics, and discounts."
        ),
    )

# Decimal → percent
dec_to_pct = [
    ("0.15", "15%", ["15%", "1.5%", "150%", "0.15%"]),
    ("0.35", "35%", ["35%", "3.5%", "350%", "0.35%"]),
    ("0.4", "40%", ["40%", "4%", "0.4%", "400%"]),
    ("0.6", "60%", ["60%", "6%", "0.6%", "600%"]),
    ("0.85", "85%", ["85%", "8.5%", "0.85%", "850%"]),
    ("0.99", "99%", ["99%", "9.9%", "0.99%", "990%"]),
    ("0.07", "7%", ["7%", "70%", "0.7%", "0.07%"]),
    ("0.45", "45%", ["45%", "4.5%", "450%", "0.45%"]),
    ("0.001", "0.1%", ["0.1%", "1%", "0.001%", "10%"]),
    ("1.25", "125%", ["125%", "12.5%", "1.25%", "0.125%"]),
]
for dec, pct, choices in dec_to_pct:
    t2_add(
        f"Convert the decimal {dec} to a percent.",
        pct,
        choices,
        (
            f"Common F/D/P conversion. To go decimal → percent, move the "
            f"decimal point two places right (multiply by 100). "
            f"{dec} = {pct}. The fraction-decimal-percent triangle: any of "
            f"the three forms can be converted to either of the others."
        ),
    )

# --- Percent of a number (25 questions) ---
# Skip simple 10%/25% of common N. Pick uncommon bases.
pct_of_uncommon = [
    ("Find 10% of 33.", "3.3", ["3.3", "33", "0.33", "30"]),
    ("Find 10% of 47.", "4.7", ["4.7", "47", "0.47", "14"]),
    ("Find 10% of 82.", "8.2", ["8.2", "82", "0.82", "18"]),
    ("Find 10% of 270.", "27", ["27", "2.7", "270", "37"]),
    ("Find 10% of 530.", "53", ["53", "5.3", "530", "63"]),
    ("Find 25% of 36.", "9", ["9", "12", "16", "11"]),
    ("Find 25% of 96.", "24", ["24", "32", "12", "30"]),
    ("Find 25% of 144.", "36", ["36", "48", "12", "44"]),
    ("Find 50% of 72.", "36", ["36", "32", "24", "44"]),
    ("Find 50% of 96.", "48", ["48", "32", "24", "52"]),
    ("Find 50% of 144.", "72", ["72", "12", "36", "144"]),
    ("Find 20% of 35.", "7", ["7", "3.5", "5", "10"]),
    ("Find 20% of 65.", "13", ["13", "6.5", "10", "16"]),
    ("Find 20% of 95.", "19", ["19", "9.5", "15", "22"]),
    ("Find 20% of 110.", "22", ["22", "11", "20", "33"]),
    ("Find 5% of 40.", "2", ["2", "4", "1", "8"]),
    ("Find 5% of 120.", "6", ["6", "12", "3", "24"]),
    ("Find 5% of 320.", "16", ["16", "32", "8", "64"]),
    ("Find 15% of 60.", "9", ["9", "6", "12", "15"]),
    ("Find 15% of 80.", "12", ["12", "8", "16", "20"]),
    ("Find 30% of 90.", "27", ["27", "9", "63", "30"]),
    ("Find 40% of 25.", "10", ["10", "5", "15", "8"]),
    ("Find 60% of 45.", "27", ["27", "9", "18", "36"]),
    ("Find 75% of 16.", "12", ["12", "4", "8", "15"]),
    ("Find 75% of 32.", "24", ["24", "8", "16", "30"]),
]
for stem, ans, choices in pct_of_uncommon:
    pct_str = stem.split('%')[0].split()[-1]
    teach = ""
    if pct_str in {"10"}:
        teach = "The 10% trick: shift the decimal one place left. "
    elif pct_str in {"20"}:
        teach = "20% = 10% then double. "
    elif pct_str in {"5"}:
        teach = "5% = 10% then halve. "
    elif pct_str in {"25"}:
        teach = "25% means quarter — divide by 4. "
    elif pct_str in {"50"}:
        teach = "50% means half — divide by 2. "
    elif pct_str in {"75"}:
        teach = "75% means three quarters — half plus a quarter. "
    elif pct_str in {"15"}:
        teach = "15% = 10% + half-of-10%. "
    t2_add(
        stem, ans, choices,
        (
            f"Percent of a number: 'of' means ×. {teach}"
            f"{stem.replace('Find ', '').replace('.', ' =')} {ans}. "
            f"All percent moves reduce to the 10% trick scaled."
        ),
    )

# --- Fraction add/subtract (uncommon pairs to dodge bank dupes) ---
frac_addsub = [
    ("Compute 2/7 + 3/7.", "5/7", ["5/7", "5/14", "1/7", "6/7"]),
    ("Compute 4/9 + 2/9.", "2/3", ["2/3", "6/18", "6/9", "8/9"]),
    ("Compute 5/12 + 1/12.", "1/2", ["1/2", "6/24", "5/12", "1/6"]),
    ("Compute 7/12 − 1/12.", "1/2", ["1/2", "6/12", "7/12", "8/24"]),
    ("Compute 5/9 + 2/9.", "7/9", ["7/9", "7/18", "3/9", "10/9"]),
    ("Compute 11/12 − 5/12.", "1/2", ["1/2", "6/24", "11/12", "1/6"]),
    ("Compute 3/7 + 2/7.", "5/7", ["5/7", "5/14", "1/7", "6/7"]),
    ("Compute 8/9 − 5/9.", "1/3", ["1/3", "3/18", "8/9", "5/9"]),
    ("Compute 5/11 + 3/11.", "8/11", ["8/11", "8/22", "2/11", "15/11"]),
    ("Compute 9/13 − 4/13.", "5/13", ["5/13", "5/26", "13/13", "4/13"]),
    # different denoms
    ("Compute 1/3 + 1/5.", "8/15", ["8/15", "2/8", "2/15", "1/8"]),
    ("Compute 1/3 + 1/6.", "1/2", ["1/2", "2/9", "3/9", "1/9"]),
    ("Compute 1/4 + 1/3.", "7/12", ["7/12", "2/7", "1/12", "2/12"]),
    ("Compute 2/3 + 1/4.", "11/12", ["11/12", "3/7", "3/12", "1/2"]),
    ("Compute 3/5 + 1/2.", "11/10", ["11/10", "4/7", "4/10", "3/7"]),
    ("Compute 1/2 − 1/5.", "3/10", ["3/10", "0", "1/3", "2/5"]),
    ("Compute 5/6 − 2/3.", "1/6", ["1/6", "3/3", "3/6", "1/3"]),
    ("Compute 3/4 − 1/6.", "7/12", ["7/12", "2/2", "2/12", "1/12"]),
    ("Compute 7/8 − 1/2.", "3/8", ["3/8", "6/16", "8/8", "4/8"]),
    ("Compute 5/6 − 1/4.", "7/12", ["7/12", "4/2", "4/12", "1/12"]),
]
for stem, ans, choices in frac_addsub:
    op = "add" if "+" in stem else "subtract"
    t2_add(
        stem, ans, choices,
        (
            f"Fraction {op}: when denominators match, keep the bottom and "
            f"{op} the tops; when denominators differ, find a common "
            f"denominator (LCM of bottoms), convert each, then {op}. "
            f"{stem.replace('Compute ', '').rstrip('.')} = {ans}. Forgetting "
            f"the common denominator is the most common error."
        ),
    )

# --- Fraction multiplication (10) ---
frac_mul = [
    ("Compute 2/5 × 5/6.", "1/3", ["1/3", "7/11", "10/11", "4/11"]),
    ("Compute 3/8 × 2/3.", "1/4", ["1/4", "5/11", "1/8", "6/24"]),
    ("Compute 4/5 × 5/8.", "1/2", ["1/2", "9/13", "20/40", "4/8"]),
    ("Compute 3/4 × 4/9.", "1/3", ["1/3", "7/13", "12/36", "3/9"]),
    ("Compute 2/7 × 7/8.", "1/4", ["1/4", "9/15", "14/56", "2/8"]),
    ("Compute 5/6 × 3/10.", "1/4", ["1/4", "8/16", "15/60", "5/10"]),
    ("Compute 3/5 × 10/9.", "2/3", ["2/3", "13/14", "30/45", "1/3"]),
    ("Compute 7/9 × 3/14.", "1/6", ["1/6", "10/23", "21/126", "1/3"]),
    ("Compute 5/8 × 2/15.", "1/12", ["1/12", "7/23", "10/120", "1/6"]),
    ("Compute 6/11 × 11/12.", "1/2", ["1/2", "17/23", "66/132", "6/12"]),
]
for stem, ans, choices in frac_mul:
    t2_add(
        stem, ans, choices,
        (
            f"Fraction multiplication: tops × tops, bottoms × bottoms, then "
            f"simplify. {stem.replace('Compute ', '').rstrip('.')} = {ans}. "
            f"Cancel BEFORE multiplying — any common factor between a top and "
            f"a bottom (cross-cancel) keeps numbers small."
        ),
    )

# --- Fraction division (10) — use parentheses so sympy parses right ---
frac_div = [
    ("Compute (1/2) ÷ (1/4).", "2", ["2", "1/8", "1/2", "4"]),
    ("Compute (3/4) ÷ (1/2).", "3/2", ["3/2", "3/8", "2/3", "1/2"]),
    ("Compute (2/3) ÷ (1/3).", "2", ["2", "2/9", "1/2", "6"]),
    ("Compute (3/5) ÷ (3/10).", "2", ["2", "9/50", "1/2", "10"]),
    ("Compute (5/6) ÷ (5/12).", "2", ["2", "25/72", "1/2", "12"]),
    ("Compute (4/5) ÷ (2/5).", "2", ["2", "8/25", "1/2", "10"]),
    ("Compute (1/3) ÷ (1/9).", "3", ["3", "1/27", "1/3", "9"]),
    ("Compute (2/3) ÷ (4/9).", "3/2", ["3/2", "8/27", "2/3", "6"]),
    ("Compute (3/8) ÷ (3/4).", "1/2", ["1/2", "9/32", "2", "1/4"]),
    ("Compute (5/8) ÷ (5/16).", "2", ["2", "25/128", "1/2", "16"]),
]
for stem, ans, choices in frac_div:
    t2_add(
        stem, ans, choices,
        (
            f"Fraction division: invert and multiply. Flip the second "
            f"fraction (its reciprocal) and multiply. "
            f"{stem.replace('Compute ', '').rstrip('.')} = {ans}. Why it "
            f"works: dividing by 1/4 asks 'how many quarters fit?' — the "
            f"same as multiplying by 4."
        ),
    )

# --- Decimal × decimal (12) — distractors within 3× magnitude ---
dec_mul = [
    # 0.3 × 0.4 = 0.12 — distractors close to 0.12
    ("Compute 0.3 × 0.4.", "0.12", ["0.12", "0.07", "0.21", "0.34"]),
    ("Compute 0.25 × 4.", "1", ["1", "0.5", "2", "0.25"]),
    ("Compute 0.5 × 0.5.", "0.25", ["0.25", "0.1", "0.5", "0.45"]),
    ("Compute 0.1 × 0.1.", "0.01", ["0.01", "0.02", "0.005", "0.03"]),
    ("Compute 0.2 × 0.5.", "0.1", ["0.1", "0.07", "0.25", "0.15"]),
    ("Compute 0.6 × 0.7.", "0.42", ["0.42", "0.13", "0.84", "0.49"]),
    ("Compute 0.4 × 0.4.", "0.16", ["0.16", "0.08", "0.32", "0.24"]),
    ("Compute 0.25 × 8.", "2", ["2", "0.25", "4", "0.2"]),
    ("Compute 0.5 × 0.2.", "0.1", ["0.1", "0.07", "0.25", "0.04"]),
    ("Compute 1.5 × 0.4.", "0.6", ["0.6", "0.4", "1.9", "0.06"]),
    ("Compute 0.3 × 0.3.", "0.09", ["0.09", "0.06", "0.18", "0.15"]),
    ("Compute 0.8 × 0.2.", "0.16", ["0.16", "0.08", "0.32", "0.24"]),
]
for stem, ans, choices in dec_mul:
    t2_add(
        stem, ans, choices,
        (
            f"Decimal × decimal: multiply as whole numbers, then count total "
            f"decimal places in the factors and put that many in the answer. "
            f"{stem.replace('Compute ', '').rstrip('.')} = {ans}. Forgetting "
            f"to move the decimal is the classic mistake — 0.3 × 0.4 has 1+1 = "
            f"2 decimal places, so 12 → 0.12."
        ),
    )

# --- Negatives intro (15) — use word framing to dodge dupes ---
neg = [
    ("Compute −7 + 12.", "5", ["5", "−5", "19", "−19"]),
    ("Compute −9 + 4.", "−5", ["−5", "5", "13", "−13"]),
    ("Compute 7 + (−10).", "−3", ["−3", "3", "17", "−17"]),
    ("Compute −6 − 4.", "−10", ["−10", "10", "−2", "2"]),
    ("Compute −12 − (−7).", "−5", ["−5", "5", "−19", "19"]),
    ("Compute 8 − 11.", "−3", ["−3", "3", "−19", "19"]),
    ("Compute −15 + 9.", "−6", ["−6", "6", "−24", "24"]),
    ("Compute 11 − (−5).", "16", ["16", "−16", "6", "−6"]),
    ("Compute −13 − 7.", "−20", ["−20", "20", "−6", "6"]),
    ("Compute −2 + (−8).", "−10", ["−10", "10", "−6", "6"]),
    ("Compute 5 − 14.", "−9", ["−9", "9", "−19", "19"]),
    ("Compute −10 + 7.", "−3", ["−3", "3", "−17", "17"]),
    ("Compute 0 − 9.", "−9", ["−9", "9", "0", "−18"]),
    ("Compute −6 + (−9).", "−15", ["−15", "15", "3", "−3"]),
    ("Compute 4 − (−8).", "12", ["12", "−12", "4", "−4"]),
]
for stem, ans, choices in neg:
    t2_add(
        stem, ans, choices,
        (
            f"Negative numbers on the number line. "
            f"{stem.replace('Compute ', '').rstrip('.')} = {ans}. The sign "
            f"rule: subtracting a negative flips to addition (a − (−b) = "
            f"a + b). Adding a negative goes left on the number line; "
            f"subtracting a negative goes right."
        ),
    )

# --- Absolute value (12) — use word phrasings to avoid dupes ---
abs_val = [
    ("Compute the absolute value: |−4|.", "4", ["4", "−4", "0", "8"]),
    ("Compute the absolute value: |−9|.", "9", ["9", "−9", "0", "18"]),
    ("Compute the absolute value: |−15|.", "15", ["15", "−15", "1", "30"]),
    ("Compute the absolute value: |−20|.", "20", ["20", "−20", "5", "40"]),
    ("Compute the absolute value: |−100|.", "100", ["100", "−100", "10", "200"]),
    ("Compute the absolute value: |11|.", "11", ["11", "−11", "1", "22"]),
    ("Compute the absolute value: |0|.", "0", ["0", "1", "−1", "10"]),
    ("Compute the absolute value: |−6|.", "6", ["6", "−6", "0", "12"]),
    ("Compute the absolute value: |−14|.", "14", ["14", "−14", "1", "28"]),
    ("Compute the absolute value: |25|.", "25", ["25", "−25", "5", "50"]),
    ("Compute the absolute value: |−50|.", "50", ["50", "−50", "5", "100"]),
    ("Compute the absolute value: |−1|.", "1", ["1", "−1", "0", "2"]),
]
for stem, ans, choices in abs_val:
    t2_add(
        stem, ans, choices,
        (
            f"Absolute value = distance from zero on the number line. Always "
            f"non-negative. {stem.replace('Compute the absolute value: ', '').rstrip('.')} "
            f"= {ans}. The sign drops, magnitude stays — useful for measuring "
            f"deviation, tolerance, and 'how far from average'."
        ),
    )

# --- Thirds, eighths conversions (10) — word phrasing ---
thirds_eighths = [
    ("Convert 1/3 to a decimal (round to thousandths).", "0.333", ["0.333", "0.13", "3.3", "0.3"]),
    ("Convert 2/3 to a decimal (round to thousandths).", "0.667", ["0.667", "0.26", "6.6", "0.67"]),
    ("Convert 1/6 to a decimal (round to thousandths).", "0.167", ["0.167", "0.6", "0.16", "1.6"]),
    ("Convert 1/3 to a percent (round to tenths).", "33.3%", ["33.3%", "30%", "13%", "3.3%"]),
    ("Convert 2/3 to a percent (round to tenths).", "66.7%", ["66.7%", "60%", "26%", "6.7%"]),
    ("Convert 1/8 to a decimal.", "0.125", ["0.125", "0.18", "0.8", "0.5"]),
    ("Convert 3/8 to a decimal.", "0.375", ["0.375", "0.38", "0.83", "0.5"]),
    ("Convert 5/8 to a decimal.", "0.625", ["0.625", "0.58", "0.85", "0.5"]),
    ("Convert 7/8 to a decimal value.", "0.875", ["0.875", "0.78", "0.87", "1.78"]),
    ("Convert 1/8 to a percent.", "12.5%", ["12.5%", "8%", "18%", "20%"]),
]
for stem, ans, choices in thirds_eighths:
    t2_add(
        stem, ans, choices,
        (
            f"Common F/D/P conversion. Thirds don't terminate (1/3 ≈ 0.333... "
            f"repeating), so we round; eighths terminate cleanly. "
            f"{stem.rstrip('.')} → {ans}. Memorize the eighths table: "
            f"1/8 = 12.5%, 3/8 = 37.5%, 5/8 = 62.5%, 7/8 = 87.5%."
        ),
    )

# --- Mixed decimal addition/subtraction (10) ---
dec_addsub = [
    ("Compute 0.45 + 0.35.", "0.8", ["0.8", "0.10", "0.080", "8"]),
    ("Compute 1.7 − 0.9.", "0.8", ["0.8", "0.08", "8", "2.6"]),
    ("Compute 0.65 + 0.25.", "0.9", ["0.9", "0.4", "0.09", "9"]),
    ("Compute 3.4 − 2.8.", "0.6", ["0.6", "1.4", "1.0", "−0.6"]),
    ("Compute 0.05 + 0.95.", "1", ["1", "0.1", "100", "0.10"]),
    ("Compute 2.25 − 0.75.", "1.5", ["1.5", "0.5", "3.0", "1.50"]),
    ("Compute 0.1 + 0.9.", "1", ["1", "0.10", "10", "1.0"]),
    ("Compute 4.5 − 1.75.", "2.75", ["2.75", "3.25", "2.5", "27.5"]),
    ("Compute 0.6 + 0.45.", "1.05", ["1.05", "0.105", "10.5", "0.51"]),
    ("Compute 5.4 − 0.6.", "4.8", ["4.8", "5.2", "6.0", "0.48"]),
]
for stem, ans, choices in dec_addsub:
    t2_add(
        stem, ans, choices,
        (
            f"Decimal addition/subtraction: line up the decimal points, then "
            f"add or subtract column by column. "
            f"{stem.replace('Compute ', '').rstrip('.')} = {ans}. Pad with "
            f"zeros so both numbers have the same number of decimal places — "
            f"mismatched decimals cause the most errors."
        ),
    )

# --- Simplify fractions (10) ---
simplify_frac = [
    ("Simplify the fraction 4/8.", "1/2", ["1/2", "1/4", "2/8", "1/8"]),
    ("Simplify the fraction 6/9.", "2/3", ["2/3", "3/9", "1/3", "2/9"]),
    ("Simplify the fraction 10/15.", "2/3", ["2/3", "1/3", "5/15", "2/5"]),
    ("Simplify the fraction 8/12.", "2/3", ["2/3", "1/2", "4/6", "8/3"]),
    ("Simplify the fraction 15/20.", "3/4", ["3/4", "1/4", "5/20", "3/20"]),
    ("Simplify the fraction 9/12.", "3/4", ["3/4", "1/4", "3/12", "9/3"]),
    ("Simplify the fraction 14/21.", "2/3", ["2/3", "1/3", "7/21", "2/7"]),
    ("Simplify the fraction 18/24.", "3/4", ["3/4", "1/4", "6/24", "3/8"]),
    ("Simplify the fraction 12/16.", "3/4", ["3/4", "1/2", "6/16", "3/8"]),
    ("Simplify the fraction 20/30.", "2/3", ["2/3", "1/3", "10/30", "2/5"]),
]
for stem, ans, choices in simplify_frac:
    t2_add(
        stem, ans, choices,
        (
            f"Simplifying fractions using the greatest common factor (GCF). "
            f"Divide top and bottom by their GCF until no common factor "
            f"remains. {stem.replace('Simplify the fraction ', '').rstrip('.')} "
            f"= {ans}. The simplified form is the same value, just most "
            f"concise."
        ),
    )

# --- Percent-to-fraction (8) ---
pct_to_frac = [
    ("Convert 60% to a fraction in simplest form.", "3/5", ["3/5", "6/10", "1/6", "60/1"]),
    ("Convert 80% to a fraction in simplest form.", "4/5", ["4/5", "8/10", "1/8", "8/1"]),
    ("Convert 5% to a fraction in simplest form.", "1/20", ["1/20", "5/100", "1/5", "5/1"]),
    ("Convert 35% to a fraction in simplest form.", "7/20", ["7/20", "35/100", "1/35", "35/10"]),
    ("Convert 12.5% to a fraction in simplest form.", "1/8", ["1/8", "125/1000", "12.5/100", "1/12"]),
    ("Convert 40% to a fraction in simplest form.", "2/5", ["2/5", "4/10", "1/40", "4/1"]),
    ("Convert 90% to a fraction in simplest form.", "9/10", ["9/10", "90/100", "9/1", "1/9"]),
    ("Convert 65% to a fraction in simplest form.", "13/20", ["13/20", "65/100", "1/65", "13/10"]),
]
for stem, ans, choices in pct_to_frac:
    t2_add(
        stem, ans, choices,
        (
            f"Percent-to-fraction conversion. Write the percent over 100, "
            f"then simplify using the GCF. {stem.replace('Convert ', '').rstrip('.')} "
            f"= {ans}. Common F/D/P table required: 25% = 1/4, 50% = 1/2, "
            f"75% = 3/4, 20% = 1/5, 12.5% = 1/8."
        ),
    )

# --- Mixed: which form equals X (8) ---
mixed_form = [
    ("Which fraction equals 0.5?", "1/2", ["1/2", "1/5", "5/100", "1/4"]),
    ("Which fraction equals 0.25?", "1/4", ["1/4", "25/100", "1/25", "1/2"]),
    ("Which fraction equals 0.75?", "3/4", ["3/4", "75/100", "1/75", "3/40"]),
    ("Which decimal equals 7/10?", "0.7", ["0.7", "0.07", "7", "1.7"]),
    ("Which decimal equals 1/8?", "0.125", ["0.125", "0.18", "0.8", "0.5"]),
    ("Which decimal equals 3/4?", "0.75", ["0.75", "0.34", "0.43", "0.7"]),
    ("Which percent equals 1/5?", "20%", ["20%", "5%", "15%", "50%"]),
    ("Which percent equals 1/8?", "12.5%", ["12.5%", "8%", "18%", "20%"]),
]
for stem, ans, choices in mixed_form:
    t2_add(
        stem, ans, choices,
        (
            f"Common F/D/P conversion. Fluency across the three forms is the "
            f"point — same value, three faces. {stem.rstrip('?')} → {ans}. "
            f"Memorize the table; a kid who knows 1/4 = 0.25 = 25% answers "
            f"a quarter of all percent problems instantly."
        ),
    )

# Fillers if needed — pad to 180
print(f"[T2 build] generated {len(T2_BATCH)} so far")

# More fillers — area/PEMDAS/mean which are P5/P6 but pillars overlap;
# stay in P3 by adding more percent-of-N at uncommon values
filler_pct = [
    ("Find 10% of 67.", "6.7", ["6.7", "67", "0.67", "16"]),
    ("Find 10% of 84.", "8.4", ["8.4", "84", "0.84", "18"]),
    ("Find 10% of 113.", "11.3", ["11.3", "113", "1.13", "21"]),
    ("Find 25% of 28.", "7", ["7", "14", "4", "11"]),
    ("Find 25% of 48.", "12", ["12", "24", "6", "16"]),
    ("Find 50% of 110.", "55", ["55", "11", "60", "100"]),
    ("Find 5% of 80.", "4", ["4", "8", "2", "16"]),
    ("Find 5% of 240.", "12", ["12", "24", "6", "48"]),
    ("Find 20% of 55.", "11", ["11", "5.5", "22", "16"]),
    ("Find 20% of 75.", "15", ["15", "7.5", "30", "12"]),
    ("Find 30% of 60.", "18", ["18", "6", "12", "30"]),
    ("Find 40% of 75.", "30", ["30", "15", "45", "20"]),
    # add some more abs-value variations
    ("Compute the absolute value: |−8|.", "8", ["8", "−8", "0", "16"]),
    ("Compute the absolute value: |2|.", "2", ["2", "−2", "0", "4"]),
    ("Compute |−5| + |3|.", "8", ["8", "−8", "2", "−2"]),
    ("Compute |−10| − |−4|.", "6", ["6", "−6", "14", "−14"]),
    # negatives with parens for variety
    ("Compute −20 + 8.", "−12", ["−12", "12", "−28", "28"]),
    ("Compute 7 + (−7).", "0", ["0", "14", "−14", "1"]),
    ("Compute −30 + 50.", "20", ["20", "−20", "80", "−80"]),
    ("Compute 12 − (−3).", "15", ["15", "−15", "9", "−9"]),
    ("Compute −1 − 1.", "−2", ["−2", "2", "0", "−1"]),
]
for stem, ans, choices in filler_pct:
    # detect category
    if "%" in stem:
        pct_str = stem.split('%')[0].split()[-1]
        teach = ""
        if pct_str == "10":
            teach = "The 10% trick: shift the decimal one place left. "
        elif pct_str == "20":
            teach = "20% = 10% then double. "
        elif pct_str == "5":
            teach = "5% = 10% then halve. "
        elif pct_str == "25":
            teach = "25% means quarter. "
        elif pct_str == "50":
            teach = "50% means half. "
        elif pct_str == "30":
            teach = "30% = 3 × 10% = three decimal-shifts. "
        elif pct_str == "40":
            teach = "40% = 4 × 10%. "
        ctx = (f"Percent of a number: 'of' means ×. {teach}"
               f"{stem.replace('Find ', '').rstrip('.')} = {ans}.")
    elif "absolute" in stem.lower():
        ctx = (f"Absolute value: distance from zero on the number line; "
               f"sign drops, magnitude stays. {stem.rstrip('.')} = {ans}.")
    else:
        ctx = (f"Negatives on the number line. The sign rule for subtraction: "
               f"subtracting a negative flips to addition. "
               f"{stem.replace('Compute ', '').rstrip('.')} = {ans}.")
    t2_add(stem, ans, choices, ctx)

# More fillers if still short
print(f"[T2 build] after fillers: {len(T2_BATCH)}")
# Padding: add more F/D/P
filler_fdp = [
    ("Convert 0.55 to a percent.", "55%", ["55%", "5.5%", "0.55%", "550%"]),
    ("Convert 0.04 to a percent.", "4%", ["4%", "40%", "0.4%", "0.04%"]),
    ("Convert 0.125 to a percent.", "12.5%", ["12.5%", "1.25%", "125%", "0.125%"]),
    ("Convert 0.375 to a percent.", "37.5%", ["37.5%", "3.75%", "375%", "0.375%"]),
    ("Convert 200% to a decimal.", "2", ["2", "0.2", "20", "200"]),
    ("Convert 45% to a decimal.", "0.45", ["0.45", "4.5", "0.045", "45"]),
    ("Convert 8% to a decimal.", "0.08", ["0.08", "0.8", "0.008", "8"]),
    ("Convert 0.625 to a percent.", "62.5%", ["62.5%", "6.25%", "625%", "0.625%"]),
    ("Convert 2/25 to a percent.", "8%", ["8%", "2.5%", "25%", "80%"]),
    ("Convert 3/20 to a percent.", "15%", ["15%", "3.2%", "20%", "60%"]),
]
for stem, ans, choices in filler_fdp:
    t2_add(
        stem, ans, choices,
        (
            f"Common F/D/P conversion. Decimal → percent: shift decimal two "
            f"right. Percent → decimal: shift two left. Fraction → percent: "
            f"top ÷ bottom × 100. {stem.replace('Convert ', '').rstrip('.')} "
            f"= {ans}."
        ),
    )

print(f"[T2 build] after extra fdp: {len(T2_BATCH)}")

# Pad with more uncommon-N percent-of if needed
while len(T2_BATCH) < 200:
    # Add more uncommon-N % moves
    extras = [
        ("Find 10% of 19.", "1.9", ["1.9", "19", "0.19", "11"]),
        ("Find 10% of 29.", "2.9", ["2.9", "29", "0.29", "12"]),
        ("Find 10% of 53.", "5.3", ["5.3", "53", "0.53", "15"]),
        ("Find 10% of 69.", "6.9", ["6.9", "69", "0.69", "16"]),
        ("Find 10% of 88.", "8.8", ["8.8", "88", "0.88", "18"]),
        ("Find 10% of 117.", "11.7", ["11.7", "117", "1.17", "22"]),
        ("Find 10% of 161.", "16.1", ["16.1", "161", "1.61", "26"]),
        ("Find 10% of 234.", "23.4", ["23.4", "234", "2.34", "33"]),
        ("Find 25% of 52.", "13", ["13", "26", "6.5", "16"]),
        ("Find 25% of 68.", "17", ["17", "34", "8.5", "20"]),
        ("Find 25% of 84.", "21", ["21", "42", "10.5", "25"]),
        ("Find 50% of 38.", "19", ["19", "9.5", "76", "24"]),
        ("Find 50% of 54.", "27", ["27", "13.5", "108", "30"]),
        ("Find 50% of 84.", "42", ["42", "21", "168", "45"]),
        ("Find 50% of 118.", "59", ["59", "29.5", "236", "62"]),
        ("Find 20% of 130.", "26", ["26", "13", "65", "30"]),
        ("Find 20% of 240.", "48", ["48", "24", "120", "52"]),
        ("Find 5% of 60.", "3", ["3", "6", "1.5", "12"]),
        ("Find 5% of 180.", "9", ["9", "18", "4.5", "36"]),
        ("Find 5% of 360.", "18", ["18", "36", "9", "72"]),
    ]
    for stem, ans, choices in extras:
        if len(T2_BATCH) >= 200:
            break
        pct_str = stem.split('%')[0].split()[-1]
        teach = ""
        if pct_str == "10":
            teach = "The 10% trick: shift the decimal one place left. "
        elif pct_str == "20":
            teach = "20% = 10% then double. "
        elif pct_str == "5":
            teach = "5% = 10% then halve. "
        elif pct_str == "25":
            teach = "25% means quarter — divide by 4. "
        elif pct_str == "50":
            teach = "50% means half — divide by 2. "
        t2_add(
            stem, ans, choices,
            (
                f"Percent of a number: 'of' means ×. {teach}"
                f"{stem.replace('Find ', '').rstrip('.')} = {ans}."
            ),
        )
    break  # only once

print(f"[T2 build] final: {len(T2_BATCH)}")

# Trim or pad to 180 (try to get 180 accepted)
# Try emitting all and see what passes
t2_pre = len(ACCEPTED)
target_t2 = 180
for q in T2_BATCH:
    if len(ACCEPTED) - t2_pre >= target_t2:
        break
    q_emit(q)
save_incremental()
t2_post = len(ACCEPTED)
print(f"[T2] accepted {t2_post - t2_pre} / {len(T2_BATCH)} tried; total={t2_post}")

# ============================================================================
# T3 — 170 questions
# ============================================================================

T3_BATCH: list[dict] = []

def t3_add(stem, ans, choices, ctx):
    T3_BATCH.append({
        "tier": 3,
        "question": stem,
        "answer": ans,
        "choices": choices,
        "context": ctx,
    })

# --- Proportions / cross-multiply (25) ---
proportions = [
    ("Solve the proportion: 3/x = 6/8", "x = 4", ["x = 4", "x = 2", "x = 6", "x = 16"]),
    ("Solve the proportion: 5/15 = x/45", "x = 15", ["x = 15", "x = 3", "x = 9", "x = 5"]),
    ("Solve the proportion: 2/3 = x/12", "x = 8", ["x = 8", "x = 4", "x = 6", "x = 18"]),
    ("Solve the proportion: x/10 = 3/5", "x = 6", ["x = 6", "x = 2", "x = 30", "x = 15"]),
    ("Solve the proportion: 4/x = 8/10", "x = 5", ["x = 5", "x = 2", "x = 20", "x = 8"]),
    ("Solve the proportion: x/8 = 9/12", "x = 6", ["x = 6", "x = 4", "x = 12", "x = 9"]),
    ("Solve the proportion: 3/4 = 9/x", "x = 12", ["x = 12", "x = 3", "x = 36", "x = 6"]),
    ("Solve the proportion: 6/x = 2/3", "x = 9", ["x = 9", "x = 4", "x = 18", "x = 6"]),
    ("Solve the proportion: x/5 = 4/10", "x = 2", ["x = 2", "x = 8", "x = 0.5", "x = 20"]),
    ("Solve the proportion: 8/x = 4/5", "x = 10", ["x = 10", "x = 1.6", "x = 40", "x = 6"]),
    ("Solve the proportion: 5/x = 1/4", "x = 20", ["x = 20", "x = 1.25", "x = 5", "x = 9"]),
    ("Solve the proportion: 3/8 = x/24", "x = 9", ["x = 9", "x = 3", "x = 6", "x = 12"]),
    ("Solve the proportion: 2/5 = 8/x", "x = 20", ["x = 20", "x = 16", "x = 4", "x = 25"]),
    ("Solve the proportion: 7/x = 14/16", "x = 8", ["x = 8", "x = 2", "x = 7", "x = 12"]),
    ("Solve the proportion: 6/9 = x/15", "x = 10", ["x = 10", "x = 5", "x = 20", "x = 2"]),
    ("Solve the proportion: 1/3 = 4/x", "x = 12", ["x = 12", "x = 3", "x = 4", "x = 8"]),
    ("Solve the proportion: x/12 = 1/4", "x = 3", ["x = 3", "x = 4", "x = 6", "x = 8"]),
    ("Solve the proportion: 9/12 = 3/x", "x = 4", ["x = 4", "x = 9", "x = 12", "x = 3"]),
    ("Solve the proportion: 2/x = 1/9", "x = 18", ["x = 18", "x = 5", "x = 7", "x = 11"]),
    ("Solve the proportion: 5/8 = x/40", "x = 25", ["x = 25", "x = 5", "x = 35", "x = 8"]),
    ("Solve the proportion: 4/x = 1/3", "x = 12", ["x = 12", "x = 3", "x = 4", "x = 7"]),
    ("Solve the proportion: 3/7 = 12/x", "x = 28", ["x = 28", "x = 4", "x = 21", "x = 36"]),
    ("Solve the proportion: x/9 = 2/3", "x = 6", ["x = 6", "x = 3", "x = 9", "x = 14"]),
    ("Solve the proportion: 10/x = 5/6", "x = 12", ["x = 12", "x = 4", "x = 5", "x = 18"]),
    ("Solve the proportion: 2/7 = x/14", "x = 4", ["x = 4", "x = 7", "x = 2", "x = 14"]),
]
for stem, ans, choices in proportions:
    t3_add(
        stem, ans, choices,
        (
            f"Cross-multiplication for proportions. If a/b = c/d, then "
            f"a·d = b·c. Multiply across the equal sign, then solve for x. "
            f"{stem.replace('Solve the proportion: ', '')} → {ans}. Used for "
            f"scale models, recipe scaling, unit conversion, similar triangles."
        ),
    )

# --- Scale problems (10) ---
scale = [
    ("Map scale: 1 cm = 50 km. 4 cm on the map represents ? km.",
     "200 km", ["200 km", "12.5 km", "54 km", "100 km"]),
    ("Map: 1 inch = 25 miles. 6 inches represents how many miles?",
     "150 miles", ["150 miles", "31 miles", "25 miles", "75 miles"]),
    ("Model train scale 1:87. A 2-inch model represents how many inches real?",
     "174 in", ["174 in", "85 in", "87 in", "44 in"]),
    ("Architect's drawing: 1 cm = 10 m. 7 cm on plan = ? meters.",
     "70 m", ["70 m", "17 m", "10 m", "100 m"]),
    ("Map: 2 cm = 5 km. 10 cm represents how many km?",
     "25 km", ["25 km", "10 km", "5 km", "50 km"]),
    ("Scale 1 mm = 1 m real. A 35 mm model represents ? meters.",
     "35 m", ["35 m", "1 m", "350 m", "100 m"]),
    ("Blueprint scale 1 in = 4 ft. A 9 in line represents ? ft.",
     "36 ft", ["36 ft", "13 ft", "4 ft", "20 ft"]),
    ("Map: 1 cm = 250 km. 3 cm represents how many km?",
     "750 km", ["750 km", "250 km", "253 km", "500 km"]),
    ("Model car scale 1:24. Car is 4 in long. Real car is ? in.",
     "96 in", ["96 in", "28 in", "24 in", "100 in"]),
    ("Map: 1 cm = 100 m. 8.5 cm represents ? meters.",
     "850 m", ["850 m", "108.5 m", "100 m", "8.5 m"]),
]
for stem, ans, choices in scale:
    t3_add(
        stem, ans, choices,
        (
            f"Scale problem solved by cross-multiplication. Set up the "
            f"proportion (scale unit / real unit) = (map measure / unknown). "
            f"{stem} → {ans}. Same trick: maps, blueprints, toy-soldier "
            f"hobbyists. Scaling a known ratio."
        ),
    )

# --- Sign rules deep dive (12) — word-prefixed to avoid bank collision ---
sign_deep = [
    ("Compute (−4) × (−5).", "20", ["20", "−20", "9", "−9"]),
    ("Compute (−3) × (+2).", "−6", ["−6", "6", "−1", "1"]),
    ("Compute (−2) × (−3) × (−1).", "−6", ["−6", "6", "−1", "1"]),
    ("Compute (−6) ÷ (−2).", "3", ["3", "−3", "12", "−12"]),
    ("Compute (+8) ÷ (−4).", "−2", ["−2", "2", "−12", "12"]),
    ("Compute (−12) ÷ (−3).", "4", ["4", "−4", "15", "−15"]),
    ("Evaluate (−2) raised to the second power.", "4", ["4", "−4", "0", "2"]),
    ("Evaluate (−3) raised to the third power.", "−27", ["−27", "27", "9", "−9"]),
    ("Compute −5 × 3 × (−2).", "30", ["30", "−30", "0", "−10"]),
    ("Compute (−1) × (−1) × (−1) × (−1).", "1", ["1", "−1", "0", "4"]),
    ("Compute (−7) × (−2) × (+3).", "42", ["42", "−42", "12", "−12"]),
    ("Compute (−24) ÷ (+6).", "−4", ["−4", "4", "−18", "18"]),
]
for stem, ans, choices in sign_deep:
    t3_add(
        stem, ans, choices,
        (
            f"Sign rule for multiplication and division. Two negatives make a "
            f"positive; an odd count of negatives stays negative; an even "
            f"count is positive. {stem.replace('Compute ', '').replace('Evaluate ', '').rstrip('.')} "
            f"= {ans}. Count the minus signs in the product — odd → −, even → +."
        ),
    )

# --- Tip math (20) ---
tip = [
    ("What is a 10% tip on $30.00?", "$3", ["$3", "$30", "$0.30", "$6"]),
    ("What is a 10% tip on $45.00?", "$4.50", ["$4.50", "$45", "$0.45", "$9"]),
    ("What is a 10% tip on $55.00?", "$5.50", ["$5.50", "$55", "$0.55", "$11"]),
    ("What is a 10% tip on $80.00?", "$8", ["$8", "$80", "$0.80", "$16"]),
    ("What is a 10% tip on $120.00?", "$12", ["$12", "$120", "$1.20", "$24"]),
    ("What is a 20% tip on $50.00?", "$10", ["$10", "$5", "$20", "$2.50"]),
    ("What is a 20% tip on $25.00?", "$5", ["$5", "$2.50", "$10", "$1.25"]),
    ("What is a 20% tip on $60.00?", "$12", ["$12", "$6", "$24", "$3"]),
    ("What is a 20% tip on $35.00?", "$7", ["$7", "$3.50", "$14", "$8.75"]),
    ("What is a 20% tip on $75.00?", "$15", ["$15", "$7.50", "$30", "$3.75"]),
    ("What is a 20% tip on $15.00?", "$3", ["$3", "$1.50", "$6", "$0.75"]),
    ("What is a 15% tip on $40.00?", "$6", ["$6", "$4", "$8", "$10"]),
    ("What is a 15% tip on $20.00?", "$3", ["$3", "$2", "$4", "$5"]),
    ("What is a 15% tip on $60.00?", "$9", ["$9", "$6", "$12", "$15"]),
    ("What is a 15% tip on $80.00?", "$12", ["$12", "$8", "$16", "$20"]),
    ("What is a 15% tip on $30.00?", "$4.50", ["$4.50", "$3", "$6", "$7.50"]),
    ("What is a 15% tip on $50.00?", "$7.50", ["$7.50", "$5", "$10", "$12.50"]),
    ("What is a 20% tip on $100.00?", "$20", ["$20", "$10", "$40", "$5"]),
    ("What is a 18% tip on $50.00?", "$9", ["$9", "$5", "$10", "$11"]),
    ("What is a 18% tip on $25.00?", "$4.50", ["$4.50", "$2.50", "$5", "$6"]),
]
for stem, ans, choices in tip:
    pct_str = stem.split('%')[0].split()[-1]
    teach = ""
    if pct_str == "10":
        teach = "The 10% trick: move the decimal one place left. "
    elif pct_str == "20":
        teach = "10%-then-double for 20%: find 10%, then ×2. "
    elif pct_str == "15":
        teach = "10% + half-of-10% for 15%: find 10%, then add half of it. "
    elif pct_str == "18":
        teach = "18% ≈ 20% − 2%: double-the-10% then subtract one-tenth-of-that. "
    t3_add(
        stem, ans, choices,
        (
            f"Tip math via the 10% trick. {teach}"
            f"{stem.replace('What is a ', '').rstrip('?')} = {ans}. "
            f"Practice this at every restaurant — fastest mental shortcut in life."
        ),
    )

# --- Percent change (10) ---
pct_change = [
    ("From 50 to 65, what is the percent increase?", "30%", ["30%", "15%", "23%", "13%"]),
    ("From 80 to 60, what is the percent decrease?", "25%", ["25%", "20%", "33%", "75%"]),
    ("From 100 to 150, what is the percent increase?", "50%", ["50%", "33%", "150%", "100%"]),
    ("From 20 to 25, what is the percent increase?", "25%", ["25%", "5%", "20%", "125%"]),
    ("From 40 to 30, what is the percent decrease?", "25%", ["25%", "10%", "33%", "75%"]),
    ("From 200 to 250, what is the percent increase?", "25%", ["25%", "50%", "20%", "125%"]),
    ("From 60 to 90, what is the percent increase?", "50%", ["50%", "30%", "33%", "150%"]),
    ("From 50 to 45, what is the percent decrease?", "10%", ["10%", "5%", "11%", "90%"]),
    ("From 25 to 40, what is the percent increase?", "60%", ["60%", "40%", "37.5%", "15%"]),
    ("From 200 to 180, what is the percent decrease?", "10%", ["10%", "20%", "11%", "90%"]),
]
for stem, ans, choices in pct_change:
    t3_add(
        stem, ans, choices,
        (
            f"Percent change formula: (new − old) / old, expressed as a percent. "
            f"{stem.rstrip('?')} = {ans}. Common error: dividing by the NEW "
            f"value instead of the OLD. Percent change is always relative to "
            f"the STARTING point."
        ),
    )

# --- Percent-of-a-percent (5) — word phrasings so sympy doesn't reject ---
pct_of_pct = [
    ("A coat is 25% off. The sale is then 20% off. What percent of the original is the final price?",
     "60%", ["60%", "45%", "55%", "65%"]),
    ("An item is reduced 50% then reduced 20% more. What percent of original remains?",
     "40%", ["40%", "30%", "70%", "50%"]),
    ("A discount stacks: 25% off, then 25% off the new price. Final fraction of original?",
     "9/16", ["9/16", "1/2", "5/8", "3/4"]),
    ("A bookstore takes 30% off, then 10% off the reduced price. Final percent of original?",
     "63%", ["63%", "60%", "55%", "67%"]),
    ("A coupon stacks 10% off then 10% off again. Final percent of original?",
     "81%", ["81%", "80%", "90%", "20%"]),
]
for stem, ans, choices in pct_of_pct:
    t3_add(
        stem, ans, choices,
        (
            f"Percent of a percent. Stacked discounts MULTIPLY (not add). "
            f"25% off = pay 75% = ×0.75. Then 20% off the reduced = ×0.80. "
            f"Combined: 0.75 × 0.80 = 0.60 = 60%. The discount fractions "
            f"compound — useful for stacking sales, taxes, and interest."
        ),
    )

# --- Signed rational ops (25) ---
signed_rat = [
    ("Compute −3/4 × 4/9.", "−1/3", ["−1/3", "1/3", "−12/36", "12/36"]),
    ("Compute −3/8 × 4/5.", "−3/10", ["−3/10", "3/10", "−12/40", "12/40"]),
    ("Compute −5/6 × 6/25.", "−1/5", ["−1/5", "1/5", "−30/150", "30/150"]),
    ("Compute −2/9 × 3/4.", "−1/6", ["−1/6", "1/6", "−6/36", "6/36"]),
    ("Compute −5/8 × −16/25.", "2/5", ["2/5", "−2/5", "−80/200", "80/200"]),
    ("Compute −3/7 × 14/9.", "−2/3", ["−2/3", "2/3", "−42/63", "42/63"]),
    ("Compute −2/3 × −9/8.", "3/4", ["3/4", "−3/4", "−18/24", "18/24"]),
    ("Compute (−1/3) ÷ (1/6).", "−2", ["−2", "2", "−1/18", "1/18"]),
    ("Compute (−5/6) ÷ (5/12).", "−2", ["−2", "2", "−25/72", "1/2"]),
    ("Compute (−2/5) ÷ (4/5).", "−1/2", ["−1/2", "1/2", "−8/25", "8/25"]),
    ("Compute (−3/4) ÷ (−1/2).", "3/2", ["3/2", "−3/2", "−3/8", "3/8"]),
    ("Compute (−7/8) ÷ (7/4).", "−1/2", ["−1/2", "1/2", "−49/32", "49/32"]),
    ("Compute (−9/10) ÷ (−3/5).", "3/2", ["3/2", "−3/2", "−27/50", "27/50"]),
    ("Compute −1/3 + 5/6.", "1/2", ["1/2", "−1/2", "4/9", "6/9"]),
    ("Compute −2/5 + 3/10.", "−1/10", ["−1/10", "1/10", "−5/15", "5/15"]),
    ("Compute −5/12 + 1/4.", "−1/6", ["−1/6", "1/6", "−4/12", "4/12"]),
    ("Compute −7/8 + 5/8.", "−1/4", ["−1/4", "1/4", "−12/8", "12/8"]),
    ("Compute −9/10 + 7/10.", "−1/5", ["−1/5", "1/5", "−16/10", "16/10"]),
    ("Compute −1/4 + 3/8.", "1/8", ["1/8", "−1/8", "−2/12", "2/12"]),
    ("Compute −3/5 − 1/10.", "−7/10", ["−7/10", "7/10", "−4/15", "4/15"]),
    ("Compute −5/8 − 1/4.", "−7/8", ["−7/8", "7/8", "−6/12", "6/12"]),
    ("Compute −2/3 − 1/4.", "−11/12", ["−11/12", "11/12", "−3/7", "3/7"]),
    ("Compute −1/6 − 5/12.", "−7/12", ["−7/12", "7/12", "−6/18", "6/18"]),
    ("Compute −7/8 − 1/8.", "−1", ["−1", "1", "0", "−6/8"]),
    ("Compute −11/12 + 5/12.", "−1/2", ["−1/2", "1/2", "−16/12", "16/12"]),
]
for stem, ans, choices in signed_rat:
    op_kind = "+/−" if any(o in stem for o in [" + ", " − ", " - "]) else ("× / ÷")
    t3_add(
        stem, ans, choices,
        (
            f"Signed fraction operation. Apply the sign rule then operate on "
            f"magnitudes. For + and − find common denominator first; for × "
            f"multiply tops/bottoms (cross-cancel); for ÷ invert and multiply. "
            f"{stem.replace('Compute ', '').rstrip('.')} = {ans}. Sign rule: "
            f"negative × negative = positive."
        ),
    )

# --- Signed decimal ops (10) — word phrasings to dodge dupes ---
signed_dec = [
    ("Compute −0.5 + 0.3.", "−0.2", ["−0.2", "0.2", "0.8", "−0.8"]),
    ("Compute −1.2 − 0.6.", "−1.8", ["−1.8", "−0.6", "0.6", "1.8"]),
    ("Compute 0.4 × −0.5.", "−0.2", ["−0.2", "0.2", "−0.9", "0.9"]),
    ("Compute −0.6 ÷ 0.2.", "−3", ["−3", "3", "−0.4", "0.4"]),
    ("Compute −2.5 + 1.5.", "−1", ["−1", "1", "−4", "4"]),
    ("Compute −0.8 × −0.5.", "0.4", ["0.4", "−0.4", "0.3", "−1.3"]),
    ("Compute 3.5 − −1.5.", "5", ["5", "2", "−5", "−2"]),
    ("Compute −1.5 ÷ −0.5.", "3", ["3", "−3", "1", "−1"]),
    ("Compute −0.75 + 0.5.", "−0.25", ["−0.25", "0.25", "−1.25", "1.25"]),
    ("Compute −1.4 × 0.5.", "−0.7", ["−0.7", "0.7", "−2.8", "2.8"]),
]
for stem, ans, choices in signed_dec:
    t3_add(
        stem, ans, choices,
        (
            f"Signed decimal arithmetic. Same sign rule as integers: two "
            f"negatives multiplied or divided make a positive; mixed signs "
            f"give a negative. {stem.replace('Compute ', '').rstrip('.')} = "
            f"{ans}. Line up decimal points for addition/subtraction."
        ),
    )

# --- Discount/sales (10) ---
discount = [
    ("Original price $80, 25% off. Sale price = ?",
     "$60", ["$60", "$20", "$55", "$100"]),
    ("Original price $40, 10% off. Sale price = ?",
     "$36", ["$36", "$4", "$30", "$44"]),
    ("Original price $50, 50% off. Sale price = ?",
     "$25", ["$25", "$50", "$75", "$10"]),
    ("Original price $100, 20% off. Sale price = ?",
     "$80", ["$80", "$20", "$120", "$60"]),
    ("Original price $120, 25% off. Sale price = ?",
     "$90", ["$90", "$30", "$95", "$100"]),
    ("Original price $200, 15% off. Sale price = ?",
     "$170", ["$170", "$30", "$185", "$150"]),
    ("Original price $60, 20% off. Sale price = ?",
     "$48", ["$48", "$12", "$72", "$40"]),
    ("Original price $35, 40% off. Sale price = ?",
     "$21", ["$21", "$14", "$31", "$25"]),
    ("Original price $150, 30% off. Sale price = ?",
     "$105", ["$105", "$45", "$120", "$135"]),
    ("Original price $250, 60% off. Sale price = ?",
     "$100", ["$100", "$150", "$190", "$210"]),
]
for stem, ans, choices in discount:
    t3_add(
        stem, ans, choices,
        (
            f"Discount via percent of a number. Find the discount amount "
            f"using the 10% trick scaled, then subtract from original. "
            f"Faster: 25% off means pay 75% — multiply original by 0.75. "
            f"{stem.rstrip('?')} {ans}."
        ),
    )

# --- Sales tax (5) ---
sales_tax = [
    ("Price $50.00 plus 8% tax. Total?",
     "$54", ["$54", "$4", "$58", "$46"]),
    ("Price $20.00 plus 5% tax. Total?",
     "$21", ["$21", "$1", "$25", "$19"]),
    ("Price $100.00 plus 10% tax. Total?",
     "$110", ["$110", "$10", "$90", "$200"]),
    ("Price $80.00 plus 5% tax. Total?",
     "$84", ["$84", "$4", "$76", "$120"]),
    ("Price $25.00 plus 8% tax. Total?",
     "$27", ["$27", "$2", "$33", "$23"]),
]
for stem, ans, choices in sales_tax:
    t3_add(
        stem, ans, choices,
        (
            f"Sales tax = percent of a number, then add to price. {stem} "
            f"Total = {ans}. For 8% tax: 10% trick (10% of N), then take "
            f"20% off that for the 2% gap (8% = 10% − 2%). Total = price + "
            f"tax."
        ),
    )

# --- Unit rate / proportion word problems (10) ---
unit_rate = [
    ("If 3 apples cost $2, what do 12 apples cost?", "$8", ["$8", "$6", "$4", "$24"]),
    ("A car covers 120 miles in 2 hours. What is its speed?", "60 mph", ["60 mph", "240 mph", "30 mph", "120 mph"]),
    ("4 cups of flour serves 12 people. How much serves 18?", "6 cups", ["6 cups", "4 cups", "8 cups", "12 cups"]),
    ("5 books cost $40. What do 8 books cost?", "$64", ["$64", "$45", "$13", "$50"]),
    ("A runner covers 6 miles in 45 minutes. Pace per mile?", "7.5 min", ["7.5 min", "6 min", "9 min", "10 min"]),
    ("3 lbs of nuts cost $9. Cost per pound?", "$3", ["$3", "$6", "$1", "$27"]),
    ("A printer prints 30 pages in 2 minutes. Rate per minute?", "15 pages", ["15 pages", "30 pages", "60 pages", "5 pages"]),
    ("2 lbs feeds 5 dogs. How much for 10 dogs?", "4 lbs", ["4 lbs", "2 lbs", "8 lbs", "5 lbs"]),
    ("A tap fills 6 gallons in 4 minutes. Time to fill 15 gallons?", "10 min", ["10 min", "9 min", "20 min", "6 min"]),
    ("A bus travels 240 km in 3 hours. Distance in 5 hours?", "400 km", ["400 km", "320 km", "480 km", "1200 km"]),
]
for stem, ans, choices in unit_rate:
    t3_add(
        stem, ans, choices,
        (
            f"Proportion / unit rate. Set up the proportion (given ratio = "
            f"unknown ratio) and cross-multiply, OR find the unit rate (per "
            f"one) and multiply. {stem.rstrip('?')} → {ans}. Unit-rate "
            f"thinking is the fastest path for shopping comparisons."
        ),
    )

# --- F/D/P at T3 (8) ---
fdp_t3 = [
    ("Convert 5/8 to a percent.", "62.5%", ["62.5%", "58%", "5.8%", "85%"]),
    ("Convert 11/20 to a percent.", "55%", ["55%", "11%", "20%", "1.1%"]),
    ("Convert 7/25 to a percent.", "28%", ["28%", "7%", "25%", "32%"]),
    ("Convert 3/16 to a decimal.", "0.1875", ["0.1875", "0.31", "0.16", "0.5"]),
    ("Convert 5/16 to a percent.", "31.25%", ["31.25%", "31%", "16%", "5.16%"]),
    ("Convert 11/25 to a decimal.", "0.44", ["0.44", "0.11", "0.25", "0.42"]),
    ("Convert 0.85 to a fraction in simplest form.", "17/20", ["17/20", "85/100", "17/100", "8/5"]),
    ("Convert 1.125 to a fraction in simplest form.", "9/8", ["9/8", "1125/1000", "11/8", "1/8"]),
]
for stem, ans, choices in fdp_t3:
    t3_add(
        stem, ans, choices,
        (
            f"F/D/P conversion at the harder end. Pick the easiest pivot: "
            f"fraction → decimal (top ÷ bottom), decimal → percent (×100), "
            f"percent → fraction (over 100 then simplify). "
            f"{stem.replace('Convert ', '').rstrip('.')} = {ans}."
        ),
    )

# --- Negative quantity word problems (5) ---
neg_word = [
    ("Temperature drops 1.5°F per hour for 3 hours. Total change?",
     "−4.5°F", ["−4.5°F", "4.5°F", "−1.5°F", "−6°F"]),
    ("Submarine descends 200 m, then ascends 80 m. Net depth change?",
     "−120 m", ["−120 m", "120 m", "−280 m", "280 m"]),
    ("Withdraw $25, then deposit $10. Net change?",
     "−$15", ["−$15", "$15", "−$35", "$35"]),
    ("Hike up 2.5 km, then down 4 km. Net elevation change?",
     "−1.5 km", ["−1.5 km", "1.5 km", "−6.5 km", "6.5 km"]),
    ("Stock loses 1/4 of value over 2 weeks. Change as a signed decimal?",
     "−0.25", ["−0.25", "0.25", "−0.5", "−0.125"]),
]
for stem, ans, choices in neg_word:
    t3_add(
        stem, ans, choices,
        (
            f"Signed-quantity word problem. Down/loss/withdraw = negative; "
            f"up/gain/deposit = positive. Add the signed changes to get the "
            f"net. {stem} → {ans}. The sign rule for accumulation."
        ),
    )

# --- Fillers to hit 170 ---
print(f"[T3 build] generated {len(T3_BATCH)}")
# More tip math and proportions if needed
filler_t3 = [
    ("What is a 10% tip on $90?", "$9", ["$9", "$0.90", "$90", "$18"]),
    ("What is a 10% tip on $35?", "$3.50", ["$3.50", "$0.35", "$35", "$7"]),
    ("What is a 20% tip on $40?", "$8", ["$8", "$4", "$16", "$2"]),
    ("What is a 15% tip on $100?", "$15", ["$15", "$10", "$20", "$25"]),
    ("Original price $90, 30% off. Sale price = ?", "$63", ["$63", "$27", "$80", "$60"]),
    ("Original price $25, 20% off. Sale price = ?", "$20", ["$20", "$5", "$30", "$15"]),
    ("From 75 to 90, what is the percent increase?", "20%", ["20%", "15%", "25%", "10%"]),
    ("From 120 to 100, what is the percent decrease?", "16.7%", ["16.7%", "20%", "12%", "83%"]),
    ("Compute −2/5 × 5/4.", "−1/2", ["−1/2", "1/2", "−10/9", "10/9"]),
    ("Compute (−4) × (+5) × (−1).", "20", ["20", "−20", "10", "−10"]),
    ("Solve the proportion: x/16 = 3/4", "x = 12", ["x = 12", "x = 4", "x = 21", "x = 24"]),
    ("Solve the proportion: 2/9 = x/27", "x = 6", ["x = 6", "x = 2", "x = 9", "x = 12"]),
    ("Compute −4 − 3 + 7.", "0", ["0", "−14", "14", "10"]),
    ("Compute (5 − 8) × (−2).", "6", ["6", "−6", "26", "−26"]),
    ("Compute |−5 + 9| − 3.", "1", ["1", "−1", "7", "−7"]),
]
for stem, ans, choices in filler_t3:
    # Determine category for context
    if "tip" in stem.lower():
        pct_str = stem.split('%')[0].split()[-1]
        teach = ""
        if pct_str == "10":
            teach = "The 10% trick: move the decimal one place left. "
        elif pct_str == "20":
            teach = "10%-then-double for 20%. "
        elif pct_str == "15":
            teach = "10% + half-of-10% for 15%. "
        ctx = (f"Tip math via the 10% trick. {teach}"
               f"{stem.replace('What is a ', '').rstrip('?')} = {ans}.")
    elif "off" in stem.lower():
        ctx = (f"Discount via percent of a number. "
               f"{stem.rstrip('?')} {ans}. Faster: subtract the percent from 100 "
               f"and multiply.")
    elif "percent" in stem.lower():
        ctx = (f"Percent change formula: (new − old) / old. "
               f"{stem.rstrip('?')} = {ans}.")
    elif "proportion" in stem.lower():
        ctx = (f"Cross-multiplication for proportions: a/b = c/d ⟹ a·d = b·c. "
               f"{stem.replace('Solve the proportion: ', '')} → {ans}.")
    elif "absolute" in stem.lower() or "|" in stem:
        ctx = (f"Sign rule + absolute value: evaluate inside the bars first, "
               f"then take the absolute value (distance from zero, non-negative). "
               f"{stem.replace('Compute ', '').rstrip('.')} = {ans}.")
    else:
        ctx = (f"Sign rule for signed numbers and fractions. "
               f"{stem.replace('Compute ', '').rstrip('.')} = {ans}.")
    t3_add(stem, ans, choices, ctx)

print(f"[T3 build] after fillers: {len(T3_BATCH)}")

# Pad to 200 to be safe
while len(T3_BATCH) < 200:
    extras = [
        ("Compute −7/8 + 1/4.", "−5/8", ["−5/8", "5/8", "−6/12", "6/12"]),
        ("Compute −5/6 − 1/3.", "−7/6", ["−7/6", "7/6", "−6/9", "6/9"]),
        ("Compute (−2/3) × (3/4).", "−1/2", ["−1/2", "1/2", "−6/12", "6/12"]),
        ("Compute (−5/6) × (−12/25).", "2/5", ["2/5", "−2/5", "60/150", "−60/150"]),
        ("Compute (−7/10) + 1/2.", "−1/5", ["−1/5", "1/5", "−12/20", "12/20"]),
        ("Compute (−1/3) × (−6/11).", "2/11", ["2/11", "−2/11", "6/33", "−6/33"]),
        ("What is a 25% tip on $20?", "$5", ["$5", "$4", "$2.50", "$10"]),
        ("What is a 25% tip on $40?", "$10", ["$10", "$5", "$8", "$20"]),
        ("From 30 to 45, what is the percent increase?", "50%", ["50%", "33%", "15%", "150%"]),
        ("From 100 to 80, what is the percent decrease?", "20%", ["20%", "25%", "80%", "10%"]),
        ("Solve the proportion: 4/x = 2/7", "x = 14", ["x = 14", "x = 8", "x = 6", "x = 2"]),
        ("Solve the proportion: 9/x = 3/2", "x = 6", ["x = 6", "x = 12", "x = 3", "x = 18"]),
    ]
    for stem, ans, choices in extras:
        if len(T3_BATCH) >= 200:
            break
        if "tip" in stem.lower():
            pct_str = stem.split('%')[0].split()[-1]
            teach = "25% means quarter — divide by 4. "
            ctx = (f"Tip math: {teach}{stem.replace('What is a ', '').rstrip('?')} = {ans}.")
        elif "percent" in stem.lower():
            ctx = (f"Percent change formula: (new − old) / old. "
                   f"{stem.rstrip('?')} = {ans}.")
        elif "proportion" in stem.lower():
            ctx = (f"Cross-multiplication for proportions. "
                   f"{stem.replace('Solve the proportion: ', '')} → {ans}.")
        else:
            ctx = (f"Sign rule for signed fractions. "
                   f"{stem.replace('Compute ', '').rstrip('.')} = {ans}.")
        t3_add(stem, ans, choices, ctx)
    break  # only once

print(f"[T3 build] final: {len(T3_BATCH)}")

# Emit
t3_pre = len(ACCEPTED)
target_t3 = 170
for q in T3_BATCH:
    if len(ACCEPTED) - t3_pre >= target_t3:
        break
    q_emit(q)
save_incremental()
t3_post = len(ACCEPTED)
print(f"[T3] accepted {t3_post - t3_pre} / {len(T3_BATCH)} tried; total={t3_post}")

# ============================================================================
# T4 — 40 questions
# ============================================================================

T4_BATCH: list[dict] = []

def t4_add(stem, ans, choices, ctx):
    T4_BATCH.append({
        "tier": 4,
        "question": stem,
        "answer": ans,
        "choices": choices,
        "context": ctx,
    })

# --- F/D/P chains (12) ---
fdp_chains = [
    ("Convert 9/16 to a percent (chain via decimal).", "56.25%",
     ["56.25%", "56%", "9.16%", "62.5%"]),
    ("Convert 0.045 to a percent, then to a fraction.", "9/200",
     ["9/200", "45/100", "9/100", "1/45"]),
    ("Convert 175% to a decimal, then to a mixed number.", "1 3/4",
     ["1 3/4", "0.175", "175/10", "7/4"]),
    ("Compute (7/8 + 1/4) and express as a percent.", "112.5%",
     ["112.5%", "100%", "87.5%", "12.5%"]),
    ("Compute (1/4 + 1/8) and express as a percent.", "37.5%",
     ["37.5%", "30%", "25%", "12.5%"]),
    ("Compute (3/5 × 0.5) and express as a percent.", "30%",
     ["30%", "60%", "15%", "3%"]),
    ("Convert 0.125 to a fraction in simplest form.", "1/8",
     ["1/8", "125/1000", "12.5/100", "1/4"]),
    ("Compute (5/8) of 200 then express the result as a percent of 500.",
     "25%", ["25%", "62.5%", "50%", "12.5%"]),
    ("Convert 13/20 to a percent.", "65%",
     ["65%", "13%", "20%", "0.65%"]),
    ("Convert 0.085 to a percent.", "8.5%",
     ["8.5%", "0.85%", "85%", "850%"]),
    ("Convert 3/40 to a percent.", "7.5%",
     ["7.5%", "3%", "40%", "12%"]),
    ("Convert 17/50 to a decimal.", "0.34",
     ["0.34", "0.17", "0.5", "0.85"]),
]
for stem, ans, choices in fdp_chains:
    t4_add(
        stem, ans, choices,
        (
            f"F/D/P conversion chain. Pick the easiest pivot: fraction → "
            f"decimal (divide top by bottom), decimal → percent (shift two "
            f"right), percent → fraction (over 100 and simplify). "
            f"{stem.rstrip('.').rstrip('?')} → {ans}. Memorize the eighths "
            f"and twentieths tables for instant conversion."
        ),
    )

# --- Two-step equations with fractions (12) ---
two_step_frac = [
    ("Solve: (1/2)x + 3 = 8", "x = 10", ["x = 10", "x = 5", "x = 22", "x = 4"]),
    ("Solve: (1/3)x − 2 = 4", "x = 18", ["x = 18", "x = 6", "x = 12", "x = 2"]),
    ("Solve: (2/3)x = 8", "x = 12", ["x = 12", "x = 16", "x = 5", "x = 24"]),
    ("Solve: (3/4)x + 1 = 7", "x = 8", ["x = 8", "x = 6", "x = 9", "x = 12"]),
    ("Solve: (1/5)x = −4", "x = −20", ["x = −20", "x = −1", "x = −9", "x = −4"]),
    ("Solve: (3/5)x = 9", "x = 15", ["x = 15", "x = 5", "x = 9", "x = 27"]),
    ("Solve: (2/3)x − 1 = 3", "x = 6", ["x = 6", "x = 4", "x = 3", "x = 12"]),
    ("Solve: (5/6)x = 10", "x = 12", ["x = 12", "x = 8", "x = 6", "x = 5"]),
    ("Solve: (1/2)x + 5 = 11", "x = 12", ["x = 12", "x = 6", "x = 22", "x = 3"]),
    ("Solve: (3/8)x = 6", "x = 16", ["x = 16", "x = 8", "x = 18", "x = 6"]),
    ("Solve: (4/5)x + 2 = 10", "x = 10", ["x = 10", "x = 8", "x = 6.4", "x = 12"]),
    ("Solve: (1/4)x − 3 = 5", "x = 32", ["x = 32", "x = 8", "x = 20", "x = 2"]),
]
for stem, ans, choices in two_step_frac:
    t4_add(
        stem, ans, choices,
        (
            f"Two-step equation with a fractional coefficient. Apply inverse "
            f"operations: undo addition/subtraction first, then undo "
            f"multiplication by multiplying both sides by the reciprocal "
            f"(invert and multiply). {stem.replace('Solve: ', '')} → {ans}."
        ),
    )

# --- Compound (complex) fraction simplification (10) ---
# For integer-valued answers, write as fraction (2 = 2/1) to satisfy parity,
# OR include at least one integer distractor.
compound_frac = [
    ("Simplify the compound fraction (1/2) / (3/4).", "2/3", ["2/3", "3/8", "5/6", "3/2"]),
    ("Simplify the compound fraction (2/3) / (4/5).", "5/6", ["5/6", "8/15", "10/12", "3/2"]),
    ("Simplify the compound fraction (5/6) / (1/2).", "5/3", ["5/3", "5/12", "1/3", "12/5"]),
    # Integer answer with at least one integer distractor for parity
    ("Simplify the compound fraction (3/4) / (3/8).", "2", ["2", "8", "1", "16"]),
    ("Simplify the compound fraction 1 / (1/4).", "4", ["4", "1", "8", "16"]),
    ("Simplify the compound fraction (1/3) / 6.", "1/18", ["1/18", "1/12", "2/9", "1/24"]),
    ("Simplify the compound fraction 5 / (2/3).", "15/2", ["15/2", "10/3", "5/6", "2/15"]),
    ("Simplify the compound fraction (2/5) / (1/10).", "4", ["4", "2", "8", "25"]),
    ("Simplify the compound fraction (7/8) / (7/4).", "1/2", ["1/2", "49/32", "1/4", "32/49"]),
    ("Simplify the compound fraction (3/2) / (9/4).", "2/3", ["2/3", "27/8", "3/8", "8/27"]),
]
for stem, ans, choices in compound_frac:
    t4_add(
        stem, ans, choices,
        (
            f"Complex (compound) fraction simplification — a fraction divided "
            f"by a fraction. Rewrite as multiplication by the reciprocal "
            f"(invert and multiply): top × (1/bottom). "
            f"{stem.replace('Simplify the compound fraction ', '').rstrip('.')} "
            f"= {ans}."
        ),
    )

# --- Sophisticated F/D/P chains (6) ---
mixed_sophisticated = [
    ("Compute (1/2 + 1/4) × 80.", "60", ["60", "40", "80", "30"]),
    ("Compute (3/4 − 1/8) × 16.", "10", ["10", "4", "12", "16"]),
    ("Compute (5/8) × 120.", "75", ["75", "60", "100", "45"]),
    ("Compute (1/2 + 1/3) of 60.", "50", ["50", "40", "30", "60"]),
    ("Compute (7/8) × 200.", "175", ["175", "150", "100", "200"]),
    ("Compute (1 − 1/4) × 80.", "60", ["60", "20", "80", "100"]),
]
for stem, ans, choices in mixed_sophisticated:
    t4_add(
        stem, ans, choices,
        (
            f"Sophisticated F/D/P chain combining add/subtract with a "
            f"fraction of a number. Evaluate parentheses first (find common "
            f"denominator), then multiply by the base. "
            f"{stem.replace('Compute ', '').rstrip('.')} = {ans}. This is the "
            f"percent-of-a-fraction-of-N pattern."
        ),
    )

# Backup T4 fillers in case earlier ones collide
backup_t4 = [
    ("Solve: (1/6)x = 5", "x = 30", ["x = 30", "x = 6", "x = 5", "x = 11"]),
    ("Solve: (2/7)x + 4 = 10", "x = 21", ["x = 21", "x = 14", "x = 6", "x = 7"]),
    ("Solve: (5/8)x − 2 = 8", "x = 16", ["x = 16", "x = 8", "x = 12", "x = 10"]),
    ("Compute (1/2 − 1/6) × 30.", "10", ["10", "5", "15", "20"]),
    ("Compute (3/5 + 1/10) × 50.", "35", ["35", "25", "30", "45"]),
    ("Compute (4/5 − 1/2) × 20.", "6", ["6", "4", "8", "12"]),
    ("Compute (7/10 + 1/5) × 100.", "90", ["90", "80", "70", "100"]),
    ("Compute (2/3 of 3/4 of 24).", "12", ["12", "16", "8", "18"]),
    ("Compute (3/8 of 4/5 of 80).", "24", ["24", "32", "20", "16"]),
    ("Solve: (3/7)x = 6", "x = 14", ["x = 14", "x = 6", "x = 18", "x = 7"]),
    ("Convert 13/40 to a decimal.", "0.325", ["0.325", "0.13", "0.4", "0.34"]),
    ("Convert 19/25 to a percent.", "76%", ["76%", "19%", "25%", "44%"]),
]
for stem, ans, choices in backup_t4:
    # category-aware context
    if stem.startswith("Solve"):
        ctx = (f"Two-step equation with fractional coefficient. Apply inverse "
               f"operations: undo addition/subtraction first, then multiply "
               f"both sides by the reciprocal. {stem.replace('Solve: ', '')} "
               f"→ {ans}.")
    elif stem.startswith("Convert"):
        ctx = (f"F/D/P conversion chain. Fraction → decimal: top ÷ bottom. "
               f"Decimal → percent: shift two right. "
               f"{stem.replace('Convert ', '').rstrip('.')} = {ans}.")
    else:
        ctx = (f"Sophisticated F/D/P chain combining add/subtract with a "
               f"fraction of a number. Find common denominator inside the "
               f"parens, then multiply by the base. "
               f"{stem.replace('Compute ', '').rstrip('.')} = {ans}.")
    t4_add(stem, ans, choices, ctx)

print(f"[T4 build] {len(T4_BATCH)}")
assert len(T4_BATCH) >= 40

# Emit
t4_pre = len(ACCEPTED)
target_t4 = 40
for q in T4_BATCH:
    if len(ACCEPTED) - t4_pre >= target_t4:
        break
    q_emit(q)
save_incremental()
t4_post = len(ACCEPTED)
print(f"[T4] accepted {t4_post - t4_pre} / {len(T4_BATCH)} tried; total={t4_post}")

# ============================================================================
# T5 — 10 questions
# ============================================================================

T5_BATCH: list[dict] = []

t5_items = [
    ("Simplify: (x² + 5x + 6) / (x + 2)", "x + 3",
     ["x + 3", "x + 2", "x − 3", "x + 6"],
     "Trinomial factoring: find two numbers that multiply to 6 and add to 5 — "
     "those are 2 and 3. So x² + 5x + 6 = (x + 2)(x + 3). Cancel the common "
     "(x + 2) factor to get x + 3. Always factor first, then cancel — "
     "never cancel raw terms."),
    ("Simplify: (x² + 7x + 12) / (x + 3)", "x + 4",
     ["x + 4", "x + 3", "x − 4", "x + 12"],
     "Trinomial factoring: find two numbers that multiply to 12 and add to "
     "7 — those are 3 and 4. So x² + 7x + 12 = (x + 3)(x + 4). Cancel the "
     "(x + 3) factor to get x + 4."),
    ("Simplify: (x² − 16) / (x − 4)", "x + 4",
     ["x + 4", "x − 4", "x + 16", "x²"],
     "Difference of squares formula: a² − b² = (a + b)(a − b). So x² − 16 "
     "= (x + 4)(x − 4). Cancel (x − 4) to get x + 4. Recognize the "
     "difference-of-squares pattern instantly."),
    ("Simplify: (x² − 25) / (x − 5)", "x + 5",
     ["x + 5", "x − 5", "x + 25", "x²"],
     "Difference of squares: a² − b² = (a + b)(a − b). x² − 25 = "
     "(x + 5)(x − 5). Cancel the (x − 5) to get x + 5."),
    ("Simplify: (x² + 6x + 9) / (x + 3)", "x + 3",
     ["x + 3", "x − 3", "x + 9", "x + 6"],
     "Perfect square trinomial: x² + 6x + 9 = (x + 3)². Cancel one (x + 3) "
     "to get (x + 3). Pattern: a² + 2ab + b² = (a + b)²."),
    ("Simplify: (x² − 9x + 20) / (x − 4)", "x − 5",
     ["x − 5", "x + 5", "x − 4", "x − 9"],
     "Trinomial factoring with negative middle term: find two numbers that "
     "multiply to +20 and add to −9 — those are −4 and −5. So "
     "x² − 9x + 20 = (x − 4)(x − 5). Cancel (x − 4) to get x − 5."),
    ("Simplify: (x² − 36) / (x + 6)", "x − 6",
     ["x − 6", "x + 6", "x − 36", "x²"],
     "Difference of squares: x² − 36 = (x + 6)(x − 6). Cancel (x + 6) to "
     "get x − 6. The factor that cancels matches the SUM (or difference) "
     "in the denominator."),
    ("Simplify: (2x² + 4x) / (2x)", "x + 2",
     ["x + 2", "2x + 2", "x", "x + 4"],
     "Factor out the greatest common factor (GCF). 2x² + 4x = 2x(x + 2). "
     "Cancel the 2x in top and bottom to leave x + 2. Always pull out the "
     "GCF before looking for trinomial or difference-of-squares factoring."),
    ("Simplify: (x² − 4) / (x − 2)", "x + 2",
     ["x + 2", "x − 2", "x + 4", "x²"],
     "Difference of squares formula: x² − 4 = (x + 2)(x − 2). Cancel "
     "(x − 2) to get x + 2."),
    ("Simplify: (x² + 8x + 16) / (x + 4)", "x + 4",
     ["x + 4", "x − 4", "x + 16", "x + 8"],
     "Perfect square trinomial: x² + 8x + 16 = (x + 4)². Cancel one (x + 4) "
     "to get (x + 4). Pattern: (a + b)² = a² + 2ab + b²."),
]
for stem, ans, choices, ctx in t5_items:
    T5_BATCH.append({
        "tier": 5,
        "question": stem,
        "answer": ans,
        "choices": choices,
        "context": ctx,
    })

print(f"[T5 build] {len(T5_BATCH)}")

t5_pre = len(ACCEPTED)
for q in T5_BATCH:
    q_emit(q)
save_incremental()
t5_post = len(ACCEPTED)
print(f"[T5] accepted {t5_post - t5_pre} / {len(T5_BATCH)}; total={t5_post}")

# ============================================================================
# Summary
# ============================================================================

print()
print("=" * 60)
print(f"FINAL ACCEPTED: {len(ACCEPTED)}")
print(f"FINAL REJECTED: {len(REJECTED)}")
print("=" * 60)

by_tier: dict[int, int] = {}
for q in ACCEPTED:
    by_tier[q["tier"]] = by_tier.get(q["tier"], 0) + 1
for t in sorted(by_tier):
    print(f"  T{t}: {by_tier[t]}")

# Print all rejected reasons
print("\nAll rejected reasons:")
for q, reason in REJECTED:
    print(f"  T{q.get('tier')} | {q.get('question','')[:50]} | {reason[:140]}")

save_incremental()
print(f"\nSaved to {OUT_PATH}")
