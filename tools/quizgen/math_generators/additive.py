"""Additive computation strategies: make-ten, near-doubles, compensate,
split, subtract-by-add-up, compensate-subtraction.

Each function returns a list of question dicts. Strategies anchored to
docs/quiz/math_strategies.md Pillar 1 § Additive.
"""
from __future__ import annotations

from tools.quizgen.math_generators.common import make_question


# ----- make_ten_addition (T1) -----
# Bridge to 10: 8+5 = 8+2+3 = 10+3
def generate_make_ten_addition() -> list[dict]:
    """T1: pairs where bridging through 10 is the natural mental move.

    Coverage: a in 4..9, b in (10-a)+1..9, total in 11..18.
    """
    out = []
    for a in range(4, 10):
        for b in range(11 - a, 10):
            if a + b < 11:
                continue
            total = a + b
            # distractors as common errors
            dist = [
                total - 1,     # off-by-one (stopped one short)
                total + 1,     # off-by-one (one too many)
                10 + (a - (10 - b)),  # stopped at make-ten step (often = total - 1)
            ]
            # ensure dedup is handled by make_question
            q = make_question(
                tier=1,
                topic_cell="basic_arithmetic",
                strategy="make_ten_addition",
                pillar="computation",
                question=f"{a} + {b} = ?",
                answer=total,
                distractors=dist,
                context=f"Bridge to 10: {a} + ({10 - a}) = 10, then add {b - (10 - a)} more → {total}.",
            )
            out.append(q)
    return out


# ----- near_doubles (T1) -----
# 7+8 = 7+7+1 = 14+1
def generate_near_doubles() -> list[dict]:
    """T1: a+(a+1) or a+(a-1). Use known double + 1."""
    out = []
    for a in range(2, 10):
        b = a + 1
        total = a + b
        dist = [
            2 * a,       # didn't add the +1
            2 * b,       # used the wrong double
            total + 1,   # off-by-one
        ]
        out.append(make_question(
            tier=1,
            topic_cell="basic_arithmetic",
            strategy="near_doubles",
            pillar="computation",
            question=f"{a} + {b} = ?",
            answer=total,
            distractors=dist,
            context=f"Use the double you know: {a} + {a} = {2*a}, then add 1 → {total}.",
        ))
    return out


# ----- compensate_addition (T2) -----
# Round one term up, adjust at the end: 29+47 = 30+47−1
def generate_compensate_addition() -> list[dict]:
    """T2: 2-digit additions where one operand is close to a round 10."""
    out = []
    # operand a near a round 10 (off by 1, 2)
    bases = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    for base in bases:
        for off in (-2, -1, 1, 2):
            a = base + off
            if a <= 0 or a > 99:
                continue
            for b in (17, 23, 36, 38, 44, 47, 52, 58, 63, 67):
                if a + b > 100:
                    continue
                total = a + b
                # round-and-adjust distractors
                dist = [
                    total + off,   # forgot to adjust (used base + b)
                    total - off,   # adjusted wrong direction
                    total + 1,     # off-by-one
                ]
                out.append(make_question(
                    tier=2,
                    topic_cell="basic_arithmetic",
                    strategy="compensate_addition",
                    pillar="computation",
                    question=f"{a} + {b} = ?",
                    answer=total,
                    distractors=dist,
                    context=(
                        f"Round {a} to {base}: {base} + {b} = {base + b}. "
                        f"{'Now subtract' if off > 0 else 'Now add'} {abs(off)} → {total}."
                    ),
                ))
                if len(out) >= 60:
                    return out
    return out


