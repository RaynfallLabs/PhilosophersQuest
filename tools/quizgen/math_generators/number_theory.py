"""Number-theory strategies: divisibility rules, prime check, GCD/LCM,
prime factorization.
"""
from __future__ import annotations

from math import gcd

from tools.quizgen.math_generators.common import make_question


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def _lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


def generate_divisibility_3() -> list[dict]:
    """T2: rule of 3 — digit sum divisible by 3."""
    out = []
    cases = [(123, True), (124, False), (471, True), (382, False), (567, True),
             (244, False), (909, True), (515, False), (846, True), (137, False),
             (351, True), (203, False), (729, True), (608, False), (444, True),
             (505, False), (612, True), (175, False), (936, True), (217, False)]
    for n, divis in cases:
        ans = "Yes" if divis else "No"
        digit_sum = sum(int(d) for d in str(n))
        dist = ["No" if divis else "Yes", "Only if even", "Only if odd"]
        out.append(make_question(
            tier=2, topic_cell="number_theory",
            strategy="divisibility_3", pillar="computation",
            question=f"Is {n} divisible by 3?",
            answer=ans, distractors=dist,
            context=f"Digit sum: {digit_sum}. Divisible by 3 → {ans}.",
        ))
    return out


def generate_divisibility_9() -> list[dict]:
    """T2: rule of 9 — digit sum divisible by 9."""
    out = []
    cases = [(729, True), (135, False), (567, True), (181, False), (819, True),
             (272, False), (936, True), (415, False), (108, True), (245, False),
             (459, True), (623, False), (873, True), (351, True), (725, False)]
    for n, divis in cases:
        ans = "Yes" if divis else "No"
        digit_sum = sum(int(d) for d in str(n))
        dist = ["No" if divis else "Yes", "Only if even", "Only if it ends in 9"]
        out.append(make_question(
            tier=2, topic_cell="number_theory",
            strategy="divisibility_9", pillar="computation",
            question=f"Is {n} divisible by 9?",
            answer=ans, distractors=dist,
            context=f"Digit sum: {digit_sum}. Divisible by 9 → {ans}.",
        ))
    return out


def generate_prime_check() -> list[dict]:
    """T1: small prime checks. T2: medium (up to 100)."""
    out = []
    for n in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
              4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25,
              26, 27, 28, 33, 35, 39, 49, 51, 53, 57, 59, 61, 63, 67,
              71, 77, 81, 83, 87, 91, 93, 97]:
        is_prime = _is_prime(n)
        ans = "Yes" if is_prime else "No"
        dist = ["No" if is_prime else "Yes", "Only if odd", "Only if greater than 10"]
        tier = 1 if n <= 30 else 2
        out.append(make_question(
            tier=tier, topic_cell="number_theory",
            strategy="prime_check_small", pillar="computation",
            question=f"Is {n} prime?",
            answer=ans, distractors=dist,
            context=f"{n} is {'prime' if is_prime else 'composite'} ({'no factors except 1 and itself' if is_prime else 'has a divisor'}).",
        ))
    return out


def generate_gcd() -> list[dict]:
    """T2-T3: GCD by factor pairs."""
    out = []
    pairs = [(12, 18), (15, 25), (8, 12), (14, 21), (16, 24), (20, 30),
             (24, 36), (18, 24), (27, 36), (28, 42), (30, 45), (32, 48),
             (35, 49), (40, 60), (45, 75), (12, 30), (18, 27), (24, 32),
             (36, 54), (50, 75), (48, 72), (60, 90), (14, 35), (9, 15)]
    for a, b in pairs:
        g = gcd(a, b)
        dist = [_lcm(a, b), a + b, a - b]
        out.append(make_question(
            tier=3, topic_cell="number_theory",
            strategy="gcd_by_factor_pairs", pillar="computation",
            question=f"gcd({a}, {b}) = ?",
            answer=g, distractors=dist,
            context=f"GCD = largest number dividing both. → {g}.",
        ))
    return out


def generate_lcm() -> list[dict]:
    """T2-T3: LCM by multiples."""
    out = []
    pairs = [(4, 6), (6, 8), (3, 5), (4, 9), (5, 6), (6, 9), (8, 12),
             (3, 7), (4, 10), (5, 15), (6, 10), (12, 18), (7, 14),
             (8, 10), (9, 12), (4, 14), (6, 15), (3, 11), (5, 12),
             (4, 16), (10, 15), (8, 14), (6, 21), (9, 15)]
    for a, b in pairs:
        l = _lcm(a, b)
        dist = [gcd(a, b), a * b, a + b]
        out.append(make_question(
            tier=3, topic_cell="number_theory",
            strategy="lcm_by_multiples", pillar="computation",
            question=f"lcm({a}, {b}) = ?",
            answer=l, distractors=dist,
            context=f"LCM = smallest number that both divide. → {l}.",
        ))
    return out


def generate_all_number_theory() -> list[dict]:
    out = []
    out.extend(generate_divisibility_3())
    out.extend(generate_divisibility_9())
    out.extend(generate_prime_check())
    out.extend(generate_gcd())
    out.extend(generate_lcm())
    return out


if __name__ == "__main__":
    qs = generate_all_number_theory()
    print(f"Generated {len(qs)} number_theory questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
