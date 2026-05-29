"""Hand-authored math exemplars — the seed corpus for bulk generation.

30 exemplars covering 6 pillars × 5 tiers each. Every T2+ exemplar
satisfies `gate_trick_context_required` by naming the trick or equation
explicitly in context.

Pillars:
  P1 — Arithmetic foundations (T1 heavy)
  P2 — Mental math tricks (T2-T3 heavy)
  P3 — Fractions, decimals, percents, signed numbers
  P4 — Algebra & equations
  P5 — Geometry, measurement, formulas
  P6 — Probability, stats & financial

Authoring contract:
  - Pass every gate in tools.quizgen.gates.math.PER_QUESTION_GATES
  - T1 stems are bare numeric (≤ 50 chars); higher tiers may have setup
  - Every T2+ context NAMES the trick / equation explicitly
  - Distractors model COMMON STUDENT ERRORS (off-by-one, sign flip,
    swapped operation, dropped carry, decimal misplacement)
  - Distractors are same order of magnitude as the answer

See `proposals/v2_audit/MATH_FRAMEWORK.md` and `MATH_TEMPLATES.md`.
"""
from __future__ import annotations


# --------------------------------------------------------------------------
# Pillar 1 — Arithmetic foundations
# --------------------------------------------------------------------------

P1_T1 = {
    "tier": 1,
    "question": "7 × 8 = ?",
    "answer": "56",
    "choices": ["56", "54", "49", "63"],
    "context": (
        "Times-table fact: 7 × 8 = 56. Memorize the multiplication "
        "table — automatic recall is the foundation of all mental math. "
        "Common confusion: 7² = 49 (one off), 6 × 9 = 54 (adjacent fact)."
    ),
}

P1_T2 = {
    "tier": 2,
    "question": "345 + 178 = ?",
    "answer": "523",
    "choices": ["523", "513", "423", "533"],
    "context": (
        "Add by tens then ones trick: 345 + 178 = 345 + 100 + 70 + 8 "
        "= 445 + 70 + 8 = 515 + 8 = 523. Break the second number into "
        "place-value chunks and add chunk by chunk to avoid carrying mistakes."
    ),
}

P1_T3 = {
    "tier": 3,
    "question": "Solve: −12 + 7 − (−5) = ?",
    "answer": "0",
    "choices": ["0", "−10", "10", "−14"],
    "context": (
        "Sign rules. Subtracting a negative flips to addition: "
        "−12 + 7 − (−5) = −12 + 7 + 5 = −12 + 12 = 0. Two negatives in "
        "a row become a positive."
    ),
}

P1_T4 = {
    "tier": 4,
    "question": "Simplify: (3 + 4 × 2) − 5²",
    "answer": "−14",
    "choices": ["−14", "−12", "11", "−24"],
    "context": (
        "PEMDAS / order of operations: parentheses first, then exponents, "
        "then ×/÷, then +/−. Inside parens: 4 × 2 = 8, then 3 + 8 = 11. "
        "Exponent: 5² = 25. Final: 11 − 25 = −14."
    ),
}

P1_T5 = {
    "tier": 5,
    "question": "Evaluate: 2³ + 4² − √81",
    "answer": "15",
    "choices": ["15", "17", "6", "24"],
    "context": (
        "Exponent rules + perfect-square recognition. 2³ = 8, 4² = 16, "
        "√81 = 9 (because 9² = 81 — recognize perfect squares 1-15²). "
        "So 8 + 16 − 9 = 15. PEMDAS: exponents before subtraction."
    ),
}


# --------------------------------------------------------------------------
# Pillar 2 — Mental math tricks
# --------------------------------------------------------------------------

P2_T1 = {
    "tier": 1,
    "question": "8 + 5 = ?",
    "answer": "13",
    "choices": ["13", "12", "14", "11"],
    "context": (
        "Make-a-ten trick: bridge through 10 to add fast. 8 + 2 = 10, "
        "then 10 + 3 = 13. Splitting the 5 into 2 + 3 lets you cross "
        "the ten cleanly. This is the foundation of all mental addition."
    ),
}

