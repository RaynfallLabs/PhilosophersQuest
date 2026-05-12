"""Percentage strategies: 10%-anchor (move decimal), easy anchors
(25/50/75%), percent-flip (a% of b = b% of a), ratio scaling.
"""
from __future__ import annotations

from tools.quizgen.math_generators.common import make_question


def generate_percent_10_anchor() -> list[dict]:
    """T2: 10% via move-the-decimal."""
    out = []
    for base in [30, 50, 80, 120, 250, 350, 500, 720, 850, 1000, 1500, 60, 90,
                 140, 180, 200, 320, 480, 640, 800, 240, 400, 600, 950]:
        ans = base // 10
        dist = [base, ans * 10, ans // 10 if ans >= 10 else ans + 5]
        out.append(make_question(
            tier=2, topic_cell="percentages_and_ratios",
            strategy="percent_10_anchor", pillar="computation",
            question=f"10% of {base} = ?",
            answer=ans, distractors=dist,
            context=f"10% = move the decimal one place left → {ans}.",
        ))
    return out


def generate_percent_easy_anchors() -> list[dict]:
    """T2: 25/50/75% via halve/halve-again."""
    out = []
    bases = [16, 24, 32, 40, 48, 60, 80, 100, 120, 160, 200, 240, 400, 800]
    for base in bases:
        if base % 4 == 0:
            for pct in (25, 50, 75):
                ans = base * pct // 100
                dist = [base // 4 if pct != 25 else base // 2, ans + base // 4, ans - base // 4]
                out.append(make_question(
                    tier=2, topic_cell="percentages_and_ratios",
                    strategy="percent_easy_anchors", pillar="computation",
                    question=f"{pct}% of {base} = ?",
                    answer=ans, distractors=dist,
                    context=f"{pct}% = " + ("quarter" if pct == 25 else "half" if pct == 50 else "three quarters") + f" → {ans}.",
                ))
    return out


def generate_percent_flip() -> list[dict]:
    """T2: a% of b = b% of a. Pick pairs where the flipped form is obvious."""
    out = []
    pairs = [
        (8, 50), (12, 50), (16, 50), (24, 50), (4, 25), (12, 25),
        (8, 25), (16, 75), (4, 75), (50, 80), (20, 40), (40, 60),
        (4, 50), (8, 100), (3, 200), (5, 60), (2, 150), (6, 50),
    ]
    for a, b in pairs:
        ans = a * b // 100
        dist = [ans * 10, ans + 5, ans - 1]
        out.append(make_question(
            tier=2, topic_cell="percentages_and_ratios",
            strategy="percent_flip", pillar="computation",
            question=f"{a}% of {b} = ?",
            answer=ans, distractors=dist,
            context=f"Flip it: {b}% of {a} = {ans}. Often easier.",
        ))
    return out


def generate_ratio_scaling() -> list[dict]:
    """T2-T3: scale a ratio by a common multiplier."""
    out = []
    triples = [(3, 4, 9), (2, 5, 8), (3, 5, 12), (4, 7, 12), (2, 3, 10),
               (5, 8, 15), (3, 7, 9), (4, 9, 16), (5, 6, 20), (7, 10, 14),
               (2, 9, 8), (3, 8, 15), (6, 7, 24), (5, 11, 20), (4, 5, 16),
               (3, 4, 12), (2, 5, 14), (3, 5, 18)]
    for a, b, scaled_a in triples:
        if scaled_a % a != 0:
            continue
        mult = scaled_a // a
        ans = b * mult
        dist = [ans + b, ans - b, b * (mult + 1)]
        out.append(make_question(
            tier=3, topic_cell="percentages_and_ratios",
            strategy="ratio_scaling", pillar="computation",
            question=f"If {a}:{b}, then {scaled_a}:?",
            answer=ans, distractors=dist,
            context=f"Multiplier = {mult}. So {b}×{mult} = {ans}.",
        ))
    return out


def generate_all_percentages() -> list[dict]:
    out = []
    out.extend(generate_percent_10_anchor())
    out.extend(generate_percent_easy_anchors())
    out.extend(generate_percent_flip())
    out.extend(generate_ratio_scaling())
    return out


if __name__ == "__main__":
    qs = generate_all_percentages()
    print(f"Generated {len(qs)} percentage questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
