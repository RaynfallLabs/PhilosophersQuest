#!/usr/bin/env python3
"""Build the snappy-math bank v3 (v2.14.1).

Replaces data/questions/math.json with a flashcard-oriented ladder that stays
recall-focused across all 5 tiers. Every stem is a single line, every answer
is a single value (no word problems, no diagrams).

Speed targets per tier:
  T1  1-2s   Foundation: +/- facts to 20, missing addend, count-by
  T2  2-3s   Times tables 0-12, doubles/halves, rounding, ±10s, skip-count
  T3  3-4s   Squares to 15, F/D/% equivalents, %-shortcuts, 2-digit arithmetic
  T4  4-5s   Squares to 20, cubes to 6, powers of 2, %-shortcuts, 1-step algebra
  T5  5-6s   2x2 distribution, teen squares, √/∛ recall, fraction ops, 2-step algebra

See docs/design/math_bank_v3.md.
"""
from __future__ import annotations
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MATH_JSON = ROOT / 'data' / 'questions' / 'math.json'

random.seed(20260912)  # deterministic build

# ---------------------------------------------------------------------------
# Distractor helpers
# ---------------------------------------------------------------------------

def _int_distractors(correct: int, n: int = 3) -> list[int]:
    """Generate `n` plausible wrong integer answers near `correct`.
    Off-by-1/2/5/10 with sign flips as needed. Never returns correct itself."""
    pool = set()
    # Off-by-small errors (typical child slip)
    for delta in (1, -1, 2, -2, 5, -5, 10, -10):
        c = correct + delta
        if c != correct and c >= 0:
            pool.add(c)
    # Digit-swap style for 2-digit numbers
    if correct >= 10:
        s = str(correct)
        rev = int(s[::-1])
        if rev != correct and rev >= 0:
            pool.add(rev)
    # Half / double
    if correct > 1:
        pool.add(correct * 2)
        if correct % 2 == 0:
            pool.add(correct // 2)
    # Ensure enough variety
    pool.discard(correct)
    if len(pool) < n:
        # Fall back: random nearby ints
        for _ in range(20):
            c = correct + random.randint(-15, 15)
            if c != correct and c >= 0:
                pool.add(c)
            if len(pool) >= n + 2:
                break
    picks = random.sample(sorted(pool), min(n, len(pool)))
    return picks


def _str_distractors(correct: str, candidates: list[str], n: int = 3) -> list[str]:
    """Pick n plausible wrong string answers from a candidate list."""
    pool = [c for c in candidates if c != correct]
    if len(pool) < n:
        return random.sample(pool, len(pool)) if pool else []
    return random.sample(pool, n)


def _build_q(tier: int, stem: str, answer: str, wrongs: list[str], context: str = '') -> dict:
    """Assemble a question dict with shuffled choices."""
    choices = [answer] + [str(w) for w in wrongs][:3]
    while len(choices) < 4:
        # Pad with fake distractors if we somehow have fewer than 3 wrongs
        choices.append(str(int(answer) + len(choices) if answer.lstrip('-').isdigit() else answer + '?'))
    random.shuffle(choices)
    q = {
        'tier': tier,
        'question': stem,
        'answer': str(answer),
        'choices': choices,
    }
    if context:
        q['context'] = context
    return q


def _int_q(tier: int, stem: str, correct: int, context: str = '') -> dict:
    wrongs = _int_distractors(correct)
    return _build_q(tier, stem, str(correct), [str(w) for w in wrongs], context)


# ---------------------------------------------------------------------------
# TIER 1 — Foundation (K-Grade 2, 1-2s recall)
# ---------------------------------------------------------------------------
# Addition/subtraction facts to 20, missing addend, count-by patterns.

def build_tier1() -> list[dict]:
    out = []

    # Addition facts a + b, 1 ≤ a,b ≤ 9 (81 facts, treat commutative as separate for drill)
    for a in range(1, 10):
        for b in range(1, 10):
            out.append(_int_q(1, f"{a} + {b} = ?", a + b,
                              "Addition fact — memorize."))

    # Add-with-0 and add-with-10
    for a in range(0, 11):
        out.append(_int_q(1, f"{a} + 0 = ?", a, "Anything plus 0 is itself."))
        out.append(_int_q(1, f"0 + {a} = ?", a, "Zero identity: 0 + n = n."))
    for a in range(0, 11):
        out.append(_int_q(1, f"{a} + 10 = ?", a + 10, "Adding 10: just count on to the tens."))

    # Subtraction facts a - b where 0 ≤ b ≤ a ≤ 18
    for a in range(1, 19):
        for b in range(0, min(a, 9) + 1):
            out.append(_int_q(1, f"{a} - {b} = ?", a - b, "Subtraction fact — memorize."))

    # Missing addend: a + ? = c
    for a in range(1, 10):
        for c in range(a + 1, min(a + 10, 19)):
            out.append(_int_q(1, f"{a} + ? = {c}", c - a,
                              "Missing addend — think 'what plus a gives c?'."))

    # Missing subtrahend: c - ? = a (result form)
    for c in range(2, 19):
        for a in range(0, c):
            if c - a <= 9:  # keep the subtrahend small
                out.append(_int_q(1, f"{c} - ? = {a}", c - a,
                                  "Missing subtrahend."))

    # Count-by-2 (fill in the blank)
    for start in [0, 2, 4, 6, 8, 10]:
        for steps in [1, 2, 3, 4]:
            val = start + 2 * steps
            out.append(_int_q(1, f"Count by 2s: {start}, {start+2}, {start+4}, ?",
                              start + 6, "Skip-count by 2."))
            break  # one per start is enough

    # Count-by-5 / 10
    for base in [0, 5, 10, 15, 20, 25]:
        out.append(_int_q(1, f"Count by 5s: {base}, {base+5}, {base+10}, ?",
                          base + 15, "Skip-count by 5."))
    for base in [0, 10, 20, 30]:
        out.append(_int_q(1, f"Count by 10s: {base}, {base+10}, {base+20}, ?",
                          base + 30, "Skip-count by 10."))

    # Doubles fact drill (fast recall aid)
    for n in range(1, 11):
        out.append(_int_q(1, f"Double {n}?", n * 2, "Doubles — memorize."))

    return out


# ---------------------------------------------------------------------------
# TIER 2 — Times Tables (Grade 3-4, 2-3s recall)
# ---------------------------------------------------------------------------
# 0-12 multiplication, division, doubles/halves of 2-digit, rounding, ±10s

def build_tier2() -> list[dict]:
    out = []

    # Multiplication facts 0×0 through 12×12
    for a in range(0, 13):
        for b in range(0, 13):
            out.append(_int_q(2, f"{a} × {b} = ?", a * b,
                              "Times-table fact."))

    # Division: c ÷ b, where c = a × b (0 not allowed as divisor)
    for a in range(1, 13):
        for b in range(1, 13):
            c = a * b
            out.append(_int_q(2, f"{c} ÷ {b} = ?", a,
                              "Division = inverse of multiplication."))

    # Double 2-digit numbers (even) — mental doubling
    for n in list(range(11, 51, 2)) + list(range(12, 52, 2)):
        out.append(_int_q(2, f"Double {n}?", n * 2,
                          "Doubling a 2-digit — double tens, double ones."))

    # Halve even 2-digit numbers
    for n in range(12, 101, 2):
        if random.random() < 0.55:
            out.append(_int_q(2, f"Half of {n}?", n // 2,
                              "Halving — split into tens and ones."))

    # Round to nearest 10
    for n in list(range(11, 100, 3)):
        rounded = 10 * round(n / 10)
        out.append(_int_q(2, f"Round {n} to nearest 10?", rounded,
                          "Round: <5 down, ≥5 up."))

    # Round to nearest 100
    for n in list(range(105, 950, 27)):
        rounded = 100 * round(n / 100)
        out.append(_int_q(2, f"Round {n} to nearest 100?", rounded,
                          "Round: look at the tens digit."))

    # ±10s
    for a in list(range(15, 90, 4)):
        for b in [10, 20, 30]:
            out.append(_int_q(2, f"{a} + {b} = ?", a + b, "Add multiples of 10."))
            if a > b:
                out.append(_int_q(2, f"{a} - {b} = ?", a - b, "Subtract multiples of 10."))

    # Skip-count by 3, 4, 6, 7, 8
    for step in [3, 4, 6, 7, 8]:
        for start_mult in [0, 1, 2]:
            start = step * start_mult
            out.append(_int_q(2,
                              f"Count by {step}s: {start}, {start+step}, {start+2*step}, ?",
                              start + 3 * step, f"Skip-count by {step}."))

    return out


# ---------------------------------------------------------------------------
# TIER 3 — Rapid Composites (Grade 5-6, 3-4s recall)
# ---------------------------------------------------------------------------
# Squares to 15, F/D/% equivalents, %-shortcuts, 2-digit ± 2-digit,
# multi-digit × single-digit, order-of-ops with 3 numbers.

def build_tier3() -> list[dict]:
    out = []

    # Squares 1²-15² (memorized)
    for n in range(1, 16):
        out.append(_int_q(3, f"{n}² = ?", n * n,
                          "Squares 1-15 — memorize."))
        # Alternative phrasing
        out.append(_int_q(3, f"{n} squared = ?", n * n,
                          "Squares 1-15 — memorize."))

    # Fraction ↔ decimal ↔ percent equivalents (common set)
    equivs = [
        ('1/2', '0.5', '50%'),
        ('1/4', '0.25', '25%'),
        ('3/4', '0.75', '75%'),
        ('1/5', '0.2', '20%'),
        ('2/5', '0.4', '40%'),
        ('3/5', '0.6', '60%'),
        ('4/5', '0.8', '80%'),
        ('1/10', '0.1', '10%'),
        ('3/10', '0.3', '30%'),
        ('7/10', '0.7', '70%'),
        ('9/10', '0.9', '90%'),
        ('1/3', '0.333', '33.3%'),
        ('2/3', '0.667', '66.7%'),
        ('1/8', '0.125', '12.5%'),
        ('1/20', '0.05', '5%'),
    ]
    all_percents = [p for _, _, p in equivs]
    all_decimals = [d for _, d, _ in equivs]
    all_fracs = [f for f, _, _ in equivs]
    for frac, dec, pct in equivs:
        # frac → percent
        wrongs = _str_distractors(pct, all_percents)
        out.append(_build_q(3, f"{frac} as a percent?", pct, wrongs,
                            "Common F↔D↔% equivalent — memorize."))
        # decimal → percent
        wrongs = _str_distractors(pct, all_percents)
        out.append(_build_q(3, f"{dec} as a percent?", pct, wrongs,
                            "Move decimal 2 places right for %."))
        # percent → decimal
        wrongs = _str_distractors(dec, all_decimals)
        out.append(_build_q(3, f"{pct} as a decimal?", dec, wrongs,
                            "Move decimal 2 places left for decimal."))

    # Percent shortcuts: 10% of X, 25% of X, 50% of X, 75% of X
    for pct, factor in [(10, 0.1), (25, 0.25), (50, 0.5), (75, 0.75)]:
        for x in [20, 40, 60, 80, 100, 120, 200, 400, 800]:
            ans = int(x * factor)
            out.append(_int_q(3, f"{pct}% of {x}?", ans,
                              f"{pct}% shortcut: memorize the multiplier."))

    # 2-digit + 2-digit — REQUIRE regrouping (ones-column carry) so the fact
    # isn't trivially easy at T3. Filter until the ones digits sum to >= 10.
    added = 0
    while added < 70:
        a = random.randint(15, 89)
        b = random.randint(15, 89)
        if (a % 10) + (b % 10) < 10:
            continue   # no carry -> trivially T1/T2; skip
        out.append(_int_q(3, f"{a} + {b} = ?", a + b,
                          "Add tens, add ones (with carry), combine."))
        added += 1

    # 2-digit − 2-digit — REQUIRE a meaningful gap AND borrow. Diff >= 15 so
    # trivial pairs like 74-72 don't slip in; a's ones digit < b's ones digit
    # forces a borrow (the harder mental step).
    added = 0
    while added < 70:
        a = random.randint(35, 99)
        b = random.randint(15, a - 15)   # diff at least 15
        if (a % 10) >= (b % 10):
            continue   # no borrow required -> too easy for T3
        out.append(_int_q(3, f"{a} - {b} = ?", a - b,
                          "Subtract with borrow: unwrap a ten."))
        added += 1

    # Multi-digit × single-digit (sample)
    for _ in range(60):
        a = random.randint(11, 49)
        b = random.randint(2, 9)
        out.append(_int_q(3, f"{a} × {b} = ?", a * b,
                          "Multiply by parts: tens×b + ones×b."))

    # Order of operations with 3 numbers (× before +)
    for _ in range(30):
        a = random.randint(2, 15)
        b = random.randint(2, 9)
        c = random.randint(2, 9)
        ans = a + b * c
        out.append(_int_q(3, f"{a} + {b} × {c} = ?", ans,
                          "Order of ops: multiply first."))
    for _ in range(30):
        a = random.randint(2, 20)
        b = random.randint(2, 9)
        c = random.randint(2, 9)
        ans = a - b * c if a >= b * c else b * c - a
        stem = f"{a} - {b} × {c} = ?" if a >= b * c else f"{b} × {c} - {a} = ?"
        out.append(_int_q(3, stem, ans, "Order of ops: multiply first."))

    # --- v3.1 demotions from T4 (grade 5-6 material) ---

    # Small perfect-square roots (√4 through √49) — inverse of memorized squares
    for root in [2, 3, 4, 5, 6, 7]:
        for _ in range(2):
            out.append(_int_q(3, f"√{root*root} = ?", root,
                              "Small perfect-square root — memorize."))

    # Powers of 10 (10^1 through 10^3) — count the zeros
    for k in range(1, 4):
        for _ in range(3):
            out.append(_int_q(3, f"10^{k} = ?", 10 ** k,
                              "Powers of 10 — count the zeros."))

    # Basic negative arithmetic (add / subtract only — sign multiplication stays T4)
    neg_basic = [
        ('-3 + 5 = ?', 2), ('-5 + 3 = ?', -2), ('-4 + 10 = ?', 6),
        ('-7 + 2 = ?', -5), ('-8 + 8 = ?', 0), ('-10 + 4 = ?', -6),
        ('4 - 7 = ?', -3), ('3 - 10 = ?', -7), ('7 - 15 = ?', -8),
        ('0 - 4 = ?', -4), ('5 - 12 = ?', -7), ('2 - 9 = ?', -7),
        ('-3 - 4 = ?', -7), ('-5 - 5 = ?', -10), ('-2 - 8 = ?', -10),
    ]
    for stem, ans in neg_basic:
        out.append(_int_q(3, stem, ans,
                          "Negative arithmetic — track the sign."))

    # Simple decimal arithmetic (grade 5-6, uses memorized fraction equivalents)
    decimal_basic = [
        ('0.5 + 0.5 = ?', '1'), ('0.5 + 0.25 = ?', '0.75'),
        ('0.75 + 0.25 = ?', '1'), ('0.25 + 0.25 = ?', '0.5'),
        ('1.5 + 0.5 = ?', '2'), ('2.5 + 1.5 = ?', '4'),
        ('1 - 0.5 = ?', '0.5'), ('1 - 0.25 = ?', '0.75'),
        ('1 - 0.1 = ?', '0.9'), ('0.5 × 2 = ?', '1'),
        ('0.25 × 4 = ?', '1'), ('0.5 × 10 = ?', '5'),
        ('0.25 × 8 = ?', '2'), ('1.5 × 2 = ?', '3'),
        ('1.5 × 4 = ?', '6'), ('2.5 × 2 = ?', '5'),
        ('2.5 × 4 = ?', '10'), ('0.1 × 100 = ?', '10'),
        ('0.01 × 100 = ?', '1'), ('10 ÷ 0.5 = ?', '20'),
        ('10 ÷ 0.25 = ?', '40'), ('6 ÷ 0.5 = ?', '12'),
        ('4 ÷ 0.25 = ?', '16'),
    ]
    dec_pool = list({a for _, a in decimal_basic})
    for stem, ans in decimal_basic:
        wrongs = _str_distractors(ans, dec_pool)
        out.append(_build_q(3, stem, ans, wrongs,
                            "Decimal fluency — same skill as common fractions."))

    # Ratio simplification (same skill as fraction reduction, already T3)
    ratio_facts = [
        ('4:8 simplified?', '1:2'), ('6:9 simplified?', '2:3'),
        ('10:15 simplified?', '2:3'), ('12:18 simplified?', '2:3'),
        ('8:12 simplified?', '2:3'), ('9:12 simplified?', '3:4'),
        ('15:20 simplified?', '3:4'), ('16:24 simplified?', '2:3'),
        ('20:30 simplified?', '2:3'), ('14:21 simplified?', '2:3'),
        ('6:8 simplified?', '3:4'), ('25:50 simplified?', '1:2'),
        ('4:16 simplified?', '1:4'), ('9:15 simplified?', '3:5'),
        ('12:16 simplified?', '3:4'),
    ]
    ratio_pool = list({a for _, a in ratio_facts})
    for stem, ans in ratio_facts:
        wrongs = _str_distractors(ans, ratio_pool)
        out.append(_build_q(3, stem, ans, wrongs,
                            "Simplify: divide both parts by their GCD."))

    return out


# ---------------------------------------------------------------------------
# TIER 4 — Advanced Fluency (Grade 7-8, 4-5s recall)
# ---------------------------------------------------------------------------
# Squares 16-20, cubes 1-6, powers of 2, %-shortcuts (15/20/30),
# fraction of qty, divisibility, 1-step algebra.

def build_tier4() -> list[dict]:
    out = []

    # Squares 16²-20² (memorized)
    for n in range(16, 21):
        for _ in range(3):
            out.append(_int_q(4, f"{n}² = ?", n * n,
                              "Squares 16-20 — memorize."))
        out.append(_int_q(4, f"{n} squared = ?", n * n,
                          "Squares 16-20 — memorize."))

    # Cubes 1³-10³ (extended past 6 for full drilling depth)
    for n in range(1, 11):
        for _ in range(3):
            out.append(_int_q(4, f"{n}³ = ?", n ** 3,
                              "Cubes 1-10 — memorize."))
        out.append(_int_q(4, f"{n} cubed = ?", n ** 3,
                          "Cubes 1-10 — memorize."))

    # Larger powers of 10 (10^4 through 10^6) — still count-zero pattern but
    # bigger integers to hold in short-term memory. 10^1-10^3 lives in T3.
    for k in range(4, 7):
        for _ in range(3):
            out.append(_int_q(4, f"10^{k} = ?", 10 ** k,
                              "Larger powers of 10 — count zeros carefully."))

    # Larger perfect-square roots (√64 through √225) — inverse of T3/T4 squares.
    for root in [8, 9, 10, 11, 12, 13, 14, 15]:
        for _ in range(2):
            out.append(_int_q(4, f"√{root*root} = ?", root,
                              "Perfect-square root — inverse of memorized squares."))

    # Fraction × integer (grade 7 mental composite)
    for p, q in [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 8),
                 (2, 3), (2, 5), (3, 4), (3, 5), (5, 6), (5, 8)]:
        for n in [12, 20, 24, 30, 40, 48, 60, 80, 100, 120]:
            if n % q == 0:
                ans = (n // q) * p
                out.append(_int_q(4, f"{p}/{q} × {n} = ?", ans,
                                  "Fraction × integer: divide by denominator, multiply by numerator."))

    # Simple exponent facts (2^5, 3^4, etc. — pure recall composites)
    exp_facts = [
        ('2^5 = ?', 32), ('2^6 = ?', 64), ('2^7 = ?', 128),
        ('2^8 = ?', 256), ('2^9 = ?', 512), ('2^10 = ?', 1024),
        ('3^3 = ?', 27), ('3^4 = ?', 81), ('3^5 = ?', 243),
        ('4^3 = ?', 64), ('4^4 = ?', 256), ('5^3 = ?', 125),
        ('5^4 = ?', 625), ('6^3 = ?', 216), ('7^3 = ?', 343),
    ]
    for stem, ans in exp_facts:
        out.append(_int_q(4, stem, ans, "Exponent recall — memorize the ladder."))

    # Powers of 2 (2¹-2¹⁰)
    for k in range(1, 11):
        for _ in range(2):
            out.append(_int_q(4, f"2^{k} = ?", 2 ** k,
                              "Powers of 2 — memorize (doubles)."))

    # % shortcuts — full common set (15/20/30/35/40/60/70/80/90)
    for pct, factor in [(15, 0.15), (20, 0.20), (30, 0.30),
                        (35, 0.35), (40, 0.40), (60, 0.60),
                        (70, 0.70), (80, 0.80), (90, 0.90)]:
        for x in [20, 40, 60, 80, 100, 120, 200, 300, 400, 500, 1000]:
            ans = int(x * factor)
            if ans == x * factor:  # integer answers only
                out.append(_int_q(4, f"{pct}% of {x}?", ans,
                                  f"{pct}% shortcut — decompose or use 10% × k."))

    # Fraction of quantity: p/q × N for common p/q
    frac_quantity_pairs = [
        (2, 5, [20, 30, 45, 60, 100]),
        (3, 5, [10, 20, 30, 50, 100]),
        (3, 4, [12, 20, 40, 80, 100]),
        (5, 6, [12, 24, 36, 60, 120]),
        (1, 6, [12, 18, 30, 60, 120]),
        (2, 3, [12, 18, 30, 60, 90]),
    ]
    for p, q, xs in frac_quantity_pairs:
        for x in xs:
            if x % q == 0:
                ans = (x // q) * p
                out.append(_int_q(4, f"{p}/{q} of {x}?", ans,
                                  "Fraction of qty: divide by q, times p."))

    # "Which is a factor of X?" — 4 divisor candidates, only 1 actually
    # divides X. Rewritten from the yes/no format after playtest: yes/no
    # gave weak distractors ('maybe', '0') and only tested one divisor rule.
    # This format forces the student to check all four candidates against
    # the divisibility rules for 3, 4, 6, 7, 8, 9, 11, 12.
    divisor_pool = [3, 4, 6, 7, 8, 9, 11, 12]
    added = 0
    while added < 45:
        target_div = random.choice(divisor_pool)
        multiplier = random.randint(3, 40)
        x = target_div * multiplier
        if x < 20 or x > 800:
            continue
        # Pick 3 divisors from the pool that do NOT divide x.
        non_divs = [d for d in divisor_pool if d != target_div and x % d != 0]
        if len(non_divs) < 3:
            continue
        # Avoid the case where target_div's factor is already covered by a
        # smaller divisor in the choices (e.g. 24 has 3, 4, 6, 8, 12 all as
        # divisors — pick a target where the OTHER choices genuinely don't
        # divide, so the student must apply the rule).
        wrongs = random.sample(non_divs, 3)
        out.append(_build_q(4, f"Which is a factor of {x}?", str(target_div),
                            [str(w) for w in wrongs],
                            f"Try each divisibility rule ({target_div} divides {x})."))
        added += 1

    # 1-step algebra: solve for x
    for _ in range(30):
        x = random.randint(2, 20)
        m = random.choice([2, 3, 4, 5, 6, 7, 8])
        c = m * x
        out.append(_int_q(4, f"Solve: {m}x = {c}", x,
                          "One-step algebra: divide."))
    for _ in range(20):
        x = random.randint(3, 25)
        b = random.randint(2, 15)
        c = x + b
        out.append(_int_q(4, f"Solve: x + {b} = {c}", x,
                          "One-step algebra: subtract."))
    for _ in range(20):
        x = random.randint(3, 20)
        b = random.randint(2, 10)
        c = x - b
        if c > 0:
            out.append(_int_q(4, f"Solve: x - {b} = {c}", x,
                              "One-step algebra: add."))

    # Sign multiplication (T4 stays — sign rule + memorized product)
    sign_mult_facts = [
        ('-3 × 4 = ?', -12), ('-2 × -5 = ?', 10), ('-6 × 3 = ?', -18),
        ('-4 × -4 = ?', 16), ('-10 × 5 = ?', -50), ('-3 × -3 = ?', 9),
        ('-7 × 2 = ?', -14), ('-8 × -3 = ?', 24), ('-6 × -6 = ?', 36),
        ('-5 × 6 = ?', -30), ('-9 × -2 = ?', 18), ('-4 × 7 = ?', -28),
        ('-12 × 3 = ?', -36), ('-2 × 15 = ?', -30), ('-4 × -8 = ?', 32),
        ('-15 × -2 = ?', 30), ('-6 × 4 = ?', -24), ('-5 × -5 = ?', 25),
    ]
    for stem, ans in sign_mult_facts:
        out.append(_int_q(4, stem, ans,
                          "Sign rule: same → +, different → -."))

    # 2-step algebra promoted from T5 (real grade-7/8 fluency work)
    for _ in range(30):
        x = random.randint(2, 15)
        m = random.choice([2, 3, 4, 5, 6])
        b = random.choice([-5, -3, 1, 3, 5, 7, 10])
        c = m * x + b
        stem = f"Solve: {m}x + {b} = {c}" if b >= 0 else f"Solve: {m}x - {abs(b)} = {c}"
        out.append(_int_q(4, stem, x,
                          "Two-step algebra: undo add/sub, then divide."))

    # Percent-of on 3-digit numbers requiring decomposition (real T4 work)
    for pct in [15, 25, 35, 45, 65, 85]:
        for x in [140, 160, 200, 220, 240, 280, 320, 360, 400, 440, 480, 520]:
            ans = int(x * pct / 100)
            if ans == x * pct / 100:  # integer answers only
                out.append(_int_q(4, f"{pct}% of {x}?", ans,
                                  f"3-digit %: use 10% + smaller %s or halve/decompose."))

    # Compound fractions (fraction of a fraction of a quantity)
    compound_frac = [
        ('1/2 of 1/3 of 60 = ?', 10), ('1/3 of 1/2 of 60 = ?', 10),
        ('1/2 of 1/4 of 80 = ?', 10), ('2/3 of 1/2 of 60 = ?', 20),
        ('3/4 of 1/2 of 40 = ?', 15), ('1/2 of 2/3 of 30 = ?', 10),
        ('2/5 of 1/2 of 100 = ?', 20), ('1/3 of 3/4 of 60 = ?', 15),
        ('1/4 of 2/3 of 60 = ?', 10), ('1/2 of 3/5 of 100 = ?', 30),
        ('1/5 of 1/2 of 200 = ?', 20), ('2/3 of 3/4 of 60 = ?', 30),
    ]
    for stem, ans in compound_frac:
        out.append(_int_q(4, stem, ans,
                          "Multiply the fractions first, then × the whole."))

    return out


# ---------------------------------------------------------------------------
# TIER 5 — Speed Composites (Grade 9+, 5-6s recall)
# ---------------------------------------------------------------------------
# 2x2 distribution, teen squares, √/∛ recall, fraction ops, 2-step algebra,
# percent of larger, "what % is X of Y".

def build_tier5() -> list[dict]:
    out = []

    # Teen squares (11²-19²) — should be memorized at this tier
    for n in range(11, 20):
        for _ in range(2):
            out.append(_int_q(5, f"{n}² = ?", n * n,
                              "Teen squares — memorize (or use (n-1)² + 2n - 1)."))

    # Square roots of memorized perfect squares
    perfect_squares = [
        (11, 121), (12, 144), (13, 169), (14, 196), (15, 225),
        (16, 256), (17, 289), (18, 324), (19, 361), (20, 400),
        (25, 625), (30, 900),
    ]
    for root, sq in perfect_squares:
        out.append(_int_q(5, f"√{sq} = ?", root,
                          "Memorized square root."))

    # Cube roots
    for n in range(1, 8):
        cube = n ** 3
        out.append(_int_q(5, f"∛{cube} = ?", n,
                          "Memorized cube root."))

    # 2-digit × 2-digit via distribution (expanded pool — the T5 workhorse)
    two_by_two_pairs = [
        # Doubles / near-doubles (easy anchors)
        (11, 11), (12, 12), (13, 13), (14, 14), (15, 15),
        (16, 16), (17, 17), (18, 18), (19, 19), (20, 20),
        (21, 21), (22, 22), (23, 23), (24, 24), (25, 25),
        # Teen × teen
        (11, 12), (11, 13), (11, 14), (11, 15), (11, 16),
        (12, 13), (12, 14), (12, 15), (12, 16), (12, 17),
        (13, 14), (13, 15), (13, 16), (13, 17), (13, 18),
        (14, 15), (14, 16), (14, 17), (14, 18), (14, 19),
        (15, 16), (15, 17), (15, 18), (15, 19), (15, 20),
        # Teen × 20-30
        (11, 20), (12, 20), (13, 20), (14, 20), (15, 20),
        (11, 25), (12, 25), (13, 25), (14, 25), (15, 25),
        (11, 30), (12, 30), (15, 30), (18, 20), (16, 20),
        # 20s × 20s (common)
        (20, 25), (20, 30), (25, 30), (20, 40), (25, 40),
        (30, 30), (30, 40), (25, 20), (24, 25),
    ]
    for a, b in two_by_two_pairs:
        for _ in range(2):  # extra drilling
            out.append(_int_q(5, f"{a} × {b} = ?", a * b,
                              "Distribute: a×tens + a×ones (then combine)."))

    # Fraction operations mental
    frac_ops = [
        ('1/2 + 1/4 = ?', '3/4', ['1/2', '2/4', '5/8']),
        ('1/2 + 1/3 = ?', '5/6', ['2/5', '1/6', '2/3']),
        ('1/3 + 1/6 = ?', '1/2', ['2/9', '1/9', '2/3']),
        ('2/3 + 1/6 = ?', '5/6', ['3/6', '3/9', '1/2']),
        ('1/4 + 1/6 = ?', '5/12', ['2/10', '2/24', '1/5']),
        ('3/4 - 1/2 = ?', '1/4', ['2/4', '2/6', '1/2']),
        ('5/6 - 1/3 = ?', '1/2', ['4/3', '4/6', '2/3']),
        ('2/3 - 1/6 = ?', '1/2', ['1/3', '1/6', '1/9']),
        ('1/2 × 1/3 = ?', '1/6', ['2/5', '1/5', '2/6']),
        ('2/3 × 3/4 = ?', '1/2', ['6/7', '5/12', '5/7']),
        ('3/4 × 2/5 = ?', '3/10', ['6/9', '5/9', '6/20']),
        ('2/5 × 5/6 = ?', '1/3', ['10/11', '7/11', '10/30']),
        ('1/2 ÷ 1/4 = ?', '2', ['1/8', '1/2', '4/2']),
        ('3/4 ÷ 1/2 = ?', '3/2', ['3/8', '2/3', '1/2']),
        ('2/3 ÷ 1/3 = ?', '2', ['2/9', '1/2', '1/3']),
    ]
    for stem, ans, wrongs in frac_ops:
        out.append(_build_q(5, stem, ans, wrongs,
                            "Fraction op: find common denom or invert-multiply."))

    # Distribution algebra: solve k(x + b) = c form (T5 — genuinely harder)
    for _ in range(20):
        x = random.randint(2, 12)
        k = random.choice([2, 3, 4, 5])
        b = random.choice([1, 2, 3, 4, 5])
        c = k * (x + b)
        out.append(_int_q(5, f"Solve: {k}(x + {b}) = {c}", x,
                          "Distribute first, or divide both sides by k first."))
    # Distribution with subtraction: k(x - b) = c
    for _ in range(15):
        x = random.randint(3, 15)
        k = random.choice([2, 3, 4, 5])
        b = random.choice([1, 2, 3, 4])
        c = k * (x - b)
        if c > 0:
            out.append(_int_q(5, f"Solve: {k}(x - {b}) = {c}", x,
                              "Divide both sides by k, then add b."))
    # Fraction-coefficient algebra: (1/k)x = c
    for _ in range(15):
        x = random.randint(2, 20)
        k = random.choice([2, 3, 4, 5, 6])
        if x % 1 == 0:
            c = x // k if x % k == 0 else None
            if c is not None:
                out.append(_int_q(5, f"Solve: x/{k} = {c}", x,
                                  "One-step with fraction: multiply both sides by k."))

    # Percent of larger numbers
    for pct in [15, 20, 25, 30, 40, 60, 75]:
        for x in [200, 240, 250, 300, 400, 500, 600, 800, 1000, 2000]:
            ans = int(x * pct / 100)
            if ans == x * pct / 100:  # only include exact answers
                out.append(_int_q(5, f"{pct}% of {x}?", ans,
                                  f"{pct}% shortcut."))

    # What percent is X of Y?
    for _ in range(30):
        y = random.choice([20, 40, 50, 100, 200, 250, 400, 500])
        pct = random.choice([10, 20, 25, 40, 50, 60, 75, 80])
        x = int(y * pct / 100)
        if x == y * pct / 100 and x != 0:
            out.append(_int_q(5, f"What % of {y} is {x}?", pct,
                              "Percent = (part / whole) × 100."))

    # Pythagorean triples — expanded list, both orderings
    pythagorean_triples = [
        (3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17),
        (7, 24, 25), (9, 40, 41), (20, 21, 29), (9, 12, 15),
        (10, 24, 26), (12, 16, 20), (15, 20, 25), (16, 30, 34),
    ]
    for a, b, c in pythagorean_triples:
        out.append(_int_q(5, f"Pyth. triple: legs {a}, {b}. Hypotenuse?", c,
                          "Memorize the classic triples + scaled versions."))
        out.append(_int_q(5, f"Pyth. triple: legs {b}, {a}. Hypotenuse?", c,
                          "Memorize the classic triples + scaled versions."))

    # Exponent rules (grade-8/9 core)
    for base in [2, 3, 5]:
        for m in range(1, 6):
            for n in range(1, 6):
                if m + n <= 8:  # keep answers manageable
                    ans = base ** (m + n)
                    out.append(_int_q(5, f"{base}^{m} × {base}^{n} = ?", ans,
                                      f"Exponent rule: a^m × a^n = a^(m+n) = {base}^{m+n}."))
    for base in [2, 3, 5]:
        for m in range(3, 7):
            for n in range(1, m):
                ans = base ** (m - n)
                out.append(_int_q(5, f"{base}^{m} ÷ {base}^{n} = ?", ans,
                                  f"Exponent rule: a^m ÷ a^n = a^(m-n) = {base}^{m-n}."))

    # Mental composites — small polynomial-in-head
    composite_facts = [
        ('2² + 3² = ?', 13), ('3² + 4² = ?', 25),
        ('5² - 3² = ?', 16), ('6² - 4² = ?', 20),
        ('4² × 2 = ?', 32), ('5² × 2 = ?', 50),
        ('3³ - 2² = ?', 23), ('2³ + 2² = ?', 12),
        ('4² + 5² = ?', 41), ('6² - 5² = ?', 11),
        ('7² - 6² = ?', 13), ('10² - 5² = ?', 75),
        ('2³ + 3³ = ?', 35), ('5² + 12² = ?', 169),
        ('8² + 6² = ?', 100), ('3² × 4 = ?', 36),
    ]
    for stem, ans in composite_facts:
        out.append(_int_q(5, stem, ans,
                          "Substitute the memorized square/cube, then compute."))

    # Percent change (from X to Y)
    percent_change_facts = [
        ('From 40 to 50: % increase?', 25),
        ('From 50 to 40: % decrease?', 20),
        ('From 20 to 25: % increase?', 25),
        ('From 25 to 20: % decrease?', 20),
        ('From 100 to 150: % increase?', 50),
        ('From 100 to 75: % decrease?', 25),
        ('From 200 to 250: % increase?', 25),
        ('From 80 to 100: % increase?', 25),
        ('From 60 to 45: % decrease?', 25),
        ('From 50 to 75: % increase?', 50),
        ('From 400 to 300: % decrease?', 25),
        ('From 10 to 15: % increase?', 50),
    ]
    for stem, ans in percent_change_facts:
        out.append(_int_q(5, stem, ans,
                          "% change = (new − old) / old × 100."))

    # Order-of-operations with 4 numbers
    for _ in range(20):
        a = random.randint(2, 15)
        b = random.randint(2, 9)
        c = random.randint(2, 9)
        d = random.randint(2, 8)
        # a + b × c − d  (mult first)
        ans = a + b * c - d
        if ans > 0:
            out.append(_int_q(5, f"{a} + {b} × {c} - {d} = ?", ans,
                              "Multiply first, then left-to-right."))
    for _ in range(15):
        a = random.randint(3, 15)
        b = random.randint(2, 6)
        c = random.randint(2, 5)
        d = random.randint(1, 4)
        # a × b + c × d
        ans = a * b + c * d
        out.append(_int_q(5, f"{a} × {b} + {c} × {d} = ?", ans,
                          "Both mults first, then add."))

    # Sum of first N integers (arithmetic-series recall)
    for n in [5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 50, 100]:
        ans = n * (n + 1) // 2
        out.append(_int_q(5, f"1+2+3+...+{n} = ?", ans,
                          "Sum formula: n(n+1)/2."))

    # Extended fraction-to-decimal (beyond common set)
    extended_fd = [
        ('3/8 as decimal?', '0.375'), ('5/8 as decimal?', '0.625'),
        ('7/8 as decimal?', '0.875'), ('1/6 as decimal?', '0.167'),
        ('5/6 as decimal?', '0.833'), ('1/12 as decimal?', '0.083'),
        ('5/12 as decimal?', '0.417'), ('7/12 as decimal?', '0.583'),
        ('11/12 as decimal?', '0.917'), ('2/9 as decimal?', '0.222'),
    ]
    ext_pool = list({a for _, a in extended_fd})
    for stem, ans in extended_fd:
        wrongs = _str_distractors(ans, ext_pool)
        out.append(_build_q(5, stem, ans, wrongs,
                            "Extended F↔D — divide the numerator by denominator."))

    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    all_qs = []
    all_qs.extend(build_tier1())
    all_qs.extend(build_tier2())
    all_qs.extend(build_tier3())
    all_qs.extend(build_tier4())
    all_qs.extend(build_tier5())

    # De-dupe (question stem + answer)
    seen = set()
    unique = []
    for q in all_qs:
        key = (q['tier'], q['question'], q['answer'])
        if key not in seen:
            seen.add(key)
            unique.append(q)

    # Sanity: assert every question has choices with correct answer inside
    bad = [q for q in unique if q['answer'] not in q['choices']]
    if bad:
        raise SystemExit(f"BUG: {len(bad)} questions have answer not in choices. First: {bad[0]}")

    MATH_JSON.write_text(json.dumps(unique, indent=2, ensure_ascii=False), encoding='utf-8')

    from collections import Counter
    by_tier = Counter(q['tier'] for q in unique)
    print(f"Wrote {len(unique)} questions to {MATH_JSON}")
    for t in sorted(by_tier):
        print(f"  Tier {t}: {by_tier[t]:5} questions")


if __name__ == '__main__':
    main()
