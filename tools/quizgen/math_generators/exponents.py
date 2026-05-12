"""Exponent and root strategies: perfect squares/cubes,
exponent rules (product/quotient/power), perfect square roots.
"""
from __future__ import annotations

from tools.quizgen.math_generators.common import make_question


def generate_square_perfect_recall() -> list[dict]:
    """T2: 1² .. 20² recall."""
    out = []
    for n in range(2, 21):
        sq = n * n
        dist = [sq + n, sq - n, sq + 1]
        out.append(make_question(
            tier=2, topic_cell="exponents_and_roots",
            strategy="square_perfect_recall", pillar="computation",
            question=f"{n}² = ?",
            answer=sq, distractors=dist,
            context=f"{n} × {n} = {sq}. Memorize 1²–20².",
        ))
    return out


def generate_cube_small_recall() -> list[dict]:
    """T3: 2³ .. 6³ recall."""
    out = []
    for n in range(2, 8):
        cube = n ** 3
        dist = [n * n, n * 3, cube + n]
        out.append(make_question(
            tier=3, topic_cell="exponents_and_roots",
            strategy="cube_small_recall", pillar="computation",
            question=f"{n}³ = ?",
            answer=cube, distractors=dist,
            context=f"{n} × {n} × {n} = {cube}. Memorize 1³–6³.",
        ))
    return out


def generate_exponent_product_rule() -> list[dict]:
    """T3: aᵐ · aⁿ = aᵐ⁺ⁿ in symbolic form."""
    out = []
    bases = [2, 3, 5, 10]
    for base in bases:
        for m in range(1, 6):
            for n in range(1, 6):
                if m == n == 1:
                    continue
                ans = f"{base}^{m + n}"
                dist = [
                    f"{base}^{m * n}",       # multiplied exponents
                    f"{base ** 2}^{m + n}",  # squared the base
                    f"{base}^{m - n}",
                ]
                out.append(make_question(
                    tier=3, topic_cell="exponents_and_roots",
                    strategy="exponent_product_rule", pillar="computation",
                    question=f"Simplify: {base}^{m} · {base}^{n}",
                    answer=ans, distractors=dist,
                    context=f"Same base, add exponents: {m}+{n} = {m+n} → {ans}.",
                ))
                if len(out) >= 30:
                    return out
    return out


def generate_exponent_quotient_rule() -> list[dict]:
    """T3: aᵐ / aⁿ = aᵐ⁻ⁿ."""
    out = []
    bases = [2, 3, 5, 10]
    for base in bases:
        for m in range(3, 8):
            for n in range(1, m):
                ans = f"{base}^{m - n}"
                dist = [
                    f"{base}^{m + n}",
                    f"{base}^{m * n}",
                    f"1^{m - n}",
                ]
                out.append(make_question(
                    tier=3, topic_cell="exponents_and_roots",
                    strategy="exponent_quotient_rule", pillar="computation",
                    question=f"Simplify: {base}^{m} / {base}^{n}",
                    answer=ans, distractors=dist,
                    context=f"Same base, subtract exponents: {m}−{n} = {m-n} → {ans}.",
                ))
                if len(out) >= 25:
                    return out
    return out


def generate_exponent_power_rule() -> list[dict]:
    """T4: (aᵐ)ⁿ = aᵐⁿ."""
    out = []
    for base in (2, 3, 5):
        for m in range(2, 6):
            for n in range(2, 5):
                ans = f"{base}^{m * n}"
                dist = [
                    f"{base}^{m + n}",
                    f"{base}^{m ** n}",
                    f"{base ** n}^{m}",
                ]
                out.append(make_question(
                    tier=4, topic_cell="exponents_and_roots",
                    strategy="exponent_power_rule", pillar="computation",
                    question=f"Simplify: ({base}^{m})^{n}",
                    answer=ans, distractors=dist,
                    context=f"Power of a power: multiply exponents → {ans}.",
                ))
                if len(out) >= 20:
                    return out
    return out


def generate_root_perfect_square() -> list[dict]:
    """T2: √(perfect square)."""
    out = []
    for n in range(2, 16):
        sq = n * n
        dist = [n + 1, n - 1, n * 2]
        out.append(make_question(
            tier=2, topic_cell="exponents_and_roots",
            strategy="root_perfect_square", pillar="computation",
            question=f"√{sq} = ?",
            answer=n, distractors=dist,
            context=f"√{sq} = {n} because {n}² = {sq}.",
        ))
    return out


def generate_all_exponents() -> list[dict]:
    out = []
    out.extend(generate_square_perfect_recall())
    out.extend(generate_cube_small_recall())
    out.extend(generate_exponent_product_rule())
    out.extend(generate_exponent_quotient_rule())
    out.extend(generate_exponent_power_rule())
    out.extend(generate_root_perfect_square())
    return out


if __name__ == "__main__":
    qs = generate_all_exponents()
    print(f"Generated {len(qs)} exponent questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
