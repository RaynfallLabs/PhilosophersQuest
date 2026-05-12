"""Algebra strategies: isolate-x (one and two step), balance both sides,
distribute, factor difference of squares, factor simple quadratics.
"""
from __future__ import annotations

from sympy import Symbol, expand, factor, solve

from tools.quizgen.math_generators.common import make_question


def generate_isolate_x_one_step() -> list[dict]:
    """T2: x + c = k, x - c = k, cx = k."""
    out = []
    # x + c = k
    for c in range(2, 13):
        for x_val in range(2, 20):
            k = x_val + c
            if x_val == c:  # avoid trivial
                continue
            dist = [k, k - c - 1, c - x_val]
            out.append(make_question(
                tier=2, topic_cell="algebra_basics",
                strategy="isolate_x_one_step", pillar="computation",
                question=f"x + {c} = {k}. x = ?",
                answer=x_val, distractors=dist,
                context=f"Subtract {c} from both sides: x = {k}−{c} = {x_val}.",
            ))
            if len(out) >= 30:
                break
        if len(out) >= 30:
            break
    # cx = k (clean integer solutions)
    for c in (2, 3, 4, 5, 6, 7, 8, 9, 10):
        for x_val in range(2, 12):
            k = c * x_val
            dist = [k, c + x_val, k - c]
            out.append(make_question(
                tier=2, topic_cell="algebra_basics",
                strategy="isolate_x_one_step", pillar="computation",
                question=f"{c}x = {k}. x = ?",
                answer=x_val, distractors=dist,
                context=f"Divide both sides by {c}: x = {k}÷{c} = {x_val}.",
            ))
            if len(out) >= 60:
                break
        if len(out) >= 60:
            break
    return out


