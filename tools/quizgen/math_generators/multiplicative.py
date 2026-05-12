"""Multiplicative computation strategies: times-table anchors,
multiply-by-5/9/11, halve-then-double, multiply-by-powers-of-10,
doubling chains.

Each function returns a list of question dicts. Strategies anchored to
docs/quiz/math_strategies.md Pillar 1 § Multiplicative.
"""
from __future__ import annotations

from tools.quizgen.math_generators.common import make_question


# ----- times_table_anchor (T1) -----
def generate_times_tables() -> list[dict]:
    """T1: every product 1..12 × 1..12, with off-by-table distractors."""
    out = []
    for a in range(2, 13):
        for b in range(2, 13):
            if a > b:
                continue  # canonical order (covers commutative)
            product = a * b
            dist = [
                product - a,   # one row down in the b-table
                product + a,   # one row up
                product - b,   # one column over
            ]
            out.append(make_question(
                tier=1,
                topic_cell="basic_arithmetic",
                strategy="times_table_anchor",
                pillar="computation",
                question=f"{a} × {b} = ?",
                answer=product,
                distractors=dist,
                context=f"{a} × {b} = {product}. Memorizing the tables is the foundation.",
            ))
    return out


# ----- multiply_by_5 (T2) -----
# Halve and ×10: 28×5 = 14×10 = 140
def generate_multiply_by_5() -> list[dict]:
    """T2: ×5 via halve-and-times-ten. Use even multipliers for clean halves."""
    out = []
    evens = [12, 14, 16, 18, 22, 24, 26, 28, 32, 34, 36, 38, 42, 44, 46, 48, 52, 54, 56, 58, 64, 68, 72, 76, 82, 84, 86, 92, 94, 96]
    for n in evens:
        product = n * 5
        half = n // 2
        dist = [
            half,                # halved without ×10
            n * 10,              # ×10 without halving
            product - 10,        # off-by-ten
        ]
        out.append(make_question(
            tier=2,
            topic_cell="basic_arithmetic",
            strategy="multiply_by_5",
            pillar="computation",
            question=f"{n} × 5 = ?",
            answer=product,
            distractors=dist,
            context=f"Halve and times ten: {n}÷2 = {half}, then ×10 = {product}.",
        ))
    return out


# ----- multiply_by_9 (T1-T2) -----
# ×10 minus ×1: 9×7 = 70−7 = 63
def generate_multiply_by_9() -> list[dict]:
    """T1: 9 × 1..12 via ×10−×1 strategy."""
    out = []
    for n in range(2, 13):
        product = 9 * n
        dist = [
            10 * n,          # forgot to subtract
            product - n,     # subtracted twice
            product + 1,
        ]
        out.append(make_question(
            tier=1,
            topic_cell="basic_arithmetic",
            strategy="multiply_by_9",
            pillar="computation",
            question=f"9 × {n} = ?",
            answer=product,
            distractors=dist,
            context=f"×10 then subtract: 10×{n} = {10*n}, minus {n} → {product}. Digits of {product} also sum to 9.",
        ))
    return out


# ----- multiply_by_11_single (T1-T2) -----
def generate_multiply_by_11_single() -> list[dict]:
    """T1: 11 × 1..9, the digit-repeat pattern."""
    out = []
    for n in range(2, 10):
        product = 11 * n
        dist = [
            product - 1,
            product + 1,
            int(str(n) * 3) if n > 0 else 111,  # 3-digit repeat (×111)
        ]
        out.append(make_question(
            tier=1,
            topic_cell="basic_arithmetic",
            strategy="multiply_by_11_single",
            pillar="computation",
            question=f"11 × {n} = ?",
            answer=product,
            distractors=dist,
            context=f"Single-digit × 11: just repeat the digit → {product}.",
        ))
    return out


