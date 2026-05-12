"""Fraction & decimal strategies: common-denominator addition,
simplification, decimal alignment, fraction-to-decimal conversion.
"""
from __future__ import annotations

from fractions import Fraction

from tools.quizgen.math_generators.common import make_question


def generate_fraction_common_denom() -> list[dict]:
    """T2: a/b + c/d via least common denominator."""
    out = []
    pairs = [
        ("1/2", "1/3"), ("1/2", "1/4"), ("1/3", "1/4"), ("1/2", "1/6"),
        ("1/3", "1/6"), ("2/3", "1/6"), ("3/4", "1/8"), ("1/4", "3/8"),
        ("1/5", "2/5"), ("2/5", "1/10"), ("1/2", "1/5"), ("1/3", "2/5"),
        ("1/4", "1/6"), ("3/8", "1/4"), ("5/6", "1/4"), ("1/2", "3/8"),
        ("2/3", "1/4"), ("1/2", "2/3"), ("3/4", "1/3"), ("5/8", "1/4"),
        ("1/6", "1/8"), ("2/3", "3/4"), ("1/5", "1/3"), ("3/5", "1/4"),
    ]
    for a_s, b_s in pairs:
        a = Fraction(a_s)
        b = Fraction(b_s)
        total = a + b
        # answer in canonical form: numerator/denominator (handle integer results)
        ans = str(total.numerator) if total.denominator == 1 else f"{total.numerator}/{total.denominator}"
        # distractor: added numerator AND denominator separately (classic error)
        bad_num = a.numerator + b.numerator
        bad_den = a.denominator + b.denominator
        bad = f"{bad_num}/{bad_den}"
        # distractor: kept denominators, added numerators (wrong-common-denom error)
        bad2_den = max(a.denominator, b.denominator)
        bad2 = f"{a.numerator + b.numerator}/{bad2_den}"
        # distractor: multiplied numerators and denominators
        bad3 = f"{a.numerator * b.numerator}/{a.denominator * b.denominator}"
        out.append(make_question(
            tier=2, topic_cell="fractions_and_decimals",
            strategy="fraction_common_denom", pillar="computation",
            question=f"{a_s} + {b_s} = ?",
            answer=ans, distractors=[bad, bad2, bad3],
            context=f"Common denominator = {total.denominator}. Convert and add → {ans}.",
        ))
    return out


def generate_fraction_simplify() -> list[dict]:
    """T2: simplify a fraction to lowest terms."""
    out = []
    pairs = [
        "2/4", "3/6", "4/8", "6/8", "4/6", "6/9", "8/12", "9/12", "10/15",
        "4/10", "6/10", "8/10", "5/15", "6/15", "12/16", "10/12",
        "15/20", "12/18", "16/20", "9/15", "8/14", "12/15", "14/21",
        "20/24", "15/25", "18/24", "20/30",
    ]
    for f_s in pairs:
        f = Fraction(f_s)
        ans = str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        # original form (didn't simplify)
        orig_n, orig_d = (int(x) for x in f_s.split("/"))
        # distractors: wrong simplifications
        dist = []
        if orig_n // 2 > 0 and orig_d // 2 > 0 and (orig_n // 2, orig_d // 2) != (f.numerator, f.denominator):
            dist.append(f"{orig_n // 2}/{orig_d // 2}")
        # subtracted same number from both (wrong)
        dist.append(f"{orig_n - 1}/{orig_d - 1}")
        # only simplified numerator
        if orig_n // 2 > 0:
            dist.append(f"{orig_n // 2}/{orig_d}")
        # always include the unsimplified original
        dist.append(f_s)
        out.append(make_question(
            tier=2, topic_cell="fractions_and_decimals",
            strategy="fraction_simplify", pillar="computation",
            question=f"Simplify {f_s} to lowest terms.",
            answer=ans, distractors=dist,
            context=f"Divide num and den by GCD = {orig_n // f.numerator if f.numerator else 1} → {ans}.",
        ))
    return out


def generate_decimal_align() -> list[dict]:
    """T2: decimal addition where alignment matters."""
    out = []
    pairs = [
        (0.7, 0.25), (0.5, 0.45), (0.3, 0.25), (1.2, 0.3), (0.8, 0.15),
        (2.4, 0.6), (3.5, 0.5), (0.6, 0.04), (1.5, 0.75), (2.7, 0.3),
        (0.45, 0.55), (0.9, 0.1), (1.25, 0.5), (2.5, 1.5), (0.85, 0.15),
    ]
    for a, b in pairs:
        total = round(a + b, 4)
        ans = f"{total:g}"  # strip trailing zeros
        dist = [
            f"{a + b/10:g}",     # misaligned (treated b as 1/10th)
            f"{round(total + 0.1, 4):g}",
            f"{round(total - 0.1, 4):g}",
        ]
        out.append(make_question(
            tier=2, topic_cell="fractions_and_decimals",
            strategy="decimal_align", pillar="computation",
            question=f"{a:g} + {b:g} = ?",
            answer=ans, distractors=dist,
            context=f"Line up the decimal point before adding: {a:g} + {b:g} = {ans}.",
        ))
    return out


def generate_fraction_to_decimal() -> list[dict]:
    """T2: convert simple fractions to decimals."""
    out = []
    # canonical conversions worth memorizing
    table = {
        "1/2": "0.5", "1/4": "0.25", "3/4": "0.75",
        "1/5": "0.2", "2/5": "0.4", "3/5": "0.6", "4/5": "0.8",
        "1/8": "0.125", "3/8": "0.375", "5/8": "0.625", "7/8": "0.875",
        "1/10": "0.1", "3/10": "0.3", "7/10": "0.7", "9/10": "0.9",
        "1/3": "0.333...", "2/3": "0.667...",
    }
    for f, d in table.items():
        # plausible wrong-decimal distractors
        n, den = (int(x) for x in f.split("/"))
        dist = [f"{round(den/n, 3):g}" if n else "0", f"{n/10:g}", f"0.{n}{den}"]
        out.append(make_question(
            tier=2, topic_cell="fractions_and_decimals",
            strategy="fraction_to_decimal", pillar="computation",
            question=f"{f} as a decimal:",
            answer=d, distractors=dist,
            context=f"{f} = {d}. Memorize the common ones.",
        ))
    return out


def generate_all_fractions_decimals() -> list[dict]:
    out = []
    out.extend(generate_fraction_common_denom())
    out.extend(generate_fraction_simplify())
    out.extend(generate_decimal_align())
    out.extend(generate_fraction_to_decimal())
    return out


if __name__ == "__main__":
    qs = generate_all_fractions_decimals()
    print(f"Generated {len(qs)} fraction/decimal questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