P2_T2 = {
    "tier": 2,
    "question": "25 × 16 = ?",
    "answer": "400",
    "choices": ["400", "300", "350", "450"],
    "context": (
        "Halving-and-doubling trick: halve one factor and double the other, "
        "keep going until one is round. 25 × 16 = 50 × 8 = 100 × 4 = 400. "
        "Halving × doubling preserves the product."
    ),
}

P2_T3 = {
    "tier": 3,
    "question": "19 × 21 = ?",
    "answer": "399",
    "choices": ["399", "400", "401", "380"],
    "context": (
        "Difference-of-squares trick: 19 × 21 = (20 − 1)(20 + 1) = "
        "20² − 1² = 400 − 1 = 399. When two factors are equidistant from a "
        "round number, use a² − b² mentally."
    ),
}

P2_T4 = {
    "tier": 4,
    "question": "Compute 47² mentally.",
    "answer": "2209",
    "choices": ["2209", "2200", "2400", "2025"],
    "context": (
        "Near-50 squaring trick: 47² = (50 − 3)² = 50² − 2(50)(3) + 3² = "
        "2500 − 300 + 9 = 2209. Use the perfect-square trinomial expansion "
        "(a − b)² = a² − 2ab + b² with a = 50."
    ),
}

P2_T5 = {
    "tier": 5,
    "question": "Expand: (x + 5)(x − 5)",
    "answer": "x² − 25",
    "choices": ["x² − 25", "x² + 25", "x² − 10x − 25", "x² − 10x + 25"],
    "context": (
        "Difference-of-squares formula: (a + b)(a − b) = a² − b². "
        "Here a = x, b = 5, so (x + 5)(x − 5) = x² − 25. The middle terms "
        "cancel: +5x − 5x = 0. Recognize this pattern instantly to factor "
        "or expand without FOIL."
    ),
}


# --------------------------------------------------------------------------
# Pillar 3 — Fractions, decimals, percents, signed numbers
# --------------------------------------------------------------------------

P3_T1 = {
    "tier": 1,
    "question": "Half of 14 = ?",
    "answer": "7",
    "choices": ["7", "6", "8", "12"],
    "context": (
        "Doubles and halves. Half of 14 = 7 because 7 + 7 = 14 (doubles). "
        "Halving and doubling are inverse moves; both build mental-math "
        "speed."
    ),
}

P3_T2 = {
    "tier": 2,
    "question": "1/4 as a percent = ?",
    "answer": "25%",
    "choices": ["25%", "14%", "40%", "20%"],
    "context": (
        "Common fraction-decimal-percent conversion: 1/4 = 0.25 = 25%. "
        "Memorize the conversion table: 1/2 = 50%, 1/4 = 25%, 1/5 = 20%, "
        "1/8 = 12.5%, 1/10 = 10%, 1/3 ≈ 33.3%. These appear everywhere."
    ),
}

P3_T3 = {
    "tier": 3,
    "question": "20% tip on $35.00 = ?",
    "answer": "$7.00",
    "choices": ["$7.00", "$3.50", "$7.50", "$14.00"],
    "context": (
        "Tip trick: 10% of any number = move the decimal one place left. "
        "10% of 35 = 3.50. Then double for 20%: 3.50 × 2 = 7.00. "
        "For 15% tip use 10% + half-of-10%."
    ),
}

P3_T4 = {
    "tier": 4,
    "question": "Solve: 3x − 7 = 14",
    "answer": "x = 7",
    "choices": ["x = 7", "x = 3", "x = 21", "x = −7"],
    "context": (
        "Two-step equation. Apply inverse operations: undo subtraction "
        "first (add 7 to both sides) gives 3x = 21; then undo "
        "multiplication (divide by 3) gives x = 7. Always undo "
        "operations in reverse order."
    ),
}

P3_T5 = {
    "tier": 5,
    "question": "Simplify: (x² − 9) / (x + 3)",
    "answer": "x − 3",
    "choices": ["x − 3", "x + 3", "x² − 3", "x − 9"],
    "context": (
        "Difference-of-squares factor: x² − 9 = (x + 3)(x − 3). "
        "Cancel the common (x + 3) factor: (x + 3)(x − 3)/(x + 3) = x − 3. "
        "Factor first, then cancel — never cancel terms before factoring."
    ),
}


# --------------------------------------------------------------------------
# Pillar 4 — Algebra & equations
# --------------------------------------------------------------------------