# ----- split_addition (T2) -----
# Place-value split: 47+38 = (40+30)+(7+8) = 70+15 = 85
def generate_split_addition() -> list[dict]:
    """T2: 2-digit + 2-digit where the place-value split is the strategy."""
    out = []
    pairs = [
        (47, 38), (53, 29), (64, 27), (35, 28), (46, 35), (58, 26),
        (37, 45), (49, 24), (56, 37), (63, 28), (74, 19), (28, 47),
        (39, 33), (52, 39), (66, 25), (43, 29), (57, 36), (61, 28),
        (45, 47), (38, 56), (29, 44), (48, 33), (54, 27), (32, 49),
        (67, 25), (41, 38), (59, 33), (62, 29), (44, 47), (36, 58),
    ]
    for a, b in pairs:
        total = a + b
        tens = (a // 10 + b // 10) * 10
        ones = (a % 10) + (b % 10)
        dist = [
            tens + (ones % 10),       # forgot to carry the tens from ones
            total + 10,               # carried an extra ten
            total - 10,               # missed a ten
        ]
        out.append(make_question(
            tier=2,
            topic_cell="basic_arithmetic",
            strategy="split_addition",
            pillar="computation",
            question=f"{a} + {b} = ?",
            answer=total,
            distractors=dist,
            context=(
                f"Split by place value: ({a//10*10}+{b//10*10}) + ({a%10}+{b%10}) "
                f"= {tens} + {ones} = {total}."
            ),
        ))
    return out


# ----- subtract_by_add_up (T2) -----
# 83 − 47: 47 to 50 is 3, 50 to 83 is 33 → 36
def generate_subtract_by_add_up() -> list[dict]:
    """T2: 2-digit subtractions where adding-up is the strategy."""
    out = []
    pairs = [
        (83, 47), (92, 58), (74, 28), (61, 23), (85, 37),
        (96, 49), (73, 28), (82, 35), (95, 47), (64, 25),
        (87, 39), (76, 28), (54, 26), (93, 47), (81, 33),
        (72, 35), (88, 49), (62, 27), (98, 49), (75, 38),
        (84, 46), (91, 53), (67, 29), (78, 39), (89, 42),
    ]
    for a, b in pairs:
        diff = a - b
        # distractors: subtracted the wrong way, carry error, off-by-one
        dist = [
            (b - a) if b > a else (a - b - 10),   # wrong direction or carry
            diff + 1,
            diff - 1,
        ]
        out.append(make_question(
            tier=2,
            topic_cell="basic_arithmetic",
            strategy="subtract_by_add_up",
            pillar="computation",
            question=f"{a} − {b} = ?",
            answer=diff,
            distractors=dist,
            context=(
                f"Count up from {b}: to the next 10 is {10 - b%10 if b%10 else 0}, "
                f"to {a} is {diff} total."
            ),
        ))
    return out


# ----- compensate_subtraction (T2) -----
# 83 − 39: round 39 to 40, subtract, then add back 1: 83−40+1 = 44
def generate_compensate_subtraction() -> list[dict]:
    """T2: subtraction where rounding the subtrahend simplifies."""
    out = []
    pairs = [
        (83, 39), (92, 29), (74, 38), (61, 49), (85, 19),
        (96, 39), (73, 48), (82, 29), (95, 49), (64, 38),
        (87, 19), (76, 49), (54, 29), (93, 38), (81, 19),
        (72, 49), (88, 39), (62, 19), (98, 29), (75, 48),
    ]
    for a, b in pairs:
        diff = a - b
        nearest_10 = round(b / 10) * 10
        off = b - nearest_10  # if b=39, nearest=40, off=-1, so subtract more then add back
        dist = [
            a - nearest_10,           # forgot to compensate
            a - nearest_10 - off,     # wrong-direction compensation
            diff + 1,
        ]
        out.append(make_question(
            tier=2,
            topic_cell="basic_arithmetic",
            strategy="compensate_subtraction",
            pillar="computation",
            question=f"{a} − {b} = ?",
            answer=diff,
            distractors=dist,
            context=(
                f"Round {b} to {nearest_10}: {a} − {nearest_10} = {a - nearest_10}. "
                f"{'Add back' if off < 0 else 'Subtract'} {abs(off)} → {diff}."
            ),
        ))
    return out


# ----- public API -----
def generate_all_additive() -> list[dict]:
    out = []
    out.extend(generate_make_ten_addition())
    out.extend(generate_near_doubles())
    out.extend(generate_compensate_addition())
    out.extend(generate_split_addition())
    out.extend(generate_subtract_by_add_up())
    out.extend(generate_compensate_subtraction())
    return out


if __name__ == "__main__":
    qs = generate_all_additive()
    print(f"Generated {len(qs)} additive questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
