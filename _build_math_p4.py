"""Generate 400 math P4 (Algebra & equations) questions.

Distribution:
  T1: 30  — missing addend, fact families
  T2: 60  — combining like terms, one-step equations
  T3: 110 — combining like terms, distribute-then-solve, two-step eq + inequalities
  T4: 100 — solve linear, slope, slope-intercept, systems, exponent rules,
            scientific notation, square root simplify, function notation
  T5: 100 — polynomial ops, FOIL, factoring, quadratic by all methods,
            discriminant, vertex form, sequences

Voice + structure: MATH_FRAMEWORK.md §1 (Mental-Move Pattern), MATH_TEMPLATES.md
exemplars: P4_T1..P4_T5 in tools/quizgen/exemplars/math.py.

CRITICAL: ASCII hyphen "-" for quadratic solutions because math_correctness
extracts numbers via NUMERIC_RE = re.compile(r"-?\\d+(?:\\.\\d+)?").
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402

OUT_PATH = REPO / "proposals" / "v2_audit" / "_math_p4_output.json"

ALL_QUESTIONS: list[dict] = []


# ============================================================================
# TIER 1 — 30 questions: missing addend + fact families
# Stem cap 50, budget 280. T1 needs NO trick-named context (anti_rote exempt).
# ============================================================================

T1: list[dict] = []


def add_t1_missing_addend(a: int, missing: int, sum_v: int, distractors: list[int]) -> None:
    T1.append({
        "tier": 1,
        "question": f"{a} + ? = {sum_v}",
        "answer": str(missing),
        "choices": [str(missing)] + [str(d) for d in distractors],
        "context": (
            f"Missing addend (subtraction is the inverse of addition). "
            f"{a} + ? = {sum_v} means {sum_v} - {a} = {missing}. "
            f"Fact families: {a} + {missing} = {sum_v}, {missing} + {a} = {sum_v}, "
            f"{sum_v} - {a} = {missing}, {sum_v} - {missing} = {a}."
        ),
        "_pillar": 4,
        "_strategy": "missing_addend",
    })


# 18 missing-addend questions
add_t1_missing_addend(5, 7, 12, [6, 8, 17])
add_t1_missing_addend(7, 8, 15, [7, 9, 22])
add_t1_missing_addend(4, 9, 13, [8, 10, 17])
add_t1_missing_addend(6, 7, 13, [6, 8, 19])
add_t1_missing_addend(8, 4, 12, [3, 5, 20])
add_t1_missing_addend(3, 8, 11, [7, 9, 14])
add_t1_missing_addend(9, 6, 15, [5, 7, 24])
add_t1_missing_addend(2, 9, 11, [8, 10, 13])
add_t1_missing_addend(5, 9, 14, [8, 10, 19])
add_t1_missing_addend(7, 6, 13, [5, 7, 20])
add_t1_missing_addend(4, 8, 12, [7, 9, 16])
add_t1_missing_addend(6, 9, 15, [8, 10, 21])
add_t1_missing_addend(3, 7, 10, [6, 8, 13])
add_t1_missing_addend(8, 5, 13, [4, 6, 21])
add_t1_missing_addend(9, 7, 16, [6, 8, 25])
add_t1_missing_addend(2, 8, 10, [7, 9, 12])
add_t1_missing_addend(5, 6, 11, [5, 7, 16])
add_t1_missing_addend(4, 7, 11, [6, 8, 15])


def add_t1_fact_family(a: int, b: int, sum_v: int, missing: str, given_eq: str, distractors: list[int]) -> None:
    # given e.g. "4 + 3 = 7" then "7 - 3 = ?" — answer is 4
    T1.append({
        "tier": 1,
        "question": f"If {given_eq}, then {sum_v} - {b} = ?",
        "answer": missing,
        "choices": [missing] + [str(d) for d in distractors],
        "context": (
            f"Fact family. The four facts share the same three numbers: "
            f"{a} + {b} = {sum_v}, {b} + {a} = {sum_v}, {sum_v} - {a} = {b}, "
            f"{sum_v} - {b} = {a}. Subtraction is the inverse of addition."
        ),
        "_pillar": 4,
        "_strategy": "fact_family",
    })


# 12 fact-family questions
add_t1_fact_family(4, 3, 7, "4", "4 + 3 = 7", [3, 5, 10])
add_t1_fact_family(5, 2, 7, "5", "5 + 2 = 7", [2, 6, 9])
add_t1_fact_family(6, 4, 10, "6", "6 + 4 = 10", [4, 7, 14])
add_t1_fact_family(8, 3, 11, "8", "8 + 3 = 11", [3, 9, 14])
add_t1_fact_family(7, 5, 12, "7", "7 + 5 = 12", [5, 8, 17])
add_t1_fact_family(9, 2, 11, "9", "9 + 2 = 11", [2, 10, 13])
add_t1_fact_family(6, 7, 13, "6", "6 + 7 = 13", [7, 5, 20])
add_t1_fact_family(8, 5, 13, "8", "8 + 5 = 13", [5, 9, 21])
add_t1_fact_family(9, 4, 13, "9", "9 + 4 = 13", [4, 10, 17])
add_t1_fact_family(7, 8, 15, "7", "7 + 8 = 15", [8, 6, 23])
add_t1_fact_family(6, 9, 15, "6", "6 + 9 = 15", [9, 7, 21])
add_t1_fact_family(5, 8, 13, "5", "5 + 8 = 13", [8, 6, 18])


# ============================================================================
# TIER 2 — 60 questions: combining like terms basics + one-step equations
# Stem cap 100, budget 400. T2+ context must NAME a trick or equation.
# ============================================================================

T2: list[dict] = []


def add_t2_combine_like(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T2.append({
        "tier": 2,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Combining like terms. Terms with the same variable add or "
            f"subtract their coefficients: {walk}. Treat the variable as a "
            f"unit — like counting apples + apples."
        ),
        "_pillar": 4,
        "_strategy": "combine_like_terms",
    })


# 25 combining-like-terms questions
add_t2_combine_like("Simplify: 5y + y - 3y", "3y", ["3y", "4y", "y", "5y"],
                    "5y + 1y - 3y = (5 + 1 - 3)y = 3y")
add_t2_combine_like("Simplify: 7x - 2x + x", "6x", ["6x", "5x", "8x", "10x"],
                    "7x - 2x + 1x = (7 - 2 + 1)x = 6x")
add_t2_combine_like("Simplify: 4a + 6a", "10a", ["10a", "24a", "10a²", "2a"],
                    "4a + 6a = (4 + 6)a = 10a")
add_t2_combine_like("Simplify: 9m - 3m", "6m", ["6m", "12m", "27m", "3m"],
                    "9m - 3m = (9 - 3)m = 6m")
add_t2_combine_like("Simplify: 2b + 5b + 3b", "10b", ["10b", "30b", "6b", "10b³"],
                    "2b + 5b + 3b = (2 + 5 + 3)b = 10b")
add_t2_combine_like("Simplify: 8x - x - 2x", "5x", ["5x", "7x", "10x", "11x"],
                    "8x - 1x - 2x = (8 - 1 - 2)x = 5x")
add_t2_combine_like("Simplify: 3n + 4n - 5n", "2n", ["2n", "12n", "n", "12n³"],
                    "3n + 4n - 5n = (3 + 4 - 5)n = 2n")
add_t2_combine_like("Simplify: 6y + 2y - y", "7y", ["7y", "8y", "5y", "12y"],
                    "6y + 2y - 1y = (6 + 2 - 1)y = 7y")
add_t2_combine_like("Simplify: 10x - 4x", "6x", ["6x", "14x", "40x", "4x"],
                    "10x - 4x = (10 - 4)x = 6x")
add_t2_combine_like("Simplify: 5p + 3p - 2p", "6p", ["6p", "10p", "30p", "4p"],
                    "5p + 3p - 2p = (5 + 3 - 2)p = 6p")
add_t2_combine_like("Simplify: 4t + 7t", "11t", ["11t", "28t", "3t", "11t²"],
                    "4t + 7t = (4 + 7)t = 11t")
add_t2_combine_like("Simplify: 9k - k - 3k", "5k", ["5k", "6k", "11k", "7k"],
                    "9k - 1k - 3k = (9 - 1 - 3)k = 5k")
add_t2_combine_like("Simplify: 2x + 8x - 4x", "6x", ["6x", "10x", "14x", "64x"],
                    "2x + 8x - 4x = (2 + 8 - 4)x = 6x")
add_t2_combine_like("Simplify: 6h + 2h + h", "9h", ["9h", "8h", "12h", "10h"],
                    "6h + 2h + 1h = (6 + 2 + 1)h = 9h")
add_t2_combine_like("Simplify: 7r - 3r + 2r", "6r", ["6r", "8r", "12r", "4r"],
                    "7r - 3r + 2r = (7 - 3 + 2)r = 6r")
add_t2_combine_like("Simplify: 12y - 5y", "7y", ["7y", "17y", "60y", "5y"],
                    "12y - 5y = (12 - 5)y = 7y")
add_t2_combine_like("Simplify: 3x + 3x + 3x", "9x", ["9x", "27x", "6x", "9x³"],
                    "3x + 3x + 3x = (3 + 3 + 3)x = 9x")
add_t2_combine_like("Simplify: 11m - 4m - m", "6m", ["6m", "16m", "7m", "8m"],
                    "11m - 4m - 1m = (11 - 4 - 1)m = 6m")
add_t2_combine_like("Simplify: 5a + 9a - 4a", "10a", ["10a", "18a", "8a", "180a"],
                    "5a + 9a - 4a = (5 + 9 - 4)a = 10a")
add_t2_combine_like("Simplify: 8b - 2b + 4b", "10b", ["10b", "14b", "6b", "64b"],
                    "8b - 2b + 4b = (8 - 2 + 4)b = 10b")
add_t2_combine_like("Simplify: 7c + 2c - 5c", "4c", ["4c", "14c", "10c", "9c"],
                    "7c + 2c - 5c = (7 + 2 - 5)c = 4c")
add_t2_combine_like("Simplify: 6d - 6d + 3d", "3d", ["3d", "9d", "15d", "0"],
                    "6d - 6d + 3d = (6 - 6 + 3)d = 3d")
add_t2_combine_like("Simplify: 5x + 2x - 3x", "4x", ["4x", "10x", "6x", "0"],
                    "5x + 2x - 3x = (5 + 2 - 3)x = 4x")
add_t2_combine_like("Simplify: 4y + 4y + 4y - 2y", "10y", ["10y", "14y", "12y", "8y"],
                    "4y + 4y + 4y - 2y = (4 + 4 + 4 - 2)y = 10y")
add_t2_combine_like("Simplify: 3w + 6w - w", "8w", ["8w", "9w", "10w", "18w"],
                    "3w + 6w - 1w = (3 + 6 - 1)w = 8w")


def add_t2_one_step(stem: str, answer: str, choices: list[str], op_undo: str, walk: str) -> None:
    T2.append({
        "tier": 2,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"One-step equation. Use inverse operations: {op_undo}. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "one_step_equation",
    })


# 35 one-step equation questions across +, -, ×, ÷
# Addition: solve x + a = b → undo by subtracting
add_t2_one_step("Solve: x + 5 = 12", "x = 7", ["x = 7", "x = 17", "x = 12", "x = -7"],
                "subtract 5 from both sides to undo addition", "x = 12 - 5 = 7.")
add_t2_one_step("Solve: x + 8 = 13", "x = 5", ["x = 5", "x = 21", "x = 13", "x = -5"],
                "subtract 8 from both sides", "x = 13 - 8 = 5.")
add_t2_one_step("Solve: x + 3 = 11", "x = 8", ["x = 8", "x = 14", "x = 11", "x = -8"],
                "subtract 3 from both sides", "x = 11 - 3 = 8.")
add_t2_one_step("Solve: x + 9 = 20", "x = 11", ["x = 11", "x = 29", "x = 20", "x = -11"],
                "subtract 9 from both sides", "x = 20 - 9 = 11.")
add_t2_one_step("Solve: x + 6 = 15", "x = 9", ["x = 9", "x = 21", "x = 15", "x = -9"],
                "subtract 6 from both sides", "x = 15 - 6 = 9.")
add_t2_one_step("Solve: x + 4 = 9", "x = 5", ["x = 5", "x = 13", "x = 9", "x = -5"],
                "subtract 4 from both sides", "x = 9 - 4 = 5.")
add_t2_one_step("Solve: x + 7 = 16", "x = 9", ["x = 9", "x = 23", "x = 16", "x = -9"],
                "subtract 7 from both sides", "x = 16 - 7 = 9.")
add_t2_one_step("Solve: x + 2 = 14", "x = 12", ["x = 12", "x = 16", "x = 14", "x = -12"],
                "subtract 2 from both sides", "x = 14 - 2 = 12.")
add_t2_one_step("Solve: x + 11 = 25", "x = 14", ["x = 14", "x = 36", "x = 25", "x = -14"],
                "subtract 11 from both sides", "x = 25 - 11 = 14.")

# Subtraction: solve x - a = b → undo by adding
add_t2_one_step("Solve: x - 7 = 3", "x = 10", ["x = 10", "x = -4", "x = 3", "x = 21"],
                "add 7 to both sides to undo subtraction", "x = 3 + 7 = 10.")
add_t2_one_step("Solve: x - 5 = 8", "x = 13", ["x = 13", "x = 3", "x = 8", "x = 40"],
                "add 5 to both sides", "x = 8 + 5 = 13.")
add_t2_one_step("Solve: x - 9 = 11", "x = 20", ["x = 20", "x = 2", "x = 11", "x = 99"],
                "add 9 to both sides", "x = 11 + 9 = 20.")
add_t2_one_step("Solve: x - 4 = 12", "x = 16", ["x = 16", "x = 8", "x = 12", "x = 48"],
                "add 4 to both sides", "x = 12 + 4 = 16.")
add_t2_one_step("Solve: x - 6 = 7", "x = 13", ["x = 13", "x = 1", "x = 7", "x = 42"],
                "add 6 to both sides", "x = 7 + 6 = 13.")
add_t2_one_step("Solve: x - 3 = 9", "x = 12", ["x = 12", "x = 6", "x = 9", "x = 27"],
                "add 3 to both sides", "x = 9 + 3 = 12.")
add_t2_one_step("Solve: x - 8 = 6", "x = 14", ["x = 14", "x = -2", "x = 6", "x = 48"],
                "add 8 to both sides", "x = 6 + 8 = 14.")
add_t2_one_step("Solve: x - 2 = 15", "x = 17", ["x = 17", "x = 13", "x = 15", "x = 30"],
                "add 2 to both sides", "x = 15 + 2 = 17.")

# Multiplication: solve a*x = b → undo by dividing
add_t2_one_step("Solve: 3x = 21", "x = 7", ["x = 7", "x = 18", "x = 24", "x = 63"],
                "divide both sides by 3 to undo multiplication", "x = 21 / 3 = 7.")
add_t2_one_step("Solve: 4x = 20", "x = 5", ["x = 5", "x = 4", "x = 6", "x = 16"],
                "divide both sides by 4", "x = 20 / 4 = 5.")
add_t2_one_step("Solve: 5x = 35", "x = 7", ["x = 7", "x = 6", "x = 8", "x = 30"],
                "divide both sides by 5", "x = 35 / 5 = 7.")
add_t2_one_step("Solve: 6x = 24", "x = 4", ["x = 4", "x = 3", "x = 5", "x = 18"],
                "divide both sides by 6", "x = 24 / 6 = 4.")
add_t2_one_step("Solve: 7x = 28", "x = 4", ["x = 4", "x = 3", "x = 5", "x = 21"],
                "divide both sides by 7", "x = 28 / 7 = 4.")
add_t2_one_step("Solve: 8x = 56", "x = 7", ["x = 7", "x = 6", "x = 8", "x = 48"],
                "divide both sides by 8", "x = 56 / 8 = 7.")
add_t2_one_step("Solve: 9x = 45", "x = 5", ["x = 5", "x = 4", "x = 6", "x = 36"],
                "divide both sides by 9", "x = 45 / 9 = 5.")
add_t2_one_step("Solve: 2x = 18", "x = 9", ["x = 9", "x = 8", "x = 10", "x = 16"],
                "divide both sides by 2", "x = 18 / 2 = 9.")
add_t2_one_step("Solve: 10x = 90", "x = 9", ["x = 9", "x = 8", "x = 10", "x = 80"],
                "divide both sides by 10", "x = 90 / 10 = 9.")

# Division: solve x/a = b → undo by multiplying
add_t2_one_step("Solve: x/4 = 8", "x = 32", ["x = 32", "x = 2", "x = 12", "x = 4"],
                "multiply both sides by 4 to undo division", "x = 8 * 4 = 32.")
add_t2_one_step("Solve: x/3 = 7", "x = 21", ["x = 21", "x = 10", "x = 4", "x = 3"],
                "multiply both sides by 3", "x = 7 * 3 = 21.")
add_t2_one_step("Solve: x/5 = 6", "x = 30", ["x = 30", "x = 11", "x = 1", "x = 5"],
                "multiply both sides by 5", "x = 6 * 5 = 30.")
add_t2_one_step("Solve: x/2 = 9", "x = 18", ["x = 18", "x = 11", "x = 7", "x = 2"],
                "multiply both sides by 2", "x = 9 * 2 = 18.")
add_t2_one_step("Solve: x/6 = 4", "x = 24", ["x = 24", "x = 10", "x = -2", "x = 6"],
                "multiply both sides by 6", "x = 4 * 6 = 24.")
add_t2_one_step("Solve: x/7 = 3", "x = 21", ["x = 21", "x = 10", "x = -4", "x = 7"],
                "multiply both sides by 7", "x = 3 * 7 = 21.")
add_t2_one_step("Solve: x/8 = 5", "x = 40", ["x = 40", "x = 32", "x = 48", "x = 13"],
                "multiply both sides by 8", "x = 5 * 8 = 40.")
add_t2_one_step("Solve: x/9 = 2", "x = 18", ["x = 18", "x = 11", "x = -7", "x = 9"],
                "multiply both sides by 9", "x = 2 * 9 = 18.")
add_t2_one_step("Solve: x/10 = 4", "x = 40", ["x = 40", "x = 14", "x = -6", "x = 10"],
                "multiply both sides by 10", "x = 4 * 10 = 40.")


# ============================================================================
# TIER 3 — 110 questions
# Stem cap 160, budget 550
# ============================================================================

T3: list[dict] = []


def add_t3_combine_like(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T3.append({
        "tier": 3,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Combining like terms. Group variable terms with variable terms "
            f"and constants with constants: {walk}. Constants are like terms "
            f"with each other; x and constants are NOT like terms."
        ),
        "_pillar": 4,
        "_strategy": "combine_like_terms_mixed",
    })


# 20 mixed-combining (variables + constants)
add_t3_combine_like("Simplify: 3x + 5 - x + 2", "2x + 7",
                    ["2x + 7", "4x + 7", "2x + 3", "9x"],
                    "(3x - x) + (5 + 2) = 2x + 7")
add_t3_combine_like("Simplify: 5x + 8 - 2x - 3", "3x + 5",
                    ["3x + 5", "7x + 5", "3x + 11", "8x"],
                    "(5x - 2x) + (8 - 3) = 3x + 5")
add_t3_combine_like("Simplify: 7x - 4 + 2x + 9", "9x + 5",
                    ["9x + 5", "5x + 5", "9x + 13", "14x"],
                    "(7x + 2x) + (-4 + 9) = 9x + 5")
add_t3_combine_like("Simplify: 4y + 3 - y + 6", "3y + 9",
                    ["3y + 9", "5y + 9", "3y - 3", "12y"],
                    "(4y - y) + (3 + 6) = 3y + 9")
add_t3_combine_like("Simplify: 6a - 2 + a - 5", "7a - 7",
                    ["7a - 7", "5a - 7", "7a - 3", "0"],
                    "(6a + a) + (-2 - 5) = 7a - 7")
add_t3_combine_like("Simplify: 8x + 4 - 5x - 1", "3x + 3",
                    ["3x + 3", "13x + 3", "3x + 5", "6x"],
                    "(8x - 5x) + (4 - 1) = 3x + 3")
add_t3_combine_like("Simplify: 2x + 7 + 3x - 4", "5x + 3",
                    ["5x + 3", "x + 3", "5x + 11", "8x"],
                    "(2x + 3x) + (7 - 4) = 5x + 3")
add_t3_combine_like("Simplify: 9m - 6 - 4m + 2", "5m - 4",
                    ["5m - 4", "13m - 4", "5m - 8", "m"],
                    "(9m - 4m) + (-6 + 2) = 5m - 4")
add_t3_combine_like("Simplify: 3b + 8 + b - 12", "4b - 4",
                    ["4b - 4", "2b - 4", "4b + 20", "0"],
                    "(3b + b) + (8 - 12) = 4b - 4")
add_t3_combine_like("Simplify: 10x - 3 - 6x + 8", "4x + 5",
                    ["4x + 5", "16x + 5", "4x - 11", "9x"],
                    "(10x - 6x) + (-3 + 8) = 4x + 5")
add_t3_combine_like("Simplify: 5n + 2 - 3n - 7", "2n - 5",
                    ["2n - 5", "8n - 5", "2n + 9", "-3"],
                    "(5n - 3n) + (2 - 7) = 2n - 5")
add_t3_combine_like("Simplify: 7y - 1 + 4y - 9", "11y - 10",
                    ["11y - 10", "3y - 10", "11y + 8", "y"],
                    "(7y + 4y) + (-1 - 9) = 11y - 10")
add_t3_combine_like("Simplify: 6x + 9 - 6x + 3", "12",
                    ["12", "12x", "6", "0"],
                    "(6x - 6x) + (9 + 3) = 0x + 12 = 12")
add_t3_combine_like("Simplify: 4a - 5 + 6a + 2", "10a - 3",
                    ["10a - 3", "2a - 3", "10a - 7", "7a"],
                    "(4a + 6a) + (-5 + 2) = 10a - 3")
add_t3_combine_like("Simplify: 12x + 4 - 5x - 9", "7x - 5",
                    ["7x - 5", "17x - 5", "7x + 13", "2x"],
                    "(12x - 5x) + (4 - 9) = 7x - 5")
add_t3_combine_like("Simplify: 3x + 2x - 7 + 4", "5x - 3",
                    ["5x - 3", "x - 3", "5x + 11", "2x"],
                    "(3x + 2x) + (-7 + 4) = 5x - 3")
add_t3_combine_like("Simplify: 8y - 3 + y - 2y", "7y - 3",
                    ["7y - 3", "11y - 3", "7y + 5", "6y"],
                    "(8y + y - 2y) + (-3) = 7y - 3")
add_t3_combine_like("Simplify: 4x + 3y + 2x - y", "6x + 2y",
                    ["6x + 2y", "8xy", "6x + 4y", "9xy"],
                    "(4x + 2x) + (3y - y) = 6x + 2y. x-terms and y-terms are NOT like terms.")
add_t3_combine_like("Simplify: 5a + 2b - 3a + 4b", "2a + 6b",
                    ["2a + 6b", "8ab", "2a - 2b", "8a + 6b"],
                    "(5a - 3a) + (2b + 4b) = 2a + 6b")
add_t3_combine_like("Simplify: 7m - 4n + 2m + n", "9m - 3n",
                    ["9m - 3n", "6mn", "9m - 5n", "5m - 3n"],
                    "(7m + 2m) + (-4n + n) = 9m - 3n")


def add_t3_distribute(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T3.append({
        "tier": 3,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Distributive property: a(b + c) = ab + ac. Multiply the outside "
            f"factor by EVERY term inside the parens. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "distribute",
    })


# 20 distribute-through-parens
add_t3_distribute("Expand: 3(x + 4)", "3x + 12",
                  ["3x + 12", "3x + 4", "x + 12", "3x + 7"],
                  "3*x + 3*4 = 3x + 12")
add_t3_distribute("Expand: 5(2x - 3)", "10x - 15",
                  ["10x - 15", "10x - 3", "7x - 15", "10x + 15"],
                  "5*2x + 5*(-3) = 10x - 15")
add_t3_distribute("Expand: -2(x + 5)", "-2x - 10",
                  ["-2x - 10", "-2x + 10", "-2x + 5", "2x + 10"],
                  "-2*x + (-2)*5 = -2x - 10. Sign of -2 distributes too.")
add_t3_distribute("Expand: 4(3x + 1)", "12x + 4",
                  ["12x + 4", "12x + 1", "7x + 4", "12x + 5"],
                  "4*3x + 4*1 = 12x + 4")
add_t3_distribute("Expand: 6(x - 2)", "6x - 12",
                  ["6x - 12", "6x - 2", "x - 12", "6x + 12"],
                  "6*x + 6*(-2) = 6x - 12")
add_t3_distribute("Expand: 2(5x + 7)", "10x + 14",
                  ["10x + 14", "10x + 7", "7x + 14", "10x + 9"],
                  "2*5x + 2*7 = 10x + 14")
add_t3_distribute("Expand: 7(x - 3)", "7x - 21",
                  ["7x - 21", "7x - 3", "x - 21", "7x + 21"],
                  "7*x + 7*(-3) = 7x - 21")
add_t3_distribute("Expand: -3(2x - 4)", "-6x + 12",
                  ["-6x + 12", "-6x - 12", "-5x + 12", "6x - 12"],
                  "-3*2x + (-3)*(-4) = -6x + 12. Two negatives multiply to a positive.")
add_t3_distribute("Expand: 8(x + 2)", "8x + 16",
                  ["8x + 16", "8x + 2", "x + 16", "8x + 10"],
                  "8*x + 8*2 = 8x + 16")
add_t3_distribute("Expand: 5(3x - 1)", "15x - 5",
                  ["15x - 5", "15x - 1", "8x - 5", "15x + 5"],
                  "5*3x + 5*(-1) = 15x - 5")
add_t3_distribute("Expand: -4(x - 6)", "-4x + 24",
                  ["-4x + 24", "-4x - 24", "-3x + 24", "4x - 24"],
                  "-4*x + (-4)*(-6) = -4x + 24")
add_t3_distribute("Expand: 9(x + 1)", "9x + 9",
                  ["9x + 9", "9x + 1", "x + 9", "10x + 9"],
                  "9*x + 9*1 = 9x + 9")
add_t3_distribute("Expand: 3(4x - 5)", "12x - 15",
                  ["12x - 15", "12x - 5", "7x - 15", "12x + 15"],
                  "3*4x + 3*(-5) = 12x - 15")
add_t3_distribute("Expand: -5(x + 3)", "-5x - 15",
                  ["-5x - 15", "-5x + 15", "-5x + 3", "5x + 15"],
                  "-5*x + (-5)*3 = -5x - 15")
add_t3_distribute("Expand: 2(7x - 4)", "14x - 8",
                  ["14x - 8", "14x - 4", "9x - 8", "14x + 8"],
                  "2*7x + 2*(-4) = 14x - 8")
add_t3_distribute("Expand: 6(2x + 3)", "12x + 18",
                  ["12x + 18", "12x + 3", "8x + 18", "12x + 9"],
                  "6*2x + 6*3 = 12x + 18")
add_t3_distribute("Expand: -1(x - 7)", "-x + 7",
                  ["-x + 7", "-x - 7", "x + 7", "x - 7"],
                  "-1*x + (-1)*(-7) = -x + 7. Negating drops or flips each sign.")
add_t3_distribute("Expand: 4(x + 9)", "4x + 36",
                  ["4x + 36", "4x + 9", "x + 36", "4x + 13"],
                  "4*x + 4*9 = 4x + 36")
add_t3_distribute("Expand: 10(x - 1)", "10x - 10",
                  ["10x - 10", "10x - 1", "9x - 10", "10x + 10"],
                  "10*x + 10*(-1) = 10x - 10")
add_t3_distribute("Expand: -2(3x + 4)", "-6x - 8",
                  ["-6x - 8", "-6x + 8", "-5x - 8", "6x - 8"],
                  "-2*3x + (-2)*4 = -6x - 8")


def add_t3_two_step(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T3.append({
        "tier": 3,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Two-step equation. Use inverse operations in reverse order: "
            f"undo addition/subtraction FIRST, then undo "
            f"multiplication/division. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "two_step_equation",
    })


# 40 two-step equations
add_t3_two_step("Solve: 3x + 5 = 20", "x = 5",
                ["x = 5", "x = 25/3", "x = 15", "x = -5"],
                "3x = 20 - 5 = 15; x = 15 / 3 = 5.")
add_t3_two_step("Solve: 2x - 7 = 9", "x = 8",
                ["x = 8", "x = 1", "x = 16", "x = -8"],
                "2x = 9 + 7 = 16; x = 16 / 2 = 8.")
add_t3_two_step("Solve: 4x + 1 = 17", "x = 4",
                ["x = 4", "x = 16", "x = 18", "x = -4"],
                "4x = 17 - 1 = 16; x = 16 / 4 = 4.")
add_t3_two_step("Solve: 5x - 3 = 22", "x = 5",
                ["x = 5", "x = 19/5", "x = 25", "x = -5"],
                "5x = 22 + 3 = 25; x = 25 / 5 = 5.")
add_t3_two_step("Solve: 6x + 2 = 26", "x = 4",
                ["x = 4", "x = 24/6", "x = 28", "x = -4"],
                "6x = 26 - 2 = 24; x = 24 / 6 = 4.")
add_t3_two_step("Solve: 7x - 4 = 24", "x = 4",
                ["x = 4", "x = 20/7", "x = 28", "x = -4"],
                "7x = 24 + 4 = 28; x = 28 / 7 = 4.")
add_t3_two_step("Solve: 3x + 8 = 23", "x = 5",
                ["x = 5", "x = 15/3", "x = 31", "x = -5"],
                "3x = 23 - 8 = 15; x = 15 / 3 = 5.")
add_t3_two_step("Solve: 4x - 5 = 11", "x = 4",
                ["x = 4", "x = 16/4", "x = 6", "x = -4"],
                "4x = 11 + 5 = 16; x = 16 / 4 = 4.")
add_t3_two_step("Solve: 2x + 9 = 17", "x = 4",
                ["x = 4", "x = 13", "x = 26", "x = -4"],
                "2x = 17 - 9 = 8; x = 8 / 2 = 4.")
add_t3_two_step("Solve: 5x - 6 = 14", "x = 4",
                ["x = 4", "x = 20/5", "x = 8", "x = -4"],
                "5x = 14 + 6 = 20; x = 20 / 5 = 4.")
add_t3_two_step("Solve: 8x + 3 = 27", "x = 3",
                ["x = 3", "x = 24/8", "x = 30", "x = -3"],
                "8x = 27 - 3 = 24; x = 24 / 8 = 3.")
add_t3_two_step("Solve: 9x - 5 = 22", "x = 3",
                ["x = 3", "x = 27/9", "x = 17", "x = -3"],
                "9x = 22 + 5 = 27; x = 27 / 9 = 3.")
add_t3_two_step("Solve: 2x + 11 = 19", "x = 4",
                ["x = 4", "x = 15", "x = 30", "x = -4"],
                "2x = 19 - 11 = 8; x = 8 / 2 = 4.")
add_t3_two_step("Solve: 3x - 7 = 8", "x = 5",
                ["x = 5", "x = 15/3", "x = 1", "x = -5"],
                "3x = 8 + 7 = 15; x = 15 / 3 = 5.")
add_t3_two_step("Solve: 4x + 7 = 31", "x = 6",
                ["x = 6", "x = 24/4", "x = 38", "x = -6"],
                "4x = 31 - 7 = 24; x = 24 / 4 = 6.")
add_t3_two_step("Solve: 6x - 9 = 21", "x = 5",
                ["x = 5", "x = 30/6", "x = 12", "x = -5"],
                "6x = 21 + 9 = 30; x = 30 / 6 = 5.")
add_t3_two_step("Solve: 7x + 2 = 30", "x = 4",
                ["x = 4", "x = 28/7", "x = 32", "x = -4"],
                "7x = 30 - 2 = 28; x = 28 / 7 = 4.")
add_t3_two_step("Solve: 5x + 12 = 27", "x = 3",
                ["x = 3", "x = 15/5", "x = 39", "x = -3"],
                "5x = 27 - 12 = 15; x = 15 / 5 = 3.")
add_t3_two_step("Solve: 2x - 13 = 5", "x = 9",
                ["x = 9", "x = 18/2", "x = -4", "x = -9"],
                "2x = 5 + 13 = 18; x = 18 / 2 = 9.")
add_t3_two_step("Solve: 3x + 14 = 29", "x = 5",
                ["x = 5", "x = 15/3", "x = 43", "x = -5"],
                "3x = 29 - 14 = 15; x = 15 / 3 = 5.")
add_t3_two_step("Solve: x/3 + 1 = 5", "x = 12",
                ["x = 12", "x = 6", "x = 16", "x = 4"],
                "x/3 = 5 - 1 = 4; x = 4 * 3 = 12.")
add_t3_two_step("Solve: x/2 + 3 = 8", "x = 10",
                ["x = 10", "x = 5", "x = 11", "x = 16"],
                "x/2 = 8 - 3 = 5; x = 5 * 2 = 10.")
add_t3_two_step("Solve: x/4 - 2 = 3", "x = 20",
                ["x = 20", "x = 5", "x = -1", "x = 12"],
                "x/4 = 3 + 2 = 5; x = 5 * 4 = 20.")
add_t3_two_step("Solve: x/5 + 4 = 7", "x = 15",
                ["x = 15", "x = 3", "x = 11", "x = 35"],
                "x/5 = 7 - 4 = 3; x = 3 * 5 = 15.")
add_t3_two_step("Solve: x/6 - 1 = 2", "x = 18",
                ["x = 18", "x = 3", "x = -6", "x = 12"],
                "x/6 = 2 + 1 = 3; x = 3 * 6 = 18.")
add_t3_two_step("Solve: x/2 - 5 = 1", "x = 12",
                ["x = 12", "x = 6", "x = -8", "x = 8"],
                "x/2 = 1 + 5 = 6; x = 6 * 2 = 12.")
add_t3_two_step("Solve: x/3 - 4 = 2", "x = 18",
                ["x = 18", "x = 6", "x = -6", "x = 14"],
                "x/3 = 2 + 4 = 6; x = 6 * 3 = 18.")
add_t3_two_step("Solve: x/7 + 2 = 5", "x = 21",
                ["x = 21", "x = 3", "x = 35", "x = 49"],
                "x/7 = 5 - 2 = 3; x = 3 * 7 = 21.")
add_t3_two_step("Solve: 3x + 5 = 14", "x = 3",
                ["x = 3", "x = 9/3", "x = 19", "x = -3"],
                "3x = 14 - 5 = 9; x = 9 / 3 = 3.")
add_t3_two_step("Solve: 4x - 1 = 19", "x = 5",
                ["x = 5", "x = 20/4", "x = 18", "x = -5"],
                "4x = 19 + 1 = 20; x = 20 / 4 = 5.")
add_t3_two_step("Solve: 5x + 7 = 37", "x = 6",
                ["x = 6", "x = 30/5", "x = 44", "x = -6"],
                "5x = 37 - 7 = 30; x = 30 / 5 = 6.")
add_t3_two_step("Solve: 6x - 4 = 32", "x = 6",
                ["x = 6", "x = 36/6", "x = 28", "x = -6"],
                "6x = 32 + 4 = 36; x = 36 / 6 = 6.")
add_t3_two_step("Solve: 7x + 5 = 33", "x = 4",
                ["x = 4", "x = 28/7", "x = 38", "x = -4"],
                "7x = 33 - 5 = 28; x = 28 / 7 = 4.")
add_t3_two_step("Solve: 8x - 6 = 26", "x = 4",
                ["x = 4", "x = 32/8", "x = 20", "x = -4"],
                "8x = 26 + 6 = 32; x = 32 / 8 = 4.")
add_t3_two_step("Solve: 3x - 2 = 13", "x = 5",
                ["x = 5", "x = 15/3", "x = 11", "x = -5"],
                "3x = 13 + 2 = 15; x = 15 / 3 = 5.")
add_t3_two_step("Solve: 9x + 1 = 28", "x = 3",
                ["x = 3", "x = 27/9", "x = 29", "x = -3"],
                "9x = 28 - 1 = 27; x = 27 / 9 = 3.")
add_t3_two_step("Solve: 2x + 4 = 16", "x = 6",
                ["x = 6", "x = 8", "x = 20", "x = -6"],
                "2x = 16 - 4 = 12; x = 12 / 2 = 6.")
add_t3_two_step("Solve: 4x + 11 = 27", "x = 4",
                ["x = 4", "x = 16/4", "x = 38", "x = -4"],
                "4x = 27 - 11 = 16; x = 16 / 4 = 4.")
add_t3_two_step("Solve: 5x - 9 = 11", "x = 4",
                ["x = 4", "x = 20/5", "x = 2", "x = -4"],
                "5x = 11 + 9 = 20; x = 20 / 5 = 4.")
add_t3_two_step("Solve: 6x + 6 = 30", "x = 4",
                ["x = 4", "x = 24/6", "x = 36", "x = -4"],
                "6x = 30 - 6 = 24; x = 24 / 6 = 4.")


def add_t3_inequality(stem: str, answer: str, choices: list[str], walk: str, flip: bool = False) -> None:
    flip_note = (
        " IMPORTANT: flip the inequality sign when multiplying or dividing "
        "by a negative number."
        if flip
        else ""
    )
    T3.append({
        "tier": 3,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Two-step inequality. Solve like an equation, but watch the sign: "
            f"{walk}.{flip_note}"
        ),
        "_pillar": 4,
        "_strategy": "two_step_inequality",
    })


# 15 two-step inequalities (including 5 sign-flips)
add_t3_inequality("Solve: 2x - 3 > 7", "x > 5",
                  ["x > 5", "x > 2", "x < 5", "x > 10"],
                  "2x > 7 + 3 = 10; x > 10 / 2 = 5")
add_t3_inequality("Solve: 3x + 4 < 19", "x < 5",
                  ["x < 5", "x < 15", "x > 5", "x < 23"],
                  "3x < 19 - 4 = 15; x < 15 / 3 = 5")
add_t3_inequality("Solve: 4x - 5 >= 11", "x >= 4",
                  ["x >= 4", "x >= 16", "x <= 4", "x >= 1.5"],
                  "4x >= 11 + 5 = 16; x >= 16 / 4 = 4")
add_t3_inequality("Solve: 5x + 2 <= 17", "x <= 3",
                  ["x <= 3", "x <= 15", "x >= 3", "x <= 19"],
                  "5x <= 17 - 2 = 15; x <= 15 / 5 = 3")
add_t3_inequality("Solve: 2x + 7 > 15", "x > 4",
                  ["x > 4", "x > 11", "x < 4", "x > 8"],
                  "2x > 15 - 7 = 8; x > 8 / 2 = 4")
add_t3_inequality("Solve: 6x - 1 < 23", "x < 4",
                  ["x < 4", "x < 22", "x > 4", "x < 24"],
                  "6x < 23 + 1 = 24; x < 24 / 6 = 4")
add_t3_inequality("Solve: 3x + 6 >= 21", "x >= 5",
                  ["x >= 5", "x >= 15", "x <= 5", "x >= 27"],
                  "3x >= 21 - 6 = 15; x >= 15 / 3 = 5")
add_t3_inequality("Solve: 7x - 4 <= 24", "x <= 4",
                  ["x <= 4", "x <= 28/7", "x >= 4", "x <= 20"],
                  "7x <= 24 + 4 = 28; x <= 28 / 7 = 4")
add_t3_inequality("Solve: 4x + 9 > 25", "x > 4",
                  ["x > 4", "x > 16", "x < 4", "x > 34"],
                  "4x > 25 - 9 = 16; x > 16 / 4 = 4")
add_t3_inequality("Solve: 5x - 2 < 18", "x < 4",
                  ["x < 4", "x < 20", "x > 4", "x < 16"],
                  "5x < 18 + 2 = 20; x < 20 / 5 = 4")
# 5 sign-flips
add_t3_inequality("Solve: -3x + 1 <= 10", "x >= -3",
                  ["x >= -3", "x <= -3", "x >= 3", "x <= 3"],
                  "-3x <= 10 - 1 = 9; divide by -3 and FLIP: x >= 9/(-3) = -3",
                  flip=True)
add_t3_inequality("Solve: -2x - 5 > 1", "x < -3",
                  ["x < -3", "x > -3", "x < 3", "x > 3"],
                  "-2x > 1 + 5 = 6; divide by -2 and FLIP: x < 6/(-2) = -3",
                  flip=True)
add_t3_inequality("Solve: -4x + 3 >= 15", "x <= -3",
                  ["x <= -3", "x >= -3", "x <= 3", "x >= 3"],
                  "-4x >= 15 - 3 = 12; divide by -4 and FLIP: x <= 12/(-4) = -3",
                  flip=True)
add_t3_inequality("Solve: -5x - 7 < 8", "x > -3",
                  ["x > -3", "x < -3", "x > 3", "x < 3"],
                  "-5x < 8 + 7 = 15; divide by -5 and FLIP: x > 15/(-5) = -3",
                  flip=True)
add_t3_inequality("Solve: -x + 4 <= 9", "x >= -5",
                  ["x >= -5", "x <= -5", "x >= 5", "x <= 5"],
                  "-x <= 9 - 4 = 5; multiply by -1 and FLIP: x >= -5",
                  flip=True)


# 15 distribute-then-solve (combined into T3 — counts as "distributing through parens" extra
# plus integrates the two-step solve)
def add_t3_dist_solve(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T3.append({
        "tier": 3,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Distributive property + two-step equation. Distribute first, "
            f"then use inverse operations. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "distribute_then_solve",
    })


add_t3_dist_solve("Solve: 2(x + 3) = 14", "x = 4",
                  ["x = 4", "x = 7", "x = 11", "x = -4"],
                  "2x + 6 = 14; 2x = 8; x = 4.")
add_t3_dist_solve("Solve: 3(x - 2) = 9", "x = 5",
                  ["x = 5", "x = 1", "x = 11", "x = -5"],
                  "3x - 6 = 9; 3x = 15; x = 5.")
add_t3_dist_solve("Solve: 4(x + 1) = 20", "x = 4",
                  ["x = 4", "x = 5", "x = 19", "x = -4"],
                  "4x + 4 = 20; 4x = 16; x = 4.")
add_t3_dist_solve("Solve: 5(x - 3) = 10", "x = 5",
                  ["x = 5", "x = 2", "x = 13", "x = -5"],
                  "5x - 15 = 10; 5x = 25; x = 5.")
add_t3_dist_solve("Solve: 2(x + 5) = 18", "x = 4",
                  ["x = 4", "x = 9", "x = 13", "x = -4"],
                  "2x + 10 = 18; 2x = 8; x = 4.")
add_t3_dist_solve("Solve: 6(x - 1) = 24", "x = 5",
                  ["x = 5", "x = 4", "x = 25", "x = -5"],
                  "6x - 6 = 24; 6x = 30; x = 5.")
add_t3_dist_solve("Solve: 3(2x + 1) = 21", "x = 10/3",
                  ["x = 10/3", "x = 7", "x = 3", "x = 20"],
                  "6x + 3 = 21; 6x = 18; x = 3. Wait — check: 3(2*3 + 1) = 3*7 = 21. So x = 3.")
add_t3_dist_solve("Solve: 4(x - 2) = 12", "x = 5",
                  ["x = 5", "x = 3", "x = 14", "x = -5"],
                  "4x - 8 = 12; 4x = 20; x = 5.")
add_t3_dist_solve("Solve: 5(x + 2) = 25", "x = 3",
                  ["x = 3", "x = 5", "x = 23", "x = -3"],
                  "5x + 10 = 25; 5x = 15; x = 3.")
add_t3_dist_solve("Solve: 7(x - 1) = 14", "x = 3",
                  ["x = 3", "x = 2", "x = 15", "x = -3"],
                  "7x - 7 = 14; 7x = 21; x = 3.")
add_t3_dist_solve("Solve: 2(x - 4) = 6", "x = 7",
                  ["x = 7", "x = 3", "x = 10", "x = -7"],
                  "2x - 8 = 6; 2x = 14; x = 7.")
add_t3_dist_solve("Solve: 3(x + 4) = 18", "x = 2",
                  ["x = 2", "x = 6", "x = 14", "x = -2"],
                  "3x + 12 = 18; 3x = 6; x = 2.")
add_t3_dist_solve("Solve: 4(x + 3) = 28", "x = 4",
                  ["x = 4", "x = 7", "x = 25", "x = -4"],
                  "4x + 12 = 28; 4x = 16; x = 4.")
add_t3_dist_solve("Solve: 5(x - 4) = 15", "x = 7",
                  ["x = 7", "x = 3", "x = 19", "x = -7"],
                  "5x - 20 = 15; 5x = 35; x = 7.")
add_t3_dist_solve("Solve: 6(x + 2) = 30", "x = 3",
                  ["x = 3", "x = 5", "x = 28", "x = -3"],
                  "6x + 12 = 30; 6x = 18; x = 3.")


# Fix the one bad question above (3(2x+1) = 21 → x = 3, not 10/3)
# Remove and re-add
T3 = [q for q in T3 if not (q.get("question") == "Solve: 3(2x + 1) = 21")]
add_t3_dist_solve("Solve: 3(2x + 1) = 21", "x = 10/3",
                  ["x = 10/3", "x = 11/3", "x = 7", "x = 3"],
                  "Actually: 3(2x + 1) = 6x + 3 = 21; 6x = 18; x = 3. Let me redo properly.")
# Re-fix
T3 = [q for q in T3 if not (q.get("question") == "Solve: 3(2x + 1) = 21")]
add_t3_dist_solve("Solve: 3(2x - 1) = 15", "x = 3",
                  ["x = 3", "x = 5", "x = 8", "x = -3"],
                  "6x - 3 = 15; 6x = 18; x = 3.")


# ============================================================================
# TIER 4 — 100 questions
# Stem cap 220, budget 750
# ============================================================================

T4: list[dict] = []


def add_t4_solve_linear(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T4.append({
        "tier": 4,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Solving a linear equation. Use inverse operations: combine like "
            f"terms or distribute first, then isolate x. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "solve_linear",
    })


# 15 solve-linear (more complex)
add_t4_solve_linear("Solve: 4x - 7 = 13", "x = 5",
                    ["x = 5", "x = 20/4", "x = 3/2", "x = -5"],
                    "4x = 20; x = 5.")
add_t4_solve_linear("Solve: 5x + 3 = 2x + 12", "x = 3",
                    ["x = 3", "x = 5", "x = 9", "x = -3"],
                    "5x - 2x = 12 - 3; 3x = 9; x = 3.")
add_t4_solve_linear("Solve: 7x - 4 = 3x + 16", "x = 5",
                    ["x = 5", "x = 4", "x = 20/4", "x = -5"],
                    "7x - 3x = 16 + 4; 4x = 20; x = 5.")
add_t4_solve_linear("Solve: 6x + 1 = 2x + 17", "x = 4",
                    ["x = 4", "x = 16/4", "x = 18", "x = -4"],
                    "6x - 2x = 17 - 1; 4x = 16; x = 4.")
add_t4_solve_linear("Solve: 3(x + 2) = 21", "x = 5",
                    ["x = 5", "x = 7", "x = 19", "x = -5"],
                    "Distribute: 3x + 6 = 21; 3x = 15; x = 5. Or divide both sides by 3 first: x + 2 = 7; x = 5.")
add_t4_solve_linear("Solve: 2(x - 3) = x + 1", "x = 7",
                    ["x = 7", "x = 5", "x = -1", "x = 1"],
                    "2x - 6 = x + 1; 2x - x = 1 + 6; x = 7.")
add_t4_solve_linear("Solve: 5x - 8 = 3x + 6", "x = 7",
                    ["x = 7", "x = 14/2", "x = 2", "x = -7"],
                    "5x - 3x = 6 + 8; 2x = 14; x = 7.")
add_t4_solve_linear("Solve: 4(x - 1) = 2x + 6", "x = 5",
                    ["x = 5", "x = 10/2", "x = 7", "x = -5"],
                    "4x - 4 = 2x + 6; 2x = 10; x = 5.")
add_t4_solve_linear("Solve: 3x + 7 = 5x - 1", "x = 4",
                    ["x = 4", "x = 8/2", "x = 6", "x = -4"],
                    "7 + 1 = 5x - 3x; 8 = 2x; x = 4.")
add_t4_solve_linear("Solve: 6x - 11 = 4x + 9", "x = 10",
                    ["x = 10", "x = 20/2", "x = -1", "x = 2"],
                    "6x - 4x = 9 + 11; 2x = 20; x = 10.")
add_t4_solve_linear("Solve: 2(3x + 1) = 4x + 10", "x = 4",
                    ["x = 4", "x = 8/2", "x = 6", "x = -4"],
                    "6x + 2 = 4x + 10; 2x = 8; x = 4.")
add_t4_solve_linear("Solve: 5(x - 2) = 3x + 4", "x = 7",
                    ["x = 7", "x = 14/2", "x = 6", "x = -7"],
                    "5x - 10 = 3x + 4; 2x = 14; x = 7.")
add_t4_solve_linear("Solve: 8x - 5 = 5x + 13", "x = 6",
                    ["x = 6", "x = 18/3", "x = 8", "x = -6"],
                    "8x - 5x = 13 + 5; 3x = 18; x = 6.")
add_t4_solve_linear("Solve: 7x + 2 = 4x + 17", "x = 5",
                    ["x = 5", "x = 15/3", "x = 19", "x = -5"],
                    "7x - 4x = 17 - 2; 3x = 15; x = 5.")
add_t4_solve_linear("Solve: 9x - 4 = 6x + 11", "x = 5",
                    ["x = 5", "x = 15/3", "x = 7", "x = -5"],
                    "9x - 6x = 11 + 4; 3x = 15; x = 5.")


def add_t4_slope(p1: tuple, p2: tuple, answer: str, choices: list[str]) -> None:
    x1, y1 = p1
    x2, y2 = p2
    T4.append({
        "tier": 4,
        "question": f"Find the slope of the line through ({x1}, {y1}) and ({x2}, {y2}).",
        "answer": answer,
        "choices": choices,
        "context": (
            f"Slope formula: m = (y2 - y1) / (x2 - x1) = rise over run. "
            f"Here m = ({y2} - {y1}) / ({x2} - {x1}) = {y2-y1}/{x2-x1} = "
            f"{answer}. Slope = how much y changes per unit change in x."
        ),
        "_pillar": 4,
        "_strategy": "slope_from_points",
    })


# 20 slope-from-points
add_t4_slope((1, 3), (4, 9), "2", ["2", "3", "1/2", "6"])
add_t4_slope((2, 1), (5, 7), "2", ["2", "3", "1/2", "6"])
add_t4_slope((0, 0), (3, 6), "2", ["2", "3", "1/2", "6"])
add_t4_slope((1, 2), (4, 11), "3", ["3", "2", "1/3", "9"])
add_t4_slope((2, 3), (5, 12), "3", ["3", "2", "1/3", "9"])
add_t4_slope((0, 1), (2, 9), "4", ["4", "3", "1/4", "8"])
add_t4_slope((1, 5), (3, 13), "4", ["4", "3", "1/4", "8"])
add_t4_slope((0, 0), (5, 25), "5", ["5", "4", "1/5", "20"])
add_t4_slope((1, 2), (3, 12), "5", ["5", "4", "1/5", "10"])
add_t4_slope((2, 4), (4, 8), "2", ["2", "1", "1/2", "4"])
add_t4_slope((1, 10), (3, 4), "-3", ["-3", "3", "-1/3", "-6"])
add_t4_slope((0, 8), (4, 0), "-2", ["-2", "2", "-1/2", "-4"])
add_t4_slope((2, 7), (5, 1), "-2", ["-2", "2", "-1/2", "-6"])
add_t4_slope((1, 6), (4, 0), "-2", ["-2", "2", "-1/2", "-3"])
add_t4_slope((0, 5), (2, 1), "-2", ["-2", "2", "-1/2", "-4"])
add_t4_slope((3, 1), (1, 5), "-2", ["-2", "2", "-1/2", "-4"])
add_t4_slope((2, 6), (8, 9), "1/2", ["1/2", "2", "3/6", "1/3"])
add_t4_slope((1, 2), (5, 4), "1/2", ["1/2", "2", "2/4", "1/3"])
add_t4_slope((0, 3), (6, 6), "1/2", ["1/2", "2", "3/6", "1/3"])
add_t4_slope((2, 1), (8, 4), "1/2", ["1/2", "2", "3/6", "1/3"])


def add_t4_slope_intercept(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T4.append({
        "tier": 4,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Slope-intercept form: y = mx + b, where m is the slope and b "
            f"is the y-intercept (where the line crosses the y-axis). {walk}"
        ),
        "_pillar": 4,
        "_strategy": "slope_intercept",
    })


# 15 slope-intercept questions
add_t4_slope_intercept("Slope 2, y-intercept 3. Equation of line?", "y = 2x + 3",
                       ["y = 2x + 3", "y = 3x + 2", "y = 2 + 3x", "y = 2x - 3"],
                       "Plug m = 2 and b = 3 into y = mx + b: y = 2x + 3.")
add_t4_slope_intercept("Slope 4, y-intercept -1. Equation of line?", "y = 4x - 1",
                       ["y = 4x - 1", "y = -x + 4", "y = 4 - x", "y = 4x + 1"],
                       "y = mx + b with m = 4, b = -1: y = 4x - 1.")
add_t4_slope_intercept("Slope -3, y-intercept 5. Equation of line?", "y = -3x + 5",
                       ["y = -3x + 5", "y = 5x - 3", "y = 3x + 5", "y = -3x - 5"],
                       "y = mx + b with m = -3, b = 5: y = -3x + 5.")
add_t4_slope_intercept("Slope 1, y-intercept -4. Equation of line?", "y = x - 4",
                       ["y = x - 4", "y = -4x + 1", "y = 4 - x", "y = x + 4"],
                       "y = mx + b with m = 1, b = -4: y = x - 4.")
add_t4_slope_intercept("Slope -2, y-intercept 0. Equation of line?", "y = -2x",
                       ["y = -2x", "y = 2x", "y = -2", "y = -x - 2"],
                       "y = mx + b with m = -2, b = 0: y = -2x. Line through the origin.")
add_t4_slope_intercept("Identify slope of: y = 5x - 7.", "5",
                       ["5", "-7", "-5", "7"],
                       "Equation is in slope-intercept form y = mx + b. The coefficient of x is the slope: m = 5.")
add_t4_slope_intercept("Identify y-intercept of: y = 3x + 8.", "8",
                       ["8", "3", "-8", "-3"],
                       "In y = mx + b, the constant term b is the y-intercept. Here b = 8.")
add_t4_slope_intercept("Identify slope of: y = -4x + 2.", "-4",
                       ["-4", "2", "4", "-2"],
                       "Slope is the coefficient of x in y = mx + b. Here m = -4.")
add_t4_slope_intercept("Identify y-intercept of: y = 7x - 3.", "-3",
                       ["-3", "7", "3", "-7"],
                       "y-intercept is b in y = mx + b. Here b = -3.")
add_t4_slope_intercept("Slope 1/2, y-intercept 1. Equation of line?", "y = (1/2)x + 1",
                       ["y = (1/2)x + 1", "y = x + 1/2", "y = 2x + 1", "y = (1/2)x - 1"],
                       "y = mx + b with m = 1/2, b = 1: y = (1/2)x + 1.")
add_t4_slope_intercept("Identify slope of: y = -x + 6.", "-1",
                       ["-1", "6", "1", "-6"],
                       "When x has no visible coefficient and a negative sign, m = -1.")
add_t4_slope_intercept("Identify slope of: y = 2x.", "2",
                       ["2", "0", "-2", "1/2"],
                       "y = 2x is y = 2x + 0; m = 2, b = 0 (line through origin).")
add_t4_slope_intercept("Slope 6, y-intercept -2. Equation of line?", "y = 6x - 2",
                       ["y = 6x - 2", "y = -2x + 6", "y = 6 - 2x", "y = 6x + 2"],
                       "y = mx + b with m = 6, b = -2: y = 6x - 2.")
add_t4_slope_intercept("Identify y-intercept of: y = -2x - 5.", "-5",
                       ["-5", "-2", "5", "2"],
                       "y-intercept is b. Here b = -5.")
add_t4_slope_intercept("Slope -1/3, y-intercept 4. Equation of line?", "y = -(1/3)x + 4",
                       ["y = -(1/3)x + 4", "y = 4x - 1/3", "y = (1/3)x + 4", "y = -3x + 4"],
                       "y = mx + b with m = -1/3, b = 4: y = -(1/3)x + 4.")


def add_t4_system_sub(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T4.append({
        "tier": 4,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"System of equations by substitution. Replace one variable "
            f"using one equation, then solve the other. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "system_substitution",
    })


# 10 systems-by-substitution
add_t4_system_sub("Solve: y = 2x + 1 and y = x + 3. Find (x, y).", "(2, 5)",
                  ["(2, 5)", "(1, 3)", "(3, 7)", "(4, 9)"],
                  "Set equal: 2x + 1 = x + 3; x = 2. Then y = 2 + 3 = 5.")
add_t4_system_sub("Solve: y = 3x - 2 and y = x + 4. Find (x, y).", "(3, 7)",
                  ["(3, 7)", "(1, 5)", "(2, 4)", "(4, 8)"],
                  "Set equal: 3x - 2 = x + 4; 2x = 6; x = 3. Then y = 3 + 4 = 7.")
add_t4_system_sub("Solve: y = x + 5 and y = 2x + 1. Find (x, y).", "(4, 9)",
                  ["(4, 9)", "(1, 6)", "(2, 5)", "(5, 10)"],
                  "Set equal: x + 5 = 2x + 1; 4 = x. Then y = 4 + 5 = 9.")
add_t4_system_sub("Solve: y = 4x - 3 and y = 2x + 5. Find (x, y).", "(4, 13)",
                  ["(4, 13)", "(2, 5)", "(1, 1)", "(3, 9)"],
                  "Set equal: 4x - 3 = 2x + 5; 2x = 8; x = 4. Then y = 2*4 + 5 = 13.")
add_t4_system_sub("Solve: y = x - 1 and y = 3x - 7. Find (x, y).", "(3, 2)",
                  ["(3, 2)", "(2, 1)", "(1, 0)", "(4, 3)"],
                  "Set equal: x - 1 = 3x - 7; 6 = 2x; x = 3. Then y = 3 - 1 = 2.")
add_t4_system_sub("Solve: y = 2x and y = x + 4. Find (x, y).", "(4, 8)",
                  ["(4, 8)", "(2, 4)", "(1, 5)", "(8, 16)"],
                  "Set equal: 2x = x + 4; x = 4. Then y = 2*4 = 8.")
add_t4_system_sub("Solve: y = 5x + 2 and y = 3x + 8. Find (x, y).", "(3, 17)",
                  ["(3, 17)", "(2, 14)", "(1, 11)", "(4, 22)"],
                  "Set equal: 5x + 2 = 3x + 8; 2x = 6; x = 3. Then y = 5*3 + 2 = 17.")
add_t4_system_sub("Solve: y = x + 7 and y = 2x + 4. Find (x, y).", "(3, 10)",
                  ["(3, 10)", "(2, 8)", "(1, 6)", "(4, 12)"],
                  "Set equal: x + 7 = 2x + 4; 3 = x. Then y = 3 + 7 = 10.")
add_t4_system_sub("Solve: y = 6x - 1 and y = 4x + 3. Find (x, y).", "(2, 11)",
                  ["(2, 11)", "(1, 5)", "(3, 15)", "(4, 19)"],
                  "Set equal: 6x - 1 = 4x + 3; 2x = 4; x = 2. Then y = 4*2 + 3 = 11.")
add_t4_system_sub("Solve: y = 3x + 1 and y = x + 5. Find (x, y).", "(2, 7)",
                  ["(2, 7)", "(1, 4)", "(3, 10)", "(4, 13)"],
                  "Set equal: 3x + 1 = x + 5; 2x = 4; x = 2. Then y = 2 + 5 = 7.")


def add_t4_system_elim(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T4.append({
        "tier": 4,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"System of equations by elimination. Add or subtract equations "
            f"to cancel a variable, then solve. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "system_elimination",
    })


# 10 systems-by-elimination
add_t4_system_elim("Solve: 2x + y = 7 and x - y = 2. Find x.", "3",
                   ["3", "2", "4", "1"],
                   "Add equations: 3x = 9; x = 3.")
add_t4_system_elim("Solve: x + y = 10 and x - y = 4. Find x.", "7",
                   ["7", "3", "5", "14"],
                   "Add equations: 2x = 14; x = 7.")
add_t4_system_elim("Solve: 3x + y = 11 and x - y = 1. Find x.", "3",
                   ["3", "2", "4", "5"],
                   "Add equations: 4x = 12; x = 3.")
add_t4_system_elim("Solve: x + 2y = 8 and x - 2y = 0. Find x.", "4",
                   ["4", "2", "6", "8"],
                   "Add equations: 2x = 8; x = 4.")
add_t4_system_elim("Solve: 2x + 3y = 13 and 2x - y = 5. Find y.", "2",
                   ["2", "3", "4", "5"],
                   "Subtract: 4y = 8; y = 2.")
add_t4_system_elim("Solve: 4x + y = 14 and x + y = 5. Find x.", "3",
                   ["3", "2", "4", "9"],
                   "Subtract: 3x = 9; x = 3.")
add_t4_system_elim("Solve: 5x + 2y = 16 and 3x + 2y = 12. Find x.", "2",
                   ["2", "1", "3", "4"],
                   "Subtract: 2x = 4; x = 2.")
add_t4_system_elim("Solve: x + y = 12 and 2x - y = 6. Find x.", "6",
                   ["6", "5", "7", "18"],
                   "Add equations: 3x = 18; x = 6.")
add_t4_system_elim("Solve: 3x + 2y = 12 and x - 2y = 4. Find x.", "4",
                   ["4", "3", "5", "16"],
                   "Add equations: 4x = 16; x = 4.")
add_t4_system_elim("Solve: 2x + y = 9 and 2x - y = 1. Find y.", "4",
                   ["4", "3", "5", "10"],
                   "Subtract: 2y = 8; y = 4.")


def add_t4_exponent(stem: str, answer: str, choices: list[str], rule: str, walk: str) -> None:
    T4.append({
        "tier": 4,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Exponent rule: {rule}. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "exponent_rules",
    })


# 15 exponent-rule questions
add_t4_exponent("Simplify: x^3 * x^5", "x^8",
                ["x^8", "x^15", "x^2", "2x^8"],
                "x^a * x^b = x^(a+b)",
                "x^3 * x^5 = x^(3+5) = x^8. When multiplying same-base, add exponents.")
add_t4_exponent("Simplify: y^4 * y^2", "y^6",
                ["y^6", "y^8", "y^2", "2y^6"],
                "x^a * x^b = x^(a+b)",
                "y^4 * y^2 = y^(4+2) = y^6.")
add_t4_exponent("Simplify: (x^2)^3", "x^6",
                ["x^6", "x^5", "x^8", "3x^2"],
                "(x^a)^b = x^(a*b) — power rule",
                "(x^2)^3 = x^(2*3) = x^6. When raising a power to a power, multiply exponents.")
add_t4_exponent("Simplify: (a^3)^4", "a^12",
                ["a^12", "a^7", "a^81", "4a^3"],
                "(x^a)^b = x^(a*b) — power rule",
                "(a^3)^4 = a^(3*4) = a^12.")
add_t4_exponent("Simplify: x^0 (where x is nonzero)", "1",
                ["1", "0", "x", "x^1"],
                "x^0 = 1 for any nonzero x",
                "Anything (nonzero) to the 0 power equals 1. This is a definition that makes the exponent rules consistent.")
add_t4_exponent("Simplify: x^(-2)", "1/x^2",
                ["1/x^2", "-x^2", "x^2", "-2x"],
                "x^(-n) = 1/x^n — negative exponent",
                "A negative exponent flips the base to the denominator: x^(-2) = 1/x^2.")
add_t4_exponent("Simplify: x^5 / x^2", "x^3",
                ["x^3", "x^7", "x^2.5", "x^10"],
                "x^a / x^b = x^(a-b)",
                "When dividing same-base, subtract exponents: x^5 / x^2 = x^(5-2) = x^3.")
add_t4_exponent("Simplify: y^7 / y^3", "y^4",
                ["y^4", "y^10", "y^21", "y^2"],
                "x^a / x^b = x^(a-b)",
                "y^7 / y^3 = y^(7-3) = y^4.")
add_t4_exponent("Simplify: (xy)^3", "x^3 y^3",
                ["x^3 y^3", "xy^3", "x^3 y", "3xy"],
                "(xy)^n = x^n * y^n — power of a product",
                "Each factor inside the parens gets the exponent: (xy)^3 = x^3 * y^3.")
add_t4_exponent("Simplify: 2^4 * 2^2", "2^6",
                ["2^6", "2^8", "4^6", "16"],
                "x^a * x^b = x^(a+b)",
                "Same base 2: 2^4 * 2^2 = 2^(4+2) = 2^6 = 64.")
add_t4_exponent("Simplify: 3^5 / 3^2", "3^3",
                ["3^3", "3^7", "3^2.5", "1^3"],
                "x^a / x^b = x^(a-b)",
                "3^5 / 3^2 = 3^(5-2) = 3^3 = 27.")
add_t4_exponent("Simplify: (x^4)^2", "x^8",
                ["x^8", "x^6", "x^16", "2x^4"],
                "(x^a)^b = x^(a*b)",
                "(x^4)^2 = x^(4*2) = x^8.")
add_t4_exponent("Simplify: x^(-3)", "1/x^3",
                ["1/x^3", "-x^3", "x^3", "-3x"],
                "x^(-n) = 1/x^n",
                "Negative exponent: x^(-3) = 1/x^3.")
add_t4_exponent("Simplify: a^6 * a", "a^7",
                ["a^7", "a^6", "a^61", "2a^7"],
                "x^a * x^b = x^(a+b); recall x = x^1",
                "a is a^1; a^6 * a^1 = a^(6+1) = a^7.")
add_t4_exponent("Simplify: y^9 / y^4", "y^5",
                ["y^5", "y^13", "y^36", "y^2.25"],
                "x^a / x^b = x^(a-b)",
                "y^9 / y^4 = y^(9-4) = y^5.")


def add_t4_sci_notation(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T4.append({
        "tier": 4,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Scientific notation: write a number as a × 10^n, where 1 <= "
            f"|a| < 10 and n is an integer. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "scientific_notation",
    })


# 10 scientific-notation questions
add_t4_sci_notation("Write 4,500,000 in scientific notation.", "4.5 × 10^6",
                    ["4.5 × 10^6", "4.5 × 10^5", "45 × 10^5", "4.5 × 10^7"],
                    "Move the decimal 6 places left: 4500000 → 4.5; n = 6. Answer: 4.5 × 10^6.")
add_t4_sci_notation("Write 3,200,000 in scientific notation.", "3.2 × 10^6",
                    ["3.2 × 10^6", "3.2 × 10^5", "32 × 10^5", "3.2 × 10^7"],
                    "Move decimal 6 places left: 3200000 → 3.2; n = 6.")
add_t4_sci_notation("Write 78,000 in scientific notation.", "7.8 × 10^4",
                    ["7.8 × 10^4", "7.8 × 10^3", "78 × 10^3", "7.8 × 10^5"],
                    "Move decimal 4 places left: 78000 → 7.8; n = 4.")
add_t4_sci_notation("Write 0.00056 in scientific notation.", "5.6 × 10^(-4)",
                    ["5.6 × 10^(-4)", "5.6 × 10^4", "56 × 10^(-5)", "5.6 × 10^(-3)"],
                    "Move decimal 4 places right (number is small, so exponent negative): 0.00056 → 5.6; n = -4.")
add_t4_sci_notation("Write 0.0029 in scientific notation.", "2.9 × 10^(-3)",
                    ["2.9 × 10^(-3)", "2.9 × 10^3", "29 × 10^(-4)", "2.9 × 10^(-2)"],
                    "Move decimal 3 places right: 0.0029 → 2.9; n = -3.")
add_t4_sci_notation("Write 1,200,000,000 in scientific notation.", "1.2 × 10^9",
                    ["1.2 × 10^9", "1.2 × 10^8", "12 × 10^8", "1.2 × 10^10"],
                    "Move decimal 9 places left: 1200000000 → 1.2; n = 9.")
add_t4_sci_notation("Write 0.000007 in scientific notation.", "7 × 10^(-6)",
                    ["7 × 10^(-6)", "7 × 10^6", "70 × 10^(-7)", "7 × 10^(-5)"],
                    "Move decimal 6 places right: 0.000007 → 7; n = -6.")
add_t4_sci_notation("Write 650,000 in scientific notation.", "6.5 × 10^5",
                    ["6.5 × 10^5", "6.5 × 10^4", "65 × 10^4", "6.5 × 10^6"],
                    "Move decimal 5 places left: 650000 → 6.5; n = 5.")
add_t4_sci_notation("Write 0.04 in scientific notation.", "4 × 10^(-2)",
                    ["4 × 10^(-2)", "4 × 10^2", "40 × 10^(-3)", "4 × 10^(-1)"],
                    "Move decimal 2 places right: 0.04 → 4; n = -2.")
add_t4_sci_notation("Write 8,900,000 in scientific notation.", "8.9 × 10^6",
                    ["8.9 × 10^6", "8.9 × 10^5", "89 × 10^5", "8.9 × 10^7"],
                    "Move decimal 6 places left: 8900000 → 8.9; n = 6.")


def add_t4_sqrt(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T4.append({
        "tier": 4,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Square root simplification: factor out perfect squares from "
            f"under the radical. √(a²b) = a√b. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "sqrt_simplify",
    })


# 10 square-root simplification questions
add_t4_sqrt("Simplify: √48", "4√3",
            ["4√3", "6√2", "4√12", "48"],
            "48 = 16 * 3, and √16 = 4. So √48 = √16 * √3 = 4√3.")
add_t4_sqrt("Simplify: √72", "6√2",
            ["6√2", "4√6", "8√9", "72"],
            "72 = 36 * 2, and √36 = 6. So √72 = 6√2.")
add_t4_sqrt("Simplify: √50", "5√2",
            ["5√2", "2√5", "25√2", "50"],
            "50 = 25 * 2, and √25 = 5. So √50 = 5√2.")
add_t4_sqrt("Simplify: √32", "4√2",
            ["4√2", "2√8", "8√2", "32"],
            "32 = 16 * 2, and √16 = 4. So √32 = 4√2.")
add_t4_sqrt("Simplify: √18", "3√2",
            ["3√2", "2√3", "9√2", "18"],
            "18 = 9 * 2, and √9 = 3. So √18 = 3√2.")
add_t4_sqrt("Simplify: √45", "3√5",
            ["3√5", "5√3", "9√5", "45"],
            "45 = 9 * 5, and √9 = 3. So √45 = 3√5.")
add_t4_sqrt("Simplify: √98", "7√2",
            ["7√2", "2√7", "49√2", "98"],
            "98 = 49 * 2, and √49 = 7. So √98 = 7√2.")
add_t4_sqrt("Simplify: √75", "5√3",
            ["5√3", "3√5", "25√3", "75"],
            "75 = 25 * 3, and √25 = 5. So √75 = 5√3.")
add_t4_sqrt("Simplify: √200", "10√2",
            ["10√2", "2√10", "100√2", "200"],
            "200 = 100 * 2, and √100 = 10. So √200 = 10√2.")
add_t4_sqrt("Simplify: √80", "4√5",
            ["4√5", "5√4", "16√5", "80"],
            "80 = 16 * 5, and √16 = 4. So √80 = 4√5.")


def add_t4_function_eval(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T4.append({
        "tier": 4,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Function notation: f(x) is read 'f of x'. To evaluate f at a "
            f"value, substitute that value for x in the formula. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "function_notation",
    })


# 10 function-notation questions
add_t4_function_eval("If f(x) = 2x + 3, what is f(5)?", "13",
                     ["13", "10", "16", "8"],
                     "f(5) = 2*5 + 3 = 10 + 3 = 13.")
add_t4_function_eval("If f(x) = 3x - 4, what is f(2)?", "2",
                     ["2", "10", "-2", "6"],
                     "f(2) = 3*2 - 4 = 6 - 4 = 2.")
add_t4_function_eval("If f(x) = x + 7, what is f(0)?", "7",
                     ["7", "0", "1", "8"],
                     "f(0) = 0 + 7 = 7. f(0) is the y-intercept.")
add_t4_function_eval("If f(x) = 4x, what is f(3)?", "12",
                     ["12", "7", "4", "9"],
                     "f(3) = 4*3 = 12.")
add_t4_function_eval("If f(x) = 5x - 2, what is f(4)?", "18",
                     ["18", "20", "10", "22"],
                     "f(4) = 5*4 - 2 = 20 - 2 = 18.")
add_t4_function_eval("If f(x) = x^2, what is f(6)?", "36",
                     ["36", "12", "64", "30"],
                     "f(6) = 6^2 = 36.")
add_t4_function_eval("If f(x) = 2x + 1, what is f(-3)?", "-5",
                     ["-5", "5", "7", "-7"],
                     "f(-3) = 2*(-3) + 1 = -6 + 1 = -5.")
add_t4_function_eval("If f(x) = x^2 + 1, what is f(3)?", "10",
                     ["10", "7", "9", "13"],
                     "f(3) = 3^2 + 1 = 9 + 1 = 10.")
add_t4_function_eval("If f(x) = -x + 4, what is f(2)?", "2",
                     ["2", "6", "-2", "4"],
                     "f(2) = -2 + 4 = 2.")
add_t4_function_eval("If f(x) = 3x - 1, what is f(0)?", "-1",
                     ["-1", "0", "3", "1"],
                     "f(0) = 3*0 - 1 = -1. f(0) is the y-intercept.")


# ============================================================================
# TIER 5 — 100 questions
# Stem cap 280, budget 900
# CRITICAL: For quadratic answers "x = a or x = b", use ASCII "-" not "−"
# ============================================================================

T5: list[dict] = []


def add_t5_poly_addsub(stem: str, answer: str, choices: list[str], walk: str, kind: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Polynomial {kind}. Combining like terms — terms with the same "
            f"variable AND same exponent are like terms. {walk}"
        ),
        "_pillar": 4,
        "_strategy": f"polynomial_{kind}",
    })


# 10 polynomial add/subtract
add_t5_poly_addsub("Simplify: (2x² + 3x - 1) + (x² - 4x + 5)", "3x² - x + 4",
                   ["3x² - x + 4", "3x² + 7x + 4", "3x² - x - 6", "2x² - x + 4"],
                   "(2x² + x²) + (3x - 4x) + (-1 + 5) = 3x² - x + 4.", "addition")
add_t5_poly_addsub("Simplify: (5x² - 2x + 7) + (3x² + 6x - 4)", "8x² + 4x + 3",
                   ["8x² + 4x + 3", "8x² - 4x + 11", "8x² + 4x + 11", "8x² + 8x + 3"],
                   "(5x² + 3x²) + (-2x + 6x) + (7 - 4) = 8x² + 4x + 3.", "addition")
add_t5_poly_addsub("Simplify: (4x² + x - 3) + (2x² + 5x + 8)", "6x² + 6x + 5",
                   ["6x² + 6x + 5", "6x² + 6x - 11", "6x² - 6x + 5", "8x² + 6x + 5"],
                   "(4x² + 2x²) + (x + 5x) + (-3 + 8) = 6x² + 6x + 5.", "addition")
add_t5_poly_addsub("Simplify: (3x² + 2x + 1) - (x² + x + 4)", "2x² + x - 3",
                   ["2x² + x - 3", "2x² + x + 5", "2x² + 3x + 5", "3x² + x - 3"],
                   "Distribute the minus: (3x² + 2x + 1) - x² - x - 4 = (3x² - x²) + (2x - x) + (1 - 4) = 2x² + x - 3.", "subtraction")
add_t5_poly_addsub("Simplify: (6x² - 3x + 5) - (2x² + x - 2)", "4x² - 4x + 7",
                   ["4x² - 4x + 7", "4x² - 2x + 3", "4x² - 4x + 3", "8x² - 4x + 7"],
                   "Distribute minus: (6x² - 3x + 5) - 2x² - x + 2 = 4x² - 4x + 7.", "subtraction")
add_t5_poly_addsub("Simplify: (4x² + 7x - 1) - (x² + 2x + 3)", "3x² + 5x - 4",
                   ["3x² + 5x - 4", "3x² + 5x + 2", "3x² + 9x - 4", "5x² + 5x - 4"],
                   "Distribute minus: (4x² + 7x - 1) - x² - 2x - 3 = 3x² + 5x - 4.", "subtraction")
add_t5_poly_addsub("Simplify: (x² + 3x + 2) + (4x² - x - 6)", "5x² + 2x - 4",
                   ["5x² + 2x - 4", "5x² + 4x - 4", "5x² + 2x + 8", "4x² + 2x - 4"],
                   "(x² + 4x²) + (3x - x) + (2 - 6) = 5x² + 2x - 4.", "addition")
add_t5_poly_addsub("Simplify: (7x² - 5x + 2) - (3x² - 2x + 1)", "4x² - 3x + 1",
                   ["4x² - 3x + 1", "4x² - 7x + 1", "4x² - 3x + 3", "10x² - 3x + 1"],
                   "Distribute minus: (7x² - 5x + 2) - 3x² + 2x - 1 = 4x² - 3x + 1.", "subtraction")
add_t5_poly_addsub("Simplify: (2x² + x) + (3x² + 4x - 5)", "5x² + 5x - 5",
                   ["5x² + 5x - 5", "5x² + 5x + 5", "5x² + 4x - 5", "6x² + 5x - 5"],
                   "(2x² + 3x²) + (x + 4x) + (0 + (-5)) = 5x² + 5x - 5.", "addition")
add_t5_poly_addsub("Simplify: (5x² - 4) - (2x² + 3)", "3x² - 7",
                   ["3x² - 7", "3x² - 1", "3x² + 7", "7x² - 7"],
                   "Distribute minus: 5x² - 4 - 2x² - 3 = 3x² - 7.", "subtraction")


def add_t5_poly_multiply(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Polynomial multiplication. Distribute every term of the first "
            f"polynomial to every term of the second, then combine like "
            f"terms. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "polynomial_multiply",
    })


# 10 polynomial multiply (NOT FOIL — degree > 2)
add_t5_poly_multiply("Expand: (x + 2)(x² - 3x + 1)", "x³ - x² - 5x + 2",
                     ["x³ - x² - 5x + 2", "x³ + x² - 5x + 2", "x³ - x² + 5x + 2", "x³ - 5x + 2"],
                     "x*(x² - 3x + 1) + 2*(x² - 3x + 1) = (x³ - 3x² + x) + (2x² - 6x + 2) = x³ - x² - 5x + 2.")
add_t5_poly_multiply("Expand: (x - 1)(x² + 2x + 3)", "x³ + x² + x - 3",
                     ["x³ + x² + x - 3", "x³ + 3x² + 5x + 3", "x³ - x² - x - 3", "x³ + x² + x + 3"],
                     "x*(x² + 2x + 3) - 1*(x² + 2x + 3) = (x³ + 2x² + 3x) - (x² + 2x + 3) = x³ + x² + x - 3.")
add_t5_poly_multiply("Expand: (x + 3)(x² + x - 2)", "x³ + 4x² + x - 6",
                     ["x³ + 4x² + x - 6", "x³ + 4x² + 5x - 6", "x³ + x² - 6", "x³ + 2x² + x - 6"],
                     "x*(x² + x - 2) + 3*(x² + x - 2) = (x³ + x² - 2x) + (3x² + 3x - 6) = x³ + 4x² + x - 6.")
add_t5_poly_multiply("Expand: (x - 2)(x² + 4x - 1)", "x³ + 2x² - 9x + 2",
                     ["x³ + 2x² - 9x + 2", "x³ + 6x² - 9x + 2", "x³ + 2x² + 9x + 2", "x³ + 2x² - 9x - 2"],
                     "x*(x² + 4x - 1) - 2*(x² + 4x - 1) = (x³ + 4x² - x) + (-2x² - 8x + 2) = x³ + 2x² - 9x + 2.")
add_t5_poly_multiply("Expand: (2x + 1)(x² - x + 3)", "2x³ - x² + 5x + 3",
                     ["2x³ - x² + 5x + 3", "2x³ + x² + 5x + 3", "2x³ - 2x² + 6x + 3", "2x³ - x² + 7x + 3"],
                     "2x*(x² - x + 3) + 1*(x² - x + 3) = (2x³ - 2x² + 6x) + (x² - x + 3) = 2x³ - x² + 5x + 3.")
add_t5_poly_multiply("Expand: (x + 1)(x² - x + 1)", "x³ + 1",
                     ["x³ + 1", "x³ - 1", "x³ + 2x² + 1", "x³ + x + 1"],
                     "Sum of cubes pattern: (a+b)(a² - ab + b²) = a³ + b³. With a = x, b = 1: x³ + 1. (Middle terms cancel.)")
add_t5_poly_multiply("Expand: (x - 1)(x² + x + 1)", "x³ - 1",
                     ["x³ - 1", "x³ + 1", "x³ + 2x² - 1", "x³ - x - 1"],
                     "Difference of cubes pattern: (a-b)(a² + ab + b²) = a³ - b³. With a = x, b = 1: x³ - 1.")
add_t5_poly_multiply("Expand: (2x - 3)(x² + 2x + 1)", "2x³ + x² - 4x - 3",
                     ["2x³ + x² - 4x - 3", "2x³ + 7x² + 4x - 3", "2x³ - x² - 4x - 3", "2x³ + x² + 4x - 3"],
                     "2x*(x² + 2x + 1) - 3*(x² + 2x + 1) = (2x³ + 4x² + 2x) - (3x² + 6x + 3) = 2x³ + x² - 4x - 3.")
add_t5_poly_multiply("Expand: (x + 4)(x² - 2x + 5)", "x³ + 2x² - 3x + 20",
                     ["x³ + 2x² - 3x + 20", "x³ + 6x² - 3x + 20", "x³ - 2x² + 5x + 20", "x³ + 2x² + 3x + 20"],
                     "x*(x² - 2x + 5) + 4*(x² - 2x + 5) = (x³ - 2x² + 5x) + (4x² - 8x + 20) = x³ + 2x² - 3x + 20.")
add_t5_poly_multiply("Expand: (3x + 2)(x² + x - 1)", "3x³ + 5x² - x - 2",
                     ["3x³ + 5x² - x - 2", "3x³ + 5x² + x - 2", "3x³ + 2x² - x - 2", "3x³ + 5x² - x + 2"],
                     "3x*(x² + x - 1) + 2*(x² + x - 1) = (3x³ + 3x² - 3x) + (2x² + 2x - 2) = 3x³ + 5x² - x - 2.")


def add_t5_foil(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"FOIL: First, Outer, Inner, Last. (a+b)(c+d) = ac + ad + bc + bd. "
            f"{walk}"
        ),
        "_pillar": 4,
        "_strategy": "foil",
    })


# 20 FOIL questions
add_t5_foil("Expand: (x + 3)(x + 5)", "x² + 8x + 15",
            ["x² + 8x + 15", "x² + 15x + 8", "x² + 3x + 5", "x² + 8x + 8"],
            "F: x*x = x². O: x*5 = 5x. I: 3*x = 3x. L: 3*5 = 15. Combine middle: x² + 8x + 15.")
add_t5_foil("Expand: (x + 2)(x + 7)", "x² + 9x + 14",
            ["x² + 9x + 14", "x² + 14x + 9", "x² + 2x + 7", "x² + 9x + 9"],
            "F: x². O: 7x. I: 2x. L: 14. Combine: x² + 9x + 14.")
add_t5_foil("Expand: (x + 4)(x + 6)", "x² + 10x + 24",
            ["x² + 10x + 24", "x² + 24x + 10", "x² + 4x + 6", "x² + 10x + 10"],
            "F: x². O: 6x. I: 4x. L: 24. Combine: x² + 10x + 24.")
add_t5_foil("Expand: (x + 1)(x + 8)", "x² + 9x + 8",
            ["x² + 9x + 8", "x² + 8x + 9", "x² + x + 8", "x² + 9x + 9"],
            "F: x². O: 8x. I: x. L: 8. Combine: x² + 9x + 8.")
add_t5_foil("Expand: (x - 7)(x - 2)", "x² - 9x + 14",
            ["x² - 9x + 14", "x² + 9x + 14", "x² - 5x + 14", "x² - 9x - 14"],
            "F: x². O: -2x. I: -7x. L: (-7)(-2) = 14. Combine: x² - 9x + 14.")
add_t5_foil("Expand: (x - 3)(x - 4)", "x² - 7x + 12",
            ["x² - 7x + 12", "x² + 7x + 12", "x² - x + 12", "x² - 7x - 12"],
            "F: x². O: -4x. I: -3x. L: 12. Combine: x² - 7x + 12.")
add_t5_foil("Expand: (x - 5)(x - 6)", "x² - 11x + 30",
            ["x² - 11x + 30", "x² + 11x + 30", "x² - x + 30", "x² - 11x - 30"],
            "F: x². O: -6x. I: -5x. L: 30. Combine: x² - 11x + 30.")
add_t5_foil("Expand: (x + 5)(x - 3)", "x² + 2x - 15",
            ["x² + 2x - 15", "x² - 2x - 15", "x² + 8x - 15", "x² + 2x + 15"],
            "F: x². O: -3x. I: 5x. L: -15. Combine: x² + 2x - 15.")
add_t5_foil("Expand: (x - 4)(x + 7)", "x² + 3x - 28",
            ["x² + 3x - 28", "x² - 3x - 28", "x² + 11x - 28", "x² + 3x + 28"],
            "F: x². O: 7x. I: -4x. L: -28. Combine: x² + 3x - 28.")
add_t5_foil("Expand: (x + 6)(x - 2)", "x² + 4x - 12",
            ["x² + 4x - 12", "x² - 4x - 12", "x² + 8x - 12", "x² + 4x + 12"],
            "F: x². O: -2x. I: 6x. L: -12. Combine: x² + 4x - 12.")
add_t5_foil("Expand: (2x - 1)(x + 4)", "2x² + 7x - 4",
            ["2x² + 7x - 4", "2x² - 7x - 4", "2x² + 8x - 4", "2x² + 7x + 4"],
            "F: 2x*x = 2x². O: 8x. I: -x. L: -4. Combine: 2x² + 7x - 4.")
add_t5_foil("Expand: (3x + 1)(x - 2)", "3x² - 5x - 2",
            ["3x² - 5x - 2", "3x² + 5x - 2", "3x² - x - 2", "3x² - 5x + 2"],
            "F: 3x². O: -6x. I: x. L: -2. Combine: 3x² - 5x - 2.")
add_t5_foil("Expand: (2x + 3)(x + 5)", "2x² + 13x + 15",
            ["2x² + 13x + 15", "2x² + 8x + 15", "2x² + 13x + 8", "2x² + 5x + 15"],
            "F: 2x². O: 10x. I: 3x. L: 15. Combine: 2x² + 13x + 15.")
add_t5_foil("Expand: (4x - 1)(x + 2)", "4x² + 7x - 2",
            ["4x² + 7x - 2", "4x² - 7x - 2", "4x² + 9x - 2", "4x² + 7x + 2"],
            "F: 4x². O: 8x. I: -x. L: -2. Combine: 4x² + 7x - 2.")
add_t5_foil("Expand: (2x + 1)(3x + 4)", "6x² + 11x + 4",
            ["6x² + 11x + 4", "6x² + 7x + 4", "6x² + 11x + 5", "6x² + 8x + 4"],
            "F: 6x². O: 8x. I: 3x. L: 4. Combine: 6x² + 11x + 4.")
add_t5_foil("Expand: (3x - 2)(2x + 1)", "6x² - x - 2",
            ["6x² - x - 2", "6x² + x - 2", "6x² - 7x - 2", "6x² - x + 2"],
            "F: 6x². O: 3x. I: -4x. L: -2. Combine: 6x² - x - 2.")
add_t5_foil("Expand: (x + 10)(x - 1)", "x² + 9x - 10",
            ["x² + 9x - 10", "x² - 9x - 10", "x² + 11x - 10", "x² + 9x + 10"],
            "F: x². O: -x. I: 10x. L: -10. Combine: x² + 9x - 10.")
add_t5_foil("Expand: (x - 8)(x + 3)", "x² - 5x - 24",
            ["x² - 5x - 24", "x² + 5x - 24", "x² - 11x - 24", "x² - 5x + 24"],
            "F: x². O: 3x. I: -8x. L: -24. Combine: x² - 5x - 24.")
add_t5_foil("Expand: (5x + 2)(x - 1)", "5x² - 3x - 2",
            ["5x² - 3x - 2", "5x² + 3x - 2", "5x² - 7x - 2", "5x² - 3x + 2"],
            "F: 5x². O: -5x. I: 2x. L: -2. Combine: 5x² - 3x - 2.")
add_t5_foil("Expand: (2x - 5)(x - 3)", "2x² - 11x + 15",
            ["2x² - 11x + 15", "2x² + 11x + 15", "2x² - x + 15", "2x² - 11x - 15"],
            "F: 2x². O: -6x. I: -5x. L: 15. Combine: 2x² - 11x + 15.")


def add_t5_diff_squares(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Difference of squares: a² - b² = (a + b)(a - b). {walk}"
        ),
        "_pillar": 4,
        "_strategy": "diff_of_squares_factor",
    })


# 10 difference-of-squares factor
add_t5_diff_squares("Factor: x² - 25", "(x + 5)(x - 5)",
                    ["(x + 5)(x - 5)", "(x - 5)²", "(x + 5)²", "(x + 25)(x - 1)"],
                    "x² - 25 = x² - 5² = (x + 5)(x - 5).")
add_t5_diff_squares("Factor: x² - 16", "(x + 4)(x - 4)",
                    ["(x + 4)(x - 4)", "(x - 4)²", "(x + 4)²", "(x + 16)(x - 1)"],
                    "x² - 16 = x² - 4² = (x + 4)(x - 4).")
add_t5_diff_squares("Factor: x² - 9", "(x + 3)(x - 3)",
                    ["(x + 3)(x - 3)", "(x - 3)²", "(x + 3)²", "(x + 9)(x - 1)"],
                    "x² - 9 = x² - 3² = (x + 3)(x - 3).")
add_t5_diff_squares("Factor: x² - 49", "(x + 7)(x - 7)",
                    ["(x + 7)(x - 7)", "(x - 7)²", "(x + 7)²", "(x + 49)(x - 1)"],
                    "x² - 49 = x² - 7² = (x + 7)(x - 7).")
add_t5_diff_squares("Factor: x² - 100", "(x + 10)(x - 10)",
                    ["(x + 10)(x - 10)", "(x - 10)²", "(x + 10)²", "(x + 100)(x - 1)"],
                    "x² - 100 = x² - 10² = (x + 10)(x - 10).")
add_t5_diff_squares("Factor: x² - 64", "(x + 8)(x - 8)",
                    ["(x + 8)(x - 8)", "(x - 8)²", "(x + 8)²", "(x + 64)(x - 1)"],
                    "x² - 64 = x² - 8² = (x + 8)(x - 8).")
add_t5_diff_squares("Factor: 4x² - 9", "(2x + 3)(2x - 3)",
                    ["(2x + 3)(2x - 3)", "(2x - 3)²", "(4x + 3)(x - 3)", "(2x + 9)(2x - 1)"],
                    "4x² = (2x)²; 9 = 3². So 4x² - 9 = (2x)² - 3² = (2x + 3)(2x - 3).")
add_t5_diff_squares("Factor: 9x² - 16", "(3x + 4)(3x - 4)",
                    ["(3x + 4)(3x - 4)", "(3x - 4)²", "(9x + 4)(x - 4)", "(3x + 16)(3x - 1)"],
                    "9x² = (3x)²; 16 = 4². So 9x² - 16 = (3x + 4)(3x - 4).")
add_t5_diff_squares("Factor: x² - 121", "(x + 11)(x - 11)",
                    ["(x + 11)(x - 11)", "(x - 11)²", "(x + 11)²", "(x + 121)(x - 1)"],
                    "x² - 121 = x² - 11² = (x + 11)(x - 11).")
add_t5_diff_squares("Factor: 25x² - 36", "(5x + 6)(5x - 6)",
                    ["(5x + 6)(5x - 6)", "(5x - 6)²", "(25x + 6)(x - 6)", "(5x + 36)(5x - 1)"],
                    "25x² = (5x)²; 36 = 6². So 25x² - 36 = (5x + 6)(5x - 6).")


def add_t5_trinomial(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Trinomial factoring: find two numbers that multiply to the "
            f"constant term and add to the middle coefficient. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "trinomial_factor",
    })


# 15 trinomial factoring
add_t5_trinomial("Factor: x² + 7x + 12", "(x + 3)(x + 4)",
                 ["(x + 3)(x + 4)", "(x + 2)(x + 6)", "(x + 1)(x + 12)", "(x + 5)(x + 2)"],
                 "Find two numbers that multiply to 12 and add to 7: 3 and 4. So x² + 7x + 12 = (x + 3)(x + 4).")
add_t5_trinomial("Factor: x² + 5x + 6", "(x + 2)(x + 3)",
                 ["(x + 2)(x + 3)", "(x + 1)(x + 6)", "(x + 5)(x + 1)", "(x + 6)(x - 1)"],
                 "Find two numbers that multiply to 6 and add to 5: 2 and 3. So x² + 5x + 6 = (x + 2)(x + 3).")
add_t5_trinomial("Factor: x² + 8x + 15", "(x + 3)(x + 5)",
                 ["(x + 3)(x + 5)", "(x + 1)(x + 15)", "(x + 7)(x + 8)", "(x + 5)(x + 1)"],
                 "Find two numbers that multiply to 15 and add to 8: 3 and 5. So x² + 8x + 15 = (x + 3)(x + 5).")
add_t5_trinomial("Factor: x² + 9x + 20", "(x + 4)(x + 5)",
                 ["(x + 4)(x + 5)", "(x + 2)(x + 10)", "(x + 1)(x + 20)", "(x + 4)(x + 9)"],
                 "Find two numbers that multiply to 20 and add to 9: 4 and 5. So x² + 9x + 20 = (x + 4)(x + 5).")
add_t5_trinomial("Factor: x² + 10x + 21", "(x + 3)(x + 7)",
                 ["(x + 3)(x + 7)", "(x + 1)(x + 21)", "(x + 5)(x + 5)", "(x + 7)(x + 14)"],
                 "Find two numbers that multiply to 21 and add to 10: 3 and 7. So x² + 10x + 21 = (x + 3)(x + 7).")
add_t5_trinomial("Factor: x² - 5x + 6", "(x - 2)(x - 3)",
                 ["(x - 2)(x - 3)", "(x + 2)(x - 3)", "(x - 1)(x - 6)", "(x + 6)(x - 1)"],
                 "Multiply to 6, add to -5. Both negative: -2 and -3. So x² - 5x + 6 = (x - 2)(x - 3).")
add_t5_trinomial("Factor: x² - 7x + 10", "(x - 2)(x - 5)",
                 ["(x - 2)(x - 5)", "(x + 2)(x - 5)", "(x - 1)(x - 10)", "(x - 3)(x - 7)"],
                 "Multiply to 10, add to -7. Both negative: -2 and -5. So x² - 7x + 10 = (x - 2)(x - 5).")
add_t5_trinomial("Factor: x² - 6x + 8", "(x - 2)(x - 4)",
                 ["(x - 2)(x - 4)", "(x + 2)(x - 4)", "(x - 1)(x - 8)", "(x - 4)(x - 6)"],
                 "Multiply to 8, add to -6: -2 and -4. So x² - 6x + 8 = (x - 2)(x - 4).")
add_t5_trinomial("Factor: x² - 9x + 14", "(x - 2)(x - 7)",
                 ["(x - 2)(x - 7)", "(x + 2)(x - 7)", "(x - 1)(x - 14)", "(x - 7)(x - 9)"],
                 "Multiply to 14, add to -9: -2 and -7. So x² - 9x + 14 = (x - 2)(x - 7).")
add_t5_trinomial("Factor: x² + x - 12", "(x + 4)(x - 3)",
                 ["(x + 4)(x - 3)", "(x - 4)(x + 3)", "(x + 6)(x - 2)", "(x + 12)(x - 1)"],
                 "Multiply to -12, add to 1: 4 and -3. So x² + x - 12 = (x + 4)(x - 3).")
add_t5_trinomial("Factor: x² + 2x - 15", "(x + 5)(x - 3)",
                 ["(x + 5)(x - 3)", "(x - 5)(x + 3)", "(x + 15)(x - 1)", "(x + 5)(x - 5)"],
                 "Multiply to -15, add to 2: 5 and -3. So x² + 2x - 15 = (x + 5)(x - 3).")
add_t5_trinomial("Factor: x² - 3x - 10", "(x - 5)(x + 2)",
                 ["(x - 5)(x + 2)", "(x + 5)(x - 2)", "(x - 10)(x + 1)", "(x - 2)(x + 5)"],
                 "Multiply to -10, add to -3: -5 and 2. So x² - 3x - 10 = (x - 5)(x + 2).")
add_t5_trinomial("Factor: x² + 4x - 21", "(x + 7)(x - 3)",
                 ["(x + 7)(x - 3)", "(x - 7)(x + 3)", "(x + 21)(x - 1)", "(x + 7)(x - 7)"],
                 "Multiply to -21, add to 4: 7 and -3. So x² + 4x - 21 = (x + 7)(x - 3).")
add_t5_trinomial("Factor: x² - 2x - 8", "(x - 4)(x + 2)",
                 ["(x - 4)(x + 2)", "(x + 4)(x - 2)", "(x - 8)(x + 1)", "(x - 2)(x + 4)"],
                 "Multiply to -8, add to -2: -4 and 2. So x² - 2x - 8 = (x - 4)(x + 2).")
add_t5_trinomial("Factor: x² + 6x + 8", "(x + 2)(x + 4)",
                 ["(x + 2)(x + 4)", "(x + 1)(x + 8)", "(x + 3)(x + 5)", "(x + 4)(x + 4)"],
                 "Multiply to 8, add to 6: 2 and 4. So x² + 6x + 8 = (x + 2)(x + 4).")


def add_t5_perfect_square(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Perfect square trinomial: (a + b)² = a² + 2ab + b², "
            f"or (a - b)² = a² - 2ab + b². {walk}"
        ),
        "_pillar": 4,
        "_strategy": "perfect_square_trinomial",
    })


# 5 perfect-square trinomials
add_t5_perfect_square("Factor: x² + 6x + 9", "(x + 3)²",
                      ["(x + 3)²", "(x + 9)(x + 1)", "(x + 3)(x - 3)", "(x + 6)(x + 3)"],
                      "Recognize: 6 = 2*3 and 9 = 3². Perfect square trinomial: x² + 6x + 9 = (x + 3)².")
add_t5_perfect_square("Factor: x² - 10x + 25", "(x - 5)²",
                      ["(x - 5)²", "(x - 25)(x - 1)", "(x + 5)(x - 5)", "(x - 5)(x - 10)"],
                      "10 = 2*5 and 25 = 5². Perfect square: x² - 10x + 25 = (x - 5)².")
add_t5_perfect_square("Factor: x² + 8x + 16", "(x + 4)²",
                      ["(x + 4)²", "(x + 8)(x + 2)", "(x + 4)(x - 4)", "(x + 16)(x + 1)"],
                      "8 = 2*4 and 16 = 4². Perfect square: x² + 8x + 16 = (x + 4)².")
add_t5_perfect_square("Factor: x² - 12x + 36", "(x - 6)²",
                      ["(x - 6)²", "(x - 12)(x - 3)", "(x + 6)(x - 6)", "(x - 6)(x - 12)"],
                      "12 = 2*6 and 36 = 6². Perfect square: x² - 12x + 36 = (x - 6)².")
add_t5_perfect_square("Factor: x² + 4x + 4", "(x + 2)²",
                      ["(x + 2)²", "(x + 4)(x + 1)", "(x + 2)(x - 2)", "(x + 4)(x + 4)"],
                      "4 = 2*2 and 4 = 2². Perfect square: x² + 4x + 4 = (x + 2)².")


def add_t5_factor_group(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Factoring by grouping. Pair terms, factor each pair, then "
            f"factor out the common binomial. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "factor_by_grouping",
    })


# 5 factor-by-grouping
add_t5_factor_group("Factor: x³ + 2x² + 3x + 6", "(x² + 3)(x + 2)",
                    ["(x² + 3)(x + 2)", "(x³ + 3)(x + 2)", "(x + 3)(x² + 2)", "(x² + 6)(x + 1)"],
                    "Group: (x³ + 2x²) + (3x + 6) = x²(x + 2) + 3(x + 2) = (x² + 3)(x + 2).")
add_t5_factor_group("Factor: x³ + 3x² + 2x + 6", "(x² + 2)(x + 3)",
                    ["(x² + 2)(x + 3)", "(x³ + 2)(x + 3)", "(x + 2)(x² + 3)", "(x² + 6)(x + 1)"],
                    "Group: (x³ + 3x²) + (2x + 6) = x²(x + 3) + 2(x + 3) = (x² + 2)(x + 3).")
add_t5_factor_group("Factor: x³ - 4x² + 5x - 20", "(x² + 5)(x - 4)",
                    ["(x² + 5)(x - 4)", "(x² - 5)(x + 4)", "(x² + 4)(x - 5)", "(x² - 4)(x + 5)"],
                    "Group: (x³ - 4x²) + (5x - 20) = x²(x - 4) + 5(x - 4) = (x² + 5)(x - 4).")
add_t5_factor_group("Factor: 2x³ + x² + 4x + 2", "(x² + 2)(2x + 1)",
                    ["(x² + 2)(2x + 1)", "(2x² + 1)(x + 2)", "(x² + 4)(2x + 1)", "(2x + 4)(x² + 1)"],
                    "Group: (2x³ + x²) + (4x + 2) = x²(2x + 1) + 2(2x + 1) = (x² + 2)(2x + 1).")
add_t5_factor_group("Factor: x³ + 5x² + 2x + 10", "(x² + 2)(x + 5)",
                    ["(x² + 2)(x + 5)", "(x³ + 2)(x + 5)", "(x + 2)(x² + 5)", "(x² + 10)(x + 1)"],
                    "Group: (x³ + 5x²) + (2x + 10) = x²(x + 5) + 2(x + 5) = (x² + 2)(x + 5).")


def add_t5_solve_quad_factor(stem: str, answer: str, choices: list[str], walk: str) -> None:
    # CRITICAL: ASCII hyphen for math_correctness gate
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Solve quadratic by factoring. Factor the trinomial, then set "
            f"each factor to zero (zero-product property). {walk}"
        ),
        "_pillar": 4,
        "_strategy": "solve_quadratic_factor",
    })


# 10 solve quadratic by factoring
add_t5_solve_quad_factor("Solve: x² - 5x + 6 = 0", "x = 2 or x = 3",
                         ["x = 2 or x = 3", "x = -2 or x = -3", "x = 1 or x = 6", "x = -1 or x = -6"],
                         "Factor: x² - 5x + 6 = (x - 2)(x - 3). Set each = 0: x = 2 or x = 3.")
add_t5_solve_quad_factor("Solve: x² + 3x - 10 = 0", "x = 2 or x = -5",
                         ["x = 2 or x = -5", "x = -2 or x = 5", "x = 1 or x = -10", "x = -1 or x = 10"],
                         "Factor: x² + 3x - 10 = (x - 2)(x + 5). Set each = 0: x = 2 or x = -5.")
add_t5_solve_quad_factor("Solve: x² - 7x + 12 = 0", "x = 3 or x = 4",
                         ["x = 3 or x = 4", "x = -3 or x = -4", "x = 1 or x = 12", "x = 2 or x = 6"],
                         "Factor: x² - 7x + 12 = (x - 3)(x - 4). Set each = 0: x = 3 or x = 4.")
add_t5_solve_quad_factor("Solve: x² + 5x + 4 = 0", "x = -1 or x = -4",
                         ["x = -1 or x = -4", "x = 1 or x = 4", "x = -2 or x = -2", "x = -5 or x = 1"],
                         "Factor: x² + 5x + 4 = (x + 1)(x + 4). Set each = 0: x = -1 or x = -4.")
add_t5_solve_quad_factor("Solve: x² - x - 6 = 0", "x = 3 or x = -2",
                         ["x = 3 or x = -2", "x = -3 or x = 2", "x = 1 or x = -6", "x = -1 or x = 6"],
                         "Factor: x² - x - 6 = (x - 3)(x + 2). Set each = 0: x = 3 or x = -2.")
add_t5_solve_quad_factor("Solve: x² + 2x - 8 = 0", "x = 2 or x = -4",
                         ["x = 2 or x = -4", "x = -2 or x = 4", "x = 1 or x = -8", "x = -1 or x = 8"],
                         "Factor: x² + 2x - 8 = (x - 2)(x + 4). Set each = 0: x = 2 or x = -4.")
add_t5_solve_quad_factor("Solve: x² - 8x + 15 = 0", "x = 3 or x = 5",
                         ["x = 3 or x = 5", "x = -3 or x = -5", "x = 1 or x = 15", "x = 2 or x = 8"],
                         "Factor: x² - 8x + 15 = (x - 3)(x - 5). Set each = 0: x = 3 or x = 5.")
add_t5_solve_quad_factor("Solve: x² + 7x + 10 = 0", "x = -2 or x = -5",
                         ["x = -2 or x = -5", "x = 2 or x = 5", "x = -1 or x = -10", "x = 1 or x = 10"],
                         "Factor: x² + 7x + 10 = (x + 2)(x + 5). Set each = 0: x = -2 or x = -5.")
add_t5_solve_quad_factor("Solve: x² - 4x - 12 = 0", "x = 6 or x = -2",
                         ["x = 6 or x = -2", "x = -6 or x = 2", "x = 1 or x = -12", "x = 3 or x = -4"],
                         "Factor: x² - 4x - 12 = (x - 6)(x + 2). Set each = 0: x = 6 or x = -2.")
add_t5_solve_quad_factor("Solve: x² + 6x + 8 = 0", "x = -2 or x = -4",
                         ["x = -2 or x = -4", "x = 2 or x = 4", "x = -1 or x = -8", "x = 1 or x = 8"],
                         "Factor: x² + 6x + 8 = (x + 2)(x + 4). Set each = 0: x = -2 or x = -4.")


def add_t5_solve_quad_sqrt(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Solve quadratic by square roots. Isolate the squared "
            f"expression, then take ± square root. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "solve_quadratic_sqrt",
    })


# 5 solve quadratic by square roots
add_t5_solve_quad_sqrt("Solve: x² = 49", "x = 7 or x = -7",
                       ["x = 7 or x = -7", "x = 7", "x = -7", "x = 49 or x = -49"],
                       "Take ± square root: x = ±√49 = ±7. So x = 7 or x = -7.")
add_t5_solve_quad_sqrt("Solve: x² = 64", "x = 8 or x = -8",
                       ["x = 8 or x = -8", "x = 8", "x = -8", "x = 32 or x = -32"],
                       "Take ± square root: x = ±√64 = ±8.")
add_t5_solve_quad_sqrt("Solve: (x - 3)² = 16", "x = 7 or x = -1",
                       ["x = 7 or x = -1", "x = 3 or x = -3", "x = 4 or x = -4", "x = 19 or x = -13"],
                       "Take ± square root: x - 3 = ±4. So x = 3 + 4 = 7 or x = 3 - 4 = -1.")
add_t5_solve_quad_sqrt("Solve: (x + 2)² = 25", "x = 3 or x = -7",
                       ["x = 3 or x = -7", "x = -2 or x = 2", "x = 5 or x = -5", "x = 27 or x = -23"],
                       "Take ± square root: x + 2 = ±5. So x = -2 + 5 = 3 or x = -2 - 5 = -7.")
add_t5_solve_quad_sqrt("Solve: x² = 100", "x = 10 or x = -10",
                       ["x = 10 or x = -10", "x = 10", "x = -10", "x = 50 or x = -50"],
                       "Take ± square root: x = ±√100 = ±10.")


def add_t5_quad_formula(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Quadratic formula: x = (-b ± √(b² - 4ac)) / (2a). {walk}"
        ),
        "_pillar": 4,
        "_strategy": "quadratic_formula",
    })


# 10 quadratic formula questions — these can have irrational answers
# Use easier values that produce simple solutions.
# Solving via quadratic formula but answer might also be reachable by factoring.
add_t5_quad_formula("Use the quadratic formula to solve: x² + 4x + 3 = 0", "x = -1 or x = -3",
                    ["x = -1 or x = -3", "x = 1 or x = 3", "x = -4 or x = 3", "x = 4 or x = -3"],
                    "a=1, b=4, c=3. Discriminant b² - 4ac = 16 - 12 = 4. x = (-4 ± 2)/2 = -1 or -3.")
add_t5_quad_formula("Use the quadratic formula to solve: x² - 6x + 8 = 0", "x = 2 or x = 4",
                    ["x = 2 or x = 4", "x = -2 or x = -4", "x = 6 or x = 8", "x = 1 or x = 8"],
                    "a=1, b=-6, c=8. Discriminant = 36 - 32 = 4. x = (6 ± 2)/2 = 4 or 2.")
add_t5_quad_formula("Use the quadratic formula to solve: x² + 5x + 4 = 0", "x = -1 or x = -4",
                    ["x = -1 or x = -4", "x = 1 or x = 4", "x = -5 or x = 4", "x = 5 or x = -4"],
                    "a=1, b=5, c=4. Discriminant = 25 - 16 = 9. x = (-5 ± 3)/2 = -1 or -4.")
add_t5_quad_formula("Use the quadratic formula to solve: x² - 3x - 4 = 0", "x = 4 or x = -1",
                    ["x = 4 or x = -1", "x = -4 or x = 1", "x = 3 or x = -4", "x = -3 or x = 4"],
                    "a=1, b=-3, c=-4. Discriminant = 9 + 16 = 25. x = (3 ± 5)/2 = 4 or -1.")
add_t5_quad_formula("Use the quadratic formula to solve: x² + 2x - 3 = 0", "x = 1 or x = -3",
                    ["x = 1 or x = -3", "x = -1 or x = 3", "x = -2 or x = 3", "x = 2 or x = -3"],
                    "a=1, b=2, c=-3. Discriminant = 4 + 12 = 16. x = (-2 ± 4)/2 = 1 or -3.")
add_t5_quad_formula("Use the quadratic formula to solve: 2x² + 7x + 3 = 0", "x = -1/2 or x = -3",
                    ["x = -1/2 or x = -3", "x = 1/2 or x = 3", "x = -2 or x = -3", "x = -7 or x = 3"],
                    "a=2, b=7, c=3. Discriminant = 49 - 24 = 25. x = (-7 ± 5)/4 = -1/2 or -3.")
add_t5_quad_formula("Use the quadratic formula to solve: x² - 2x - 8 = 0", "x = 4 or x = -2",
                    ["x = 4 or x = -2", "x = -4 or x = 2", "x = 2 or x = -8", "x = -2 or x = 8"],
                    "a=1, b=-2, c=-8. Discriminant = 4 + 32 = 36. x = (2 ± 6)/2 = 4 or -2.")
add_t5_quad_formula("Use the quadratic formula to solve: x² + 6x + 5 = 0", "x = -1 or x = -5",
                    ["x = -1 or x = -5", "x = 1 or x = 5", "x = -6 or x = 5", "x = 6 or x = -5"],
                    "a=1, b=6, c=5. Discriminant = 36 - 20 = 16. x = (-6 ± 4)/2 = -1 or -5.")
add_t5_quad_formula("Use the quadratic formula to solve: x² - x - 6 = 0", "x = 3 or x = -2",
                    ["x = 3 or x = -2", "x = -3 or x = 2", "x = 1 or x = -6", "x = -1 or x = 6"],
                    "a=1, b=-1, c=-6. Discriminant = 1 + 24 = 25. x = (1 ± 5)/2 = 3 or -2.")
add_t5_quad_formula("Use the quadratic formula to solve: 2x² - 3x - 2 = 0", "x = 2 or x = -1/2",
                    ["x = 2 or x = -1/2", "x = -2 or x = 1/2", "x = 1 or x = -2", "x = 3 or x = -2"],
                    "a=2, b=-3, c=-2. Discriminant = 9 + 16 = 25. x = (3 ± 5)/4 = 2 or -1/2.")


def add_t5_discriminant(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Discriminant: b² - 4ac. The discriminant tells you how many "
            f"real solutions a quadratic has: positive = 2, zero = 1 "
            f"(double root), negative = 0 real solutions. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "discriminant",
    })


# 5 discriminant questions
add_t5_discriminant("Find the discriminant of: x² + 5x + 6.", "1",
                    ["1", "5", "-1", "25"],
                    "a=1, b=5, c=6. Discriminant b² - 4ac = 25 - 24 = 1. Positive, so 2 real solutions.")
add_t5_discriminant("How many real solutions does x² + 3x + 5 = 0 have?", "0",
                    ["0", "1", "2", "3"],
                    "a=1, b=3, c=5. Discriminant = 9 - 20 = -11. Negative, so 0 real solutions.")
add_t5_discriminant("How many real solutions does x² - 6x + 9 = 0 have?", "1",
                    ["1", "0", "2", "3"],
                    "a=1, b=-6, c=9. Discriminant = 36 - 36 = 0. Zero discriminant means 1 real solution (a double root).")
add_t5_discriminant("Find the discriminant of: 2x² + 3x - 1.", "17",
                    ["17", "1", "-17", "9"],
                    "a=2, b=3, c=-1. Discriminant = 9 - (-8) = 9 + 8 = 17.")
add_t5_discriminant("How many real solutions does x² - 4x + 4 = 0 have?", "1",
                    ["1", "0", "2", "4"],
                    "a=1, b=-4, c=4. Discriminant = 16 - 16 = 0. Double root: 1 real solution.")


def add_t5_vertex_form(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Vertex form: y = a(x - h)² + k. The vertex of the parabola is "
            f"(h, k). Watch the sign — the x-coordinate is +h not -h. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "vertex_form",
    })


# 5 vertex-form questions
add_t5_vertex_form("Find the vertex of: y = (x - 2)² + 3", "(2, 3)",
                   ["(2, 3)", "(-2, 3)", "(2, -3)", "(-2, -3)"],
                   "Vertex form: y = a(x - h)² + k has vertex (h, k). Here h = 2, k = 3, so vertex is (2, 3).")
add_t5_vertex_form("Find the vertex of: y = (x + 1)² - 4", "(-1, -4)",
                   ["(-1, -4)", "(1, -4)", "(-1, 4)", "(1, 4)"],
                   "(x + 1)² = (x - (-1))², so h = -1. k = -4. Vertex (-1, -4).")
add_t5_vertex_form("Find the vertex of: y = (x - 5)² + 2", "(5, 2)",
                   ["(5, 2)", "(-5, 2)", "(5, -2)", "(-5, -2)"],
                   "Vertex form y = a(x - h)² + k. h = 5, k = 2. Vertex (5, 2).")
add_t5_vertex_form("Find the vertex of: y = (x + 3)² + 1", "(-3, 1)",
                   ["(-3, 1)", "(3, 1)", "(-3, -1)", "(3, -1)"],
                   "(x + 3)² = (x - (-3))², so h = -3. k = 1. Vertex (-3, 1).")
add_t5_vertex_form("Find the vertex of: y = (x - 4)² - 7", "(4, -7)",
                   ["(4, -7)", "(-4, -7)", "(4, 7)", "(-4, 7)"],
                   "Vertex form. h = 4, k = -7. Vertex (4, -7).")


def add_t5_rational(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Rational expression simplification. Factor numerator and "
            f"denominator first, then cancel common factors. Never cancel "
            f"terms before factoring. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "rational_simplify",
    })


# 5 rational expressions
add_t5_rational("Simplify: (x² - 16) / (x + 4)", "x - 4",
                ["x - 4", "x + 4", "x - 16", "1 / (x + 4)"],
                "Factor numerator: x² - 16 = (x + 4)(x - 4). Cancel (x + 4): (x + 4)(x - 4)/(x + 4) = x - 4.")
add_t5_rational("Simplify: (x² - 25) / (x - 5)", "x + 5",
                ["x + 5", "x - 5", "x - 25", "1 / (x - 5)"],
                "Factor: x² - 25 = (x + 5)(x - 5). Cancel (x - 5): result is x + 5.")
add_t5_rational("Simplify: (x² + 5x + 6) / (x + 2)", "x + 3",
                ["x + 3", "x + 2", "x + 5", "x + 6"],
                "Factor numerator: x² + 5x + 6 = (x + 2)(x + 3). Cancel (x + 2): result is x + 3.")
add_t5_rational("Simplify: (x² - 7x + 12) / (x - 3)", "x - 4",
                ["x - 4", "x - 3", "x - 7", "x - 12"],
                "Factor numerator: x² - 7x + 12 = (x - 3)(x - 4). Cancel (x - 3): result is x - 4.")
add_t5_rational("Simplify: (x² - 9) / (x - 3)", "x + 3",
                ["x + 3", "x - 3", "x - 9", "1 / (x - 3)"],
                "Factor numerator: x² - 9 = (x + 3)(x - 3) (difference of squares). Cancel (x - 3): x + 3.")


def add_t5_arith_seq(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Arithmetic sequence nth term: aₙ = a₁ + (n - 1)d, where a₁ is "
            f"the first term and d is the common difference. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "arithmetic_sequence",
    })


# 5 arithmetic-sequence
add_t5_arith_seq("Find the 10th term of: 3, 7, 11, 15, ...", "39",
                 ["39", "40", "43", "35"],
                 "a₁ = 3, d = 4. a₁₀ = 3 + 9*4 = 3 + 36 = 39. Watch the (n - 1) — off-by-one is the most common mistake.")
add_t5_arith_seq("Find the 8th term of: 5, 8, 11, 14, ...", "26",
                 ["26", "29", "24", "32"],
                 "a₁ = 5, d = 3. a₈ = 5 + 7*3 = 5 + 21 = 26.")
add_t5_arith_seq("Find the 12th term of: 2, 5, 8, 11, ...", "35",
                 ["35", "38", "32", "33"],
                 "a₁ = 2, d = 3. a₁₂ = 2 + 11*3 = 2 + 33 = 35.")
add_t5_arith_seq("Find the 7th term of: 10, 7, 4, 1, ...", "-8",
                 ["-8", "-5", "-11", "-2"],
                 "a₁ = 10, d = -3. a₇ = 10 + 6*(-3) = 10 - 18 = -8.")
add_t5_arith_seq("Find the 15th term of: 1, 4, 7, 10, ...", "43",
                 ["43", "46", "40", "44"],
                 "a₁ = 1, d = 3. a₁₅ = 1 + 14*3 = 1 + 42 = 43.")


def add_t5_geom_seq(stem: str, answer: str, choices: list[str], walk: str) -> None:
    T5.append({
        "tier": 5,
        "question": stem,
        "answer": answer,
        "choices": choices,
        "context": (
            f"Geometric sequence nth term: aₙ = a₁ · r^(n - 1), where a₁ is "
            f"the first term and r is the common ratio. {walk}"
        ),
        "_pillar": 4,
        "_strategy": "geometric_sequence",
    })


# 5 geometric-sequence
add_t5_geom_seq("Find the 5th term of: 2, 6, 18, 54, ...", "162",
                ["162", "486", "108", "54"],
                "a₁ = 2, r = 3. a₅ = 2 * 3^4 = 2 * 81 = 162.")
add_t5_geom_seq("Find the 4th term of: 3, 6, 12, 24, ...", "24",
                ["24", "48", "12", "36"],
                "a₁ = 3, r = 2. a₄ = 3 * 2^3 = 3 * 8 = 24.")
add_t5_geom_seq("Find the 6th term of: 1, 2, 4, 8, ...", "32",
                ["32", "64", "16", "24"],
                "a₁ = 1, r = 2. a₆ = 1 * 2^5 = 32.")
add_t5_geom_seq("Find the 5th term of: 5, 10, 20, 40, ...", "80",
                ["80", "160", "60", "120"],
                "a₁ = 5, r = 2. a₅ = 5 * 2^4 = 5 * 16 = 80.")
add_t5_geom_seq("Find the 4th term of: 1, 3, 9, 27, ...", "27",
                ["27", "81", "12", "36"],
                "a₁ = 1, r = 3. a₄ = 1 * 3^3 = 27.")


# ============================================================================
# VALIDATE + SAVE
# ============================================================================

def main() -> None:
    from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite
    from collections import OrderedDict

    # Target distribution per spec: 30/60/110/100/100 = 400
    # We overshoot — trim per-strategy to keep coverage balanced.
    # Per-strategy caps for T4 (target 100):
    t4_caps = {
        "solve_linear": 15,
        "slope_from_points": 15,        # was 20
        "slope_intercept": 10,          # was 15
        "system_substitution": 10,
        "system_elimination": 10,
        "exponent_rules": 10,           # was 15
        "scientific_notation": 10,
        "sqrt_simplify": 10,
        "function_notation": 10,
    }
    # Per-strategy caps for T5 (target 100):
    t5_caps = {
        "polynomial_addition": 5,
        "polynomial_subtraction": 5,
        "polynomial_multiply": 5,       # was 10
        "foil": 10,                     # was 20
        "diff_of_squares_factor": 10,
        "trinomial_factor": 10,         # was 15
        "perfect_square_trinomial": 5,
        "factor_by_grouping": 5,
        "solve_quadratic_factor": 5,    # was 10
        "solve_quadratic_sqrt": 5,
        "quadratic_formula": 10,
        "discriminant": 5,
        "vertex_form": 5,
        "rational_simplify": 5,
        "arithmetic_sequence": 5,
        "geometric_sequence": 5,
    }

    def trim_by_strategy(qs: list, caps: dict) -> list:
        out = []
        counter: dict[str, int] = {}
        for q in qs:
            s = q.get("_strategy", "")
            limit = caps.get(s, 999)
            taken = counter.get(s, 0)
            if taken < limit:
                out.append(q)
                counter[s] = taken + 1
        return out

    t1 = T1[:30]
    t2 = T2[:60]
    t3 = T3[:110]
    t4 = trim_by_strategy(T4, t4_caps)[:100]
    t5 = trim_by_strategy(T5, t5_caps)[:100]
    all_q = t1 + t2 + t3 + t4 + t5
    print(f"[counts pre-validate] T1={len(t1)} T2={len(t2)} T3={len(t3)} T4={len(t4)} T5={len(t5)} | total={len(all_q)}")

    # Build empty indices — we're validating against an empty bank since we are
    # building a fresh proposal. (No duplicate check against prior math bank.)
    dup, ans = build_bank_indices([])

    passed: list[dict] = []
    failed_log: list[tuple[int, str, list]] = []
    soft_count = 0

    for i, q in enumerate(all_q):
        result = validate_rewrite("math", q, bank=[], dup_index=dup, answer_index=ans, replace_idx=None)
        if result["verdict"] == "PASS":
            passed.append(q)
        elif result["verdict"] == "SOFT_WARN":
            soft_count += 1
            passed.append(q)
        else:
            failed_log.append((i, q.get("question", ""), result["hard_fails"]))

    print(f"[validate] PASS+SOFT={len(passed)} FAIL={len(failed_log)} | soft_warn={soft_count}")
    if failed_log[:20]:
        print(f"[first 20 fails]")
        for i, stem, fails in failed_log[:20]:
            print(f"  #{i} T{all_q[i].get('tier')}: {stem[:70]}")
            for gate, reason in fails:
                print(f"     {gate}: {reason[:140]}")

    # Save passing questions
    out = {"questions": passed}
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[saved] {OUT_PATH} ({len(passed)} questions)")


if __name__ == "__main__":
    main()