P4_T1 = {
    "tier": 1,
    "question": "5 + ? = 12",
    "answer": "7",
    "choices": ["7", "6", "8", "17"],
    "context": (
        "Missing addend (subtraction is the inverse of addition). "
        "5 + ? = 12 means 12 − 5 = 7. Fact families: 5 + 7 = 12, "
        "7 + 5 = 12, 12 − 5 = 7, 12 − 7 = 5 all encode the same fact."
    ),
}

P4_T2 = {
    "tier": 2,
    "question": "Simplify: 4x + 3x − 2x",
    "answer": "5x",
    "choices": ["5x", "9x", "7x", "5"],
    "context": (
        "Combining like terms. Terms with the same variable add or "
        "subtract their coefficients: 4x + 3x − 2x = (4 + 3 − 2)x = 5x. "
        "Treat x as a unit — like counting 4 apples + 3 apples − 2 apples."
    ),
}

P4_T3 = {
    "tier": 3,
    "question": "Solve: 3(x + 4) = 21",
    "answer": "x = 3",
    "choices": ["x = 3", "x = 7", "x = 17", "x = 21"],
    "context": (
        "Distributive property + two-step equation. Distribute first: "
        "3(x + 4) = 3x + 12. Then 3x + 12 = 21, so 3x = 9 and x = 3. "
        "Or divide both sides by 3 first: x + 4 = 7, x = 3."
    ),
}

P4_T4 = {
    "tier": 4,
    "question": "Find the slope of the line through (1, 3) and (4, 9).",
    "answer": "2",
    "choices": ["2", "3", "1/2", "6"],
    "context": (
        "Slope formula: m = (y₂ − y₁) / (x₂ − x₁) = rise over run. "
        "Here m = (9 − 3) / (4 − 1) = 6/3 = 2. Slope = how much y "
        "changes per unit change in x."
    ),
}

P4_T5 = {
    "tier": 5,
    "question": "Solve: x² + 5x + 6 = 0",
    "answer": "x = -3 or x = -2",
    "choices": [
        "x = -3 or x = -2",
        "x = 3 or x = 2",
        "x = -6 or x = -1",
        "x = 6 or x = 5",
    ],
    "context": (
        "Trinomial factoring: find two numbers that multiply to 6 and "
        "add to 5. Those are 2 and 3. So x² + 5x + 6 = (x + 2)(x + 3) = 0; "
        "either factor zero gives x = −2 or x = −3. The quadratic formula "
        "x = (−b ± √(b²−4ac))/(2a) would also work."
    ),
}


# --------------------------------------------------------------------------
# Pillar 5 — Geometry, measurement, formulas
# --------------------------------------------------------------------------

P5_T1 = {
    "tier": 1,
    "question": "5, 10, 15, 20, ? — what comes next?",
    "answer": "25",
    "choices": ["25", "30", "21", "100"],
    "context": (
        "Skip counting by 5s. Adding 5 each step: 5, 10, 15, 20, 25, 30. "
        "Skip counting is the bridge between counting and multiplication "
        "(5 × 5 = 25)."
    ),
}

P5_T2 = {
    "tier": 2,
    "question": "Rectangle: length 7, width 4. Area?",
    "answer": "28",
    "choices": ["28", "22", "11", "14"],
    "context": (
        "Rectangle area formula: A = l × w. Here A = 7 × 4 = 28 square "
        "units. Perimeter would be P = 2(l + w) = 2(11) = 22 — don't mix "
        "the two formulas."
    ),
}

P5_T3 = {
    "tier": 3,
    "question": "Circle: radius 6. Circumference in terms of π?",
    "answer": "12π",
    "choices": ["12π", "6π", "36π", "12"],
    "context": (
        "Circumference of a circle: C = 2πr. With r = 6, C = 2 × π × 6 = "
        "12π. Don't confuse with area A = πr² = 36π. Circumference uses "
        "radius once, area uses it squared."
    ),
}

P5_T4 = {
    "tier": 4,
    "question": "Right triangle with legs 5 and 12. Hypotenuse?",
    "answer": "13",
    "choices": ["13", "17", "7", "60"],
    "context": (
        "Pythagorean theorem: a² + b² = c². 5² + 12² = 25 + 144 = 169; "
        "c = √169 = 13. The 5-12-13 triangle is one of four common "
        "Pythagorean triples to memorize: 3-4-5, 5-12-13, 8-15-17, 7-24-25."
    ),
}