# ----- multiply_by_11_double (T2) -----
# Outside digits + inside sum: 11 × 34 = 3 (3+4) 4 = 374
def generate_multiply_by_11_double() -> list[dict]:
    """T2: 11 × NN where digits sum < 10 (no carry — clean pattern)."""
    out = []
    for ab in range(12, 100):
        a, b = ab // 10, ab % 10
        if a + b >= 10:
            continue  # skip carry cases
        product = 11 * ab
        # right form: a (a+b) b
        dist = [
            int(f"{a}{a+b+1}{b}") if a + b + 1 < 10 else product + 100,  # carry-error
            int(f"{a}{a}{b}"),     # forgot to add inside
            product + 11,
        ]
        out.append(make_question(
            tier=2,
            topic_cell="basic_arithmetic",
            strategy="multiply_by_11_double",
            pillar="computation",
            question=f"11 × {ab} = ?",
            answer=product,
            distractors=dist,
            context=f"Outer digits {a} and {b}; middle is their sum {a+b} → {product}.",
        ))
    return out


# ----- halve_then_double (T2) -----
# 14×5 = 7×10, 18×5 = 9×10, 12×15 = 6×30
def generate_halve_then_double() -> list[dict]:
    """T2: even × odd-or-5 problems where halve-then-double simplifies."""
    out = []
    pairs = [
        (14, 5), (18, 5), (16, 5), (24, 5), (28, 5), (32, 5),
        (12, 15), (16, 15), (18, 15), (24, 15),
        (12, 25), (16, 25), (18, 25), (24, 25),
        (14, 50), (18, 50), (22, 50), (26, 50),
    ]
    for a, b in pairs:
        product = a * b
        dist = [
            product // 2,
            product * 2,
            (a // 2) * b,
        ]
        out.append(make_question(
            tier=2,
            topic_cell="basic_arithmetic",
            strategy="halve_then_double",
            pillar="computation",
            question=f"{a} × {b} = ?",
            answer=product,
            distractors=dist,
            context=f"Halve {a} and double {b}: {a//2} × {b*2} = {product}.",
        ))
    return out


# ----- multiply_by_powers_of_10 (T1) -----
def generate_multiply_by_powers_of_10() -> list[dict]:
    """T1: shift decimal / append zeros."""
    out = []
    for n in [7, 12, 23, 47, 68, 84, 95]:
        for k in (10, 100, 1000):
            product = n * k
            dist = [
                product * 10,
                product // 10,
                n + len(str(k)) - 1,   # added zeros instead of multiplying
            ]
            out.append(make_question(
                tier=1,
                topic_cell="basic_arithmetic",
                strategy="multiply_by_powers_of_10",
                pillar="computation",
                question=f"{n} × {k} = ?",
                answer=product,
                distractors=dist,
                context=f"Multiplying by {k} = append {len(str(k))-1} zero{'s' if k > 10 else ''} → {product}.",
            ))
    return out


# ----- double_double_double (T2) -----
# ×8 via three doublings: 13×8 = 13→26→52→104
def generate_double_double_double() -> list[dict]:
    """T2: ×8 questions where chained doubling is clean."""
    out = []
    for n in range(7, 30):
        product = n * 8
        dist = [
            n * 4,           # stopped at two doublings
            n * 16,          # one too many doublings
            product - 8,
        ]
        out.append(make_question(
            tier=2,
            topic_cell="basic_arithmetic",
            strategy="double_double_double",
            pillar="computation",
            question=f"{n} × 8 = ?",
            answer=product,
            distractors=dist,
            context=f"Double three times: {n} → {n*2} → {n*4} → {product}.",
        ))
    return out


# ----- public API -----
def generate_all_multiplicative() -> list[dict]:
    out = []
    out.extend(generate_times_tables())
    out.extend(generate_multiply_by_5())
    out.extend(generate_multiply_by_9())
    out.extend(generate_multiply_by_11_single())
    out.extend(generate_multiply_by_11_double())
    out.extend(generate_halve_then_double())
    out.extend(generate_multiply_by_powers_of_10())
    out.extend(generate_double_double_double())
    return out


if __name__ == "__main__":
    qs = generate_all_multiplicative()
    print(f"Generated {len(qs)} multiplicative questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
