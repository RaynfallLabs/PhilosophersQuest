"""Number-sense strategies: doubling/halving chains, rounding,
magnitude comparison, negative comparison.

T1 strategies anchored to docs/quiz/math_strategies.md Pillar 1 § Number sense.
"""
from __future__ import annotations

from tools.quizgen.math_generators.common import make_question


def generate_doubling_chain() -> list[dict]:
    """T1: 'Double X is?' for clean doubles up to ~100."""
    out = []
    for n in [3, 4, 6, 7, 8, 9, 12, 15, 18, 22, 25, 28, 32, 35, 40, 45]:
        doubled = n * 2
        dist = [doubled + 1, doubled - 1, n + 2]
        out.append(make_question(
            tier=1, topic_cell="number_sense", strategy="doubling_chain", pillar="computation",
            question=f"Double {n} is?", answer=doubled, distractors=dist,
            context=f"Double {n} = {n} + {n} = {doubled}.",
        ))
    return out


def generate_halving_chain() -> list[dict]:
    """T1: 'Half of X is?' for even numbers."""
    out = []
    for n in [4, 6, 8, 12, 14, 16, 18, 20, 24, 28, 30, 36, 40, 48, 50, 60, 72, 80, 100]:
        halved = n // 2
        dist = [halved + 1, halved - 1, n - 1]
        out.append(make_question(
            tier=1, topic_cell="number_sense", strategy="halving_chain", pillar="computation",
            question=f"Half of {n} is?", answer=halved, distractors=dist,
            context=f"Half of {n} = {halved}. Halving is the inverse of doubling.",
        ))
    return out


def generate_round_to_anchor() -> list[dict]:
    """T1-T2: Round to nearest 10, 100."""
    out = []
    # nearest 10
    for n in [23, 27, 34, 38, 42, 47, 51, 56, 63, 68, 74, 79, 85, 91, 96]:
        rounded = round(n / 10) * 10
        dist = [rounded + 10, rounded - 10, n]
        out.append(make_question(
            tier=1, topic_cell="number_sense", strategy="round_to_anchor", pillar="computation",
            question=f"Round {n} to the nearest ten.", answer=rounded, distractors=dist,
            context=f"{n%10} ≥ 5 means round up; else down. → {rounded}.",
        ))
    # nearest 100
    for n in [127, 234, 358, 471, 583, 649, 712, 836, 945, 487, 521, 168, 793, 264]:
        rounded = round(n / 100) * 100
        dist = [rounded + 100, rounded - 100, (n // 10) * 10]
        out.append(make_question(
            tier=2, topic_cell="number_sense", strategy="round_to_anchor", pillar="computation",
            question=f"Round {n} to the nearest hundred.", answer=rounded, distractors=dist,
            context=f"Look at the tens digit ({(n//10)%10}). Round to {rounded}.",
        ))
    return out


def generate_magnitude_comparison() -> list[dict]:
    """T1: which decimal/integer is larger?"""
    out = []
    decimals = [
        ("0.7", "0.65"),  ("0.30", "0.3"), ("0.45", "0.5"), ("0.09", "0.1"),
        ("0.25", "0.2"),  ("0.8", "0.75"), ("0.4", "0.41"), ("0.06", "0.6"),
        ("1.05", "1.5"),  ("2.30", "2.3"), ("0.99", "1.0"), ("0.55", "0.5"),
    ]
    for a, b in decimals:
        af, bf = float(a), float(b)
        if af == bf:
            answer = "They are equal"
            dist = [a, b, "Cannot tell"]
            out.append(make_question(
                tier=1, topic_cell="number_sense", strategy="magnitude_comparison", pillar="computation",
                question=f"Which is larger: {a} or {b}?", answer=answer, distractors=dist,
                context=f"{a} and {b} represent the same value.",
            ))
        else:
            answer = a if af > bf else b
            other = b if answer == a else a
            dist = [other, "They are equal", "Cannot tell"]
            out.append(make_question(
                tier=1, topic_cell="number_sense", strategy="magnitude_comparison", pillar="computation",
                question=f"Which is larger: {a} or {b}?", answer=answer, distractors=dist,
                context=f"Compare digit by digit after the decimal: {answer} is larger.",
            ))
    return out


def generate_negative_compare() -> list[dict]:
    """T2: compare negative numbers — the LESS-negative is the larger."""
    out = []
    pairs = [(-8, -3), (-5, -2), (-12, -7), (-15, -4), (-9, -1), (-20, -11),
             (-6, -10), (-3, -3), (-7, -14), (-2, -8), (-25, -13), (-18, -6)]
    for a, b in pairs:
        if a == b:
            answer = "They are equal"
            dist = [str(a), str(b), "Cannot tell"]
        else:
            larger = max(a, b)
            answer = str(larger)
            other = str(min(a, b))
            dist = [other, "They are equal", "Cannot tell"]
        out.append(make_question(
            tier=2, topic_cell="number_sense", strategy="negative_compare", pillar="computation",
            question=f"Which is larger: {a} or {b}?", answer=answer, distractors=dist,
            context=f"On a number line, the less-negative is larger. → {answer}",
        ))
    return out


def generate_all_number_sense() -> list[dict]:
    out = []
    out.extend(generate_doubling_chain())
    out.extend(generate_halving_chain())
    out.extend(generate_round_to_anchor())
    out.extend(generate_magnitude_comparison())
    out.extend(generate_negative_compare())
    return out


if __name__ == "__main__":
    qs = generate_all_number_sense()
    print(f"Generated {len(qs)} number_sense questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