P5_T5 = {
    "tier": 5,
    "question": "Sphere with radius 3. Volume in terms of π?",
    "answer": "36π",
    "choices": ["36π", "12π", "9π", "108π"],
    "context": (
        "Sphere volume formula: V = (4/3)πr³. With r = 3, r³ = 27, "
        "so V = (4/3) × 27 × π = 36π. Don't confuse with surface area "
        "4πr² (T4 sphere area = 36π too by coincidence at r = 3 — be careful)."
    ),
}


# --------------------------------------------------------------------------
# Pillar 6 — Probability, stats & financial
# --------------------------------------------------------------------------

P6_T1 = {
    "tier": 1,
    "question": "2, 4, 6, 8, ? — what comes next?",
    "answer": "10",
    "choices": ["10", "9", "12", "16"],
    "context": (
        "Skip counting by 2s — even numbers. Adding 2 each step: 2, 4, "
        "6, 8, 10, 12. This pattern is the foundation for the 2 times "
        "table and recognizing even numbers."
    ),
}

P6_T2 = {
    "tier": 2,
    "question": "Mean of 4, 7, 8, 11, 5 = ?",
    "answer": "7",
    "choices": ["7", "5", "8", "35"],
    "context": (
        "Mean (average) = sum ÷ count. Sum: 4 + 7 + 8 + 11 + 5 = 35. "
        "Count: 5. Mean = 35 ÷ 5 = 7. Median (middle value when sorted: "
        "4, 5, 7, 8, 11) is also 7 here — a coincidence; usually they differ."
    ),
}

P6_T3 = {
    "tier": 3,
    "question": "Roll two dice. Probability both show 6?",
    "answer": "1/36",
    "choices": ["1/36", "1/6", "2/12", "1/12"],
    "context": (
        "Compound probability with independent events: multiply the "
        "single-event probabilities. P(6 on die 1) = 1/6; P(6 on die 2) = "
        "1/6. P(both 6) = 1/6 × 1/6 = 1/36. Independent events: one outcome "
        "does not affect the other."
    ),
}

P6_T4 = {
    "tier": 4,
    "question": "$500 at 4% simple interest for 3 years. Total interest earned?",
    "answer": "$60",
    "choices": ["$60", "$20", "$120", "$612.32"],
    "context": (
        "Simple interest formula: I = P × r × t. P = 500, r = 0.04, "
        "t = 3 years. I = 500 × 0.04 × 3 = 60. Total = principal + "
        "interest = 560. Compound interest A = P(1 + r/n)^(nt) gives a "
        "different number; check which the problem asks for."
    ),
}

P6_T5 = {
    "tier": 5,
    "question": "Arithmetic sequence 3, 7, 11, 15, ... — find the 10th term.",
    "answer": "39",
    "choices": ["39", "40", "43", "35"],
    "context": (
        "Arithmetic sequence nth term formula: aₙ = a₁ + (n − 1)d, where "
        "a₁ is the first term and d is the common difference. Here a₁ = 3, "
        "d = 4. So a₁₀ = 3 + 9 × 4 = 3 + 36 = 39. Watch the (n − 1) — "
        "off-by-one is the most common mistake."
    ),
}


# --------------------------------------------------------------------------
# All exemplars (validated by tests/test_math_exemplars.py)
# --------------------------------------------------------------------------

ALL_EXEMPLARS = [
    # P1
    P1_T1, P1_T2, P1_T3, P1_T4, P1_T5,
    # P2
    P2_T1, P2_T2, P2_T3, P2_T4, P2_T5,
    # P3
    P3_T1, P3_T2, P3_T3, P3_T4, P3_T5,
    # P4
    P4_T1, P4_T2, P4_T3, P4_T4, P4_T5,
    # P5
    P5_T1, P5_T2, P5_T3, P5_T4, P5_T5,
    # P6
    P6_T1, P6_T2, P6_T3, P6_T4, P6_T5,
]


__all__ = ["ALL_EXEMPLARS"] + [
    f"P{p}_T{t}" for p in range(1, 7) for t in range(1, 6)
]