def generate_isolate_x_two_step() -> list[dict]:
    """T3: cx + b = k."""
    out = []
    for c in (2, 3, 4, 5, 6, 7):
        for x_val in range(2, 10):
            for b in (1, 3, 5, 7, 11):
                k = c * x_val + b
                if k > 50:
                    continue
                dist = [k - b, (k - b) // c + 1, x_val + 1]
                out.append(make_question(
                    tier=3, topic_cell="algebra_basics",
                    strategy="isolate_x_two_step", pillar="computation",
                    question=f"Solve for x: {c}x + {b} = {k}",
                    answer=f"x = {x_val}", distractors=[f"x = {d}" for d in dist],
                    context=f"Subtract {b}: {c}x = {k - b}. Divide by {c}: x = {x_val}.",
                ))
                if len(out) >= 40:
                    return out
    return out


def generate_distribute() -> list[dict]:
    """T3: expand a(b+c)."""
    out = []
    x = Symbol("x")
    cases = [(3, x, 4), (5, x, 2), (4, x, 7), (6, x, 3), (2, x, 9), (7, x, 5),
             (8, x, 3), (9, x, 4), (3, x, -2), (5, x, -3), (4, x, -1), (10, x, 5),
             (2, x, 11), (6, x, 7), (4, x, 9), (5, x, 8), (3, x, 6), (7, x, 4)]
    for a, _, c in cases:
        expanded = expand(a * (x + c))
        ans = str(expanded).replace(" ", "").replace("*", "")
        # canonical form: "Nx+M" or "Nx-M"
        # distractors: forgot to distribute, doubled coefficient, distributed wrong
        if c >= 0:
            d1 = f"{a}x+{c}"        # only multiplied x term
            d2 = f"{a}x+{a + c}"    # added instead of multiplied for constant
            d3 = f"{a + c}x+{a*c}"  # swapped roles
        else:
            d1 = f"{a}x{c}"
            d2 = f"{a}x{a + c:+d}"
            d3 = f"{a + c}x{a*c:+d}"
        out.append(make_question(
            tier=3, topic_cell="algebra_basics",
            strategy="distribute", pillar="computation",
            question=f"Expand: {a}(x{'+' if c>=0 else ''}{c})",
            answer=ans, distractors=[d1, d2, d3],
            context=f"Distribute {a} to each term: {a}·x + {a}·({c}) = {ans}.",
        ))
    return out


def generate_factor_difference_squares() -> list[dict]:
    """T4: factor a² − b² = (a+b)(a−b)."""
    out = []
    cases = [(1, 9), (1, 25), (1, 16), (1, 49), (1, 81), (1, 100),
             (4, 9), (9, 16), (4, 25), (9, 25), (16, 25), (1, 36),
             (1, 64), (1, 121), (4, 49), (25, 36), (16, 81), (1, 144)]
    for a_sq, b_sq in cases:
        from math import isqrt
        a_v = isqrt(a_sq)
        b_v = isqrt(b_sq)
        if a_v * a_v != a_sq or b_v * b_v != b_sq:
            continue
        # build the question — "Factor: 4x² − 9"
        if a_v == 1:
            lhs = f"x² − {b_sq}"
        else:
            lhs = f"{a_sq}x² − {b_sq}"
        # canonical answer (right form): (ax+b)(ax−b)
        if a_v == 1:
            ans = f"(x+{b_v})(x−{b_v})"
        else:
            ans = f"({a_v}x+{b_v})({a_v}x−{b_v})"
        dist = [
            f"(x+{b_v})²",
            f"(x−{b_v})²",
            f"x² − {b_v}²" if a_v == 1 else f"{a_v}x² − {b_v}²",
        ]
        out.append(make_question(
            tier=4, topic_cell="algebra_advanced",
            strategy="factor_difference_squares", pillar="computation",
            question=f"Factor: {lhs}",
            answer=ans, distractors=dist,
            context=f"Difference of squares: a²−b² = (a+b)(a−b) → {ans}.",
        ))
    return out


def generate_factor_quadratic_simple() -> list[dict]:
    """T4: solve x² + bx + c = 0 by factoring."""
    out = []
    # generate (r1, r2) pairs; quadratic = x² - (r1+r2)x + r1*r2
    root_pairs = [(2, 3), (1, 4), (1, 5), (1, 6), (2, 5), (3, 4), (1, 7),
                  (2, 7), (3, 5), (4, 5), (1, 8), (2, 6), (3, 6), (1, 9),
                  (2, 8), (3, 7), (4, 6), (1, 10), (2, 9), (4, 7), (5, 6),
                  (-1, 2), (-2, 3), (-1, 4), (-3, 2), (-1, 5), (-2, 4),
                  (-3, 4), (-1, 6), (-2, 5)]
    for r1, r2 in root_pairs:
        b = -(r1 + r2)
        c = r1 * r2
        # build LHS
        if b == 0:
            b_str = ""
        elif b > 0:
            b_str = f" + {b}x"
        else:
            b_str = f" − {abs(b)}x"
        if c >= 0:
            c_str = f" + {c}"
        else:
            c_str = f" − {abs(c)}"
        lhs = f"x²{b_str}{c_str}"

        ans = f"x = {min(r1, r2)} or x = {max(r1, r2)}"
        # distractors: sign-flipped roots, swap with c, b instead
        dist = [
            f"x = {-min(r1, r2)} or x = {-max(r1, r2)}",
            f"x = {r1 + r2} or x = {r1 * r2}",
            f"x = {abs(b)} or x = {abs(c)}",
        ]
        out.append(make_question(
            tier=4, topic_cell="algebra_advanced",
            strategy="factor_quadratic_simple", pillar="computation",
            question=f"Solve: {lhs} = 0",
            answer=ans, distractors=dist,
            context=f"Factor as (x−{r1})(x−{r2}) = 0 → x = {r1} or x = {r2}.",
        ))
    return out


def generate_all_algebra() -> list[dict]:
    out = []
    out.extend(generate_isolate_x_one_step())
    out.extend(generate_isolate_x_two_step())
    out.extend(generate_distribute())
    out.extend(generate_factor_difference_squares())
    out.extend(generate_factor_quadratic_simple())
    return out


if __name__ == "__main__":
    qs = generate_all_algebra()
    print(f"Generated {len(qs)} algebra questions")
    from collections import Counter
    print("By strategy:", dict(Counter(q["_meta"]["strategy"] for q in qs)))
