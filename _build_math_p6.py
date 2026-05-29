"""Bulk generator for Math Pillar 6 (Probability, stats & financial).

Target: 250 questions
  T1: 20  (skip counting / even-odd)
  T2: 50  (mean/median/mode/range, fundamental counting principle)
  T3: 80  (probability basics, compound probability, complement, sample)
  T4: 70  (simple interest, scatterplots, bivariate, outliers)
  T5: 30  (compound interest, arithmetic/geometric sequences)

Hard rules:
  - Stem caps: T1<=50, T2<=100, T3<=160, T4<=220, T5<=280
  - T2+ context names the formula/concept by name
  - Distractors model errors
  - Magnitude leak avoided
  - Currency stays currency, fractions stay fractions, etc.
  - All validated via tools.quizgen.audit.validate.validate_rewrite

Saves incrementally to proposals/v2_audit/_math_p6_output.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path("C:/Users/brand/Documents/PhilosophersQuest")
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import validate_rewrite, build_bank_indices  # noqa: E402

OUT_PATH = REPO / "proposals" / "v2_audit" / "_math_p6_output.json"
BANK_PATH = REPO / "data" / "questions" / "math.json"

# Use the en-dash / minus / multiplication signs as used in exemplars
MINUS = "−"  # U+2212 (used in exemplar contexts)
TIMES = "×"  # U+00D7
DIV = "÷"    # U+00F7


# ---------------------------------------------------------------------------
# T1 — 20 questions: skip counting (probability foundation) + even/odd
# ---------------------------------------------------------------------------
T1_QUESTIONS = [
    # Skip counting by 2s (foundation of probability / even numbers)
    {
        "tier": 1,
        "question": "2, 4, 6, ?, 10",
        "answer": "8",
        "choices": ["8", "7", "9", "12"],
        "context": (
            "Skip counting by 2s — even numbers. Adding 2 each step: 2, 4, "
            "6, 8, 10. This pattern is the foundation for the 2 times "
            "table and recognizing even numbers."
        ),
    },
    {
        "tier": 1,
        "question": "4, 6, 8, 10, ?",
        "answer": "12",
        "choices": ["12", "11", "14", "16"],
        "context": (
            "Skip counting by 2s. Adding 2 each step: 4, 6, 8, 10, 12. "
            "Skip counting by 2s gives the even numbers."
        ),
    },
    {
        "tier": 1,
        "question": "10, 12, 14, ?, 18",
        "answer": "16",
        "choices": ["16", "15", "17", "20"],
        "context": (
            "Skip counting by 2s. Each step adds 2: 10, 12, 14, 16, 18. "
            "Even numbers continue the pattern past 10."
        ),
    },
    # Skip counting by 5s
    {
        "tier": 1,
        "question": "5, 10, ?, 20, 25",
        "answer": "15",
        "choices": ["15", "11", "12", "17"],
        "context": (
            "Skip counting by 5s. Adding 5 each step: 5, 10, 15, 20, 25. "
            "Skip counting builds the 5 times table."
        ),
    },
    {
        "tier": 1,
        "question": "25, 30, 35, 40, ?",
        "answer": "45",
        "choices": ["45", "41", "50", "42"],
        "context": (
            "Skip counting by 5s. Each step adds 5: 25, 30, 35, 40, 45. "
            "Numbers ending in 0 or 5 form the 5 times table."
        ),
    },
    # Skip counting by 10s
    {
        "tier": 1,
        "question": "10, 20, 30, ?, 50",
        "answer": "40",
        "choices": ["40", "31", "35", "45"],
        "context": (
            "Skip counting by 10s. Adding 10 each step: 10, 20, 30, 40, 50. "
            "Skip counting by 10s grows the tens place."
        ),
    },
    {
        "tier": 1,
        "question": "50, 60, ?, 80, 90",
        "answer": "70",
        "choices": ["70", "65", "75", "72"],
        "context": (
            "Skip counting by 10s. Each step adds 10: 50, 60, 70, 80, 90. "
            "The tens digit grows by 1 each step."
        ),
    },
    # Skip counting by 3s (probability — odd/even mix)
    {
        "tier": 1,
        "question": "3, 6, 9, ?, 15",
        "answer": "12",
        "choices": ["12", "10", "11", "13"],
        "context": (
            "Skip counting by 3s. Adding 3 each step: 3, 6, 9, 12, 15. "
            "Skip counting by 3s builds the 3 times table."
        ),
    },
    {
        "tier": 1,
        "question": "12, 15, 18, 21, ?",
        "answer": "24",
        "choices": ["24", "22", "25", "27"],
        "context": (
            "Skip counting by 3s. Each step adds 3: 12, 15, 18, 21, 24. "
            "Multiples of 3 alternate even and odd."
        ),
    },
    # Even/odd recognition
    {
        "tier": 1,
        "question": "Is 47 even or odd?",
        "answer": "odd",
        "choices": ["odd", "even", "both", "neither"],
        "context": (
            "Even / odd. Look at the last digit: 0, 2, 4, 6, 8 are even; "
            "1, 3, 5, 7, 9 are odd. The 7 in 47 is odd, so 47 is odd."
        ),
    },
    {
        "tier": 1,
        "question": "Is 30 even or odd?",
        "answer": "even",
        "choices": ["even", "odd", "both", "neither"],
        "context": (
            "Even / odd. Last digit rule: ends in 0, 2, 4, 6, 8 → even. "
            "30 ends in 0, so 30 is even."
        ),
    },
    {
        "tier": 1,
        "question": "Is 83 even or odd?",
        "answer": "odd",
        "choices": ["odd", "even", "both", "neither"],
        "context": (
            "Even / odd. Last digit 3 is odd (1, 3, 5, 7, 9 are odd), "
            "so 83 is odd. Only the last digit matters."
        ),
    },
    {
        "tier": 1,
        "question": "Is 26 even or odd?",
        "answer": "even",
        "choices": ["even", "odd", "both", "neither"],
        "context": (
            "Even / odd. Last digit 6 is even, so 26 is even. "
            "Only the last digit matters for the even/odd rule."
        ),
    },
    {
        "tier": 1,
        "question": "Is 45 even or odd?",
        "answer": "odd",
        "choices": ["odd", "even", "both", "neither"],
        "context": (
            "Even / odd. Last digit 5 is odd, so 45 is odd. "
            "Multiples of 5 are odd unless they also end in 0."
        ),
    },
    {
        "tier": 1,
        "question": "Is 56 even or odd?",
        "answer": "even",
        "choices": ["even", "odd", "both", "neither"],
        "context": (
            "Even / odd. Last digit 6 is even (0, 2, 4, 6, 8 are even), "
            "so 56 is even."
        ),
    },
    {
        "tier": 1,
        "question": "Is 21 even or odd?",
        "answer": "odd",
        "choices": ["odd", "even", "both", "neither"],
        "context": (
            "Even / odd. Last digit 1 is odd, so 21 is odd. "
            "All numbers ending in 1 are odd."
        ),
    },
    {
        "tier": 1,
        "question": "Is 72 even or odd?",
        "answer": "even",
        "choices": ["even", "odd", "both", "neither"],
        "context": (
            "Even / odd. Last digit 2 is even, so 72 is even. "
            "72 = 8 × 9, both factors visible at a glance."
        ),
    },
    {
        "tier": 1,
        "question": "Is 15 even or odd?",
        "answer": "odd",
        "choices": ["odd", "even", "both", "neither"],
        "context": (
            "Even / odd. Last digit 5 is odd, so 15 is odd. "
            "All multiples of 5 that aren't multiples of 10 are odd."
        ),
    },
    {
        "tier": 1,
        "question": "Is 78 even or odd?",
        "answer": "even",
        "choices": ["even", "odd", "both", "neither"],
        "context": (
            "Even / odd. Last digit 8 is even, so 78 is even. "
            "All multiples of 2 are even."
        ),
    },
    {
        "tier": 1,
        "question": "Is 37 even or odd?",
        "answer": "odd",
        "choices": ["odd", "even", "both", "neither"],
        "context": (
            "Even / odd. Last digit 7 is odd, so 37 is odd. "
            "37 is also a prime number."
        ),
    },
]


# ---------------------------------------------------------------------------
# T2 — 50 questions: mean/median/mode/range + fundamental counting principle
# ---------------------------------------------------------------------------
T2_QUESTIONS = [
    # Mean / average — 16 questions
    {
        "tier": 2,
        "question": "Mean of 3, 5, 7, 9 = ?",
        "answer": "6",
        "choices": ["6", "5", "7", "24"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 3 + 5 + 7 + 9 = 24. "
            "Count: 4. Mean = 24 ÷ 4 = 6. Common error: forgetting to "
            "divide and reporting the sum (24)."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 2, 4, 6 = ?",
        "answer": "4",
        "choices": ["4", "3", "6", "12"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 2 + 4 + 6 = 12. "
            "Count: 3. Mean = 12 ÷ 3 = 4. The mean of evenly-spaced "
            "numbers is the middle one."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 10, 20, 30, 40 = ?",
        "answer": "25",
        "choices": ["25", "20", "30", "100"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 10 + 20 + 30 + 40 = 100. "
            "Count: 4. Mean = 100 ÷ 4 = 25. Forgetting to divide gives "
            "the sum, 100."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 5, 10, 15, 20, 25 = ?",
        "answer": "15",
        "choices": ["15", "13", "20", "75"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 5 + 10 + 15 + 20 + 25 = 75. "
            "Count: 5. Mean = 75 ÷ 5 = 15. Evenly-spaced data: mean equals "
            "the middle value."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 1, 2, 3, 4, 5 = ?",
        "answer": "3",
        "choices": ["3", "2", "4", "15"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 1 + 2 + 3 + 4 + 5 = 15. "
            "Count: 5. Mean = 15 ÷ 5 = 3. The mean of 1 through n equals "
            "the middle when n is odd."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 6, 8, 10 = ?",
        "answer": "8",
        "choices": ["8", "7", "9", "24"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 6 + 8 + 10 = 24. "
            "Count: 3. Mean = 24 ÷ 3 = 8. Mean of evenly-spaced numbers = "
            "the middle number."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 12, 14, 16, 18 = ?",
        "answer": "15",
        "choices": ["15", "14", "16", "60"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 12 + 14 + 16 + 18 = 60. "
            "Count: 4. Mean = 60 ÷ 4 = 15. Halfway between the two "
            "middle values for evenly-spaced data."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 4, 4, 4, 4 = ?",
        "answer": "4",
        "choices": ["4", "1", "8", "16"],
        "context": (
            "Mean (average): sum ÷ count. All values equal 4, so sum = "
            "16 and count = 4. Mean = 16 ÷ 4 = 4. When every value is "
            "the same, the mean equals that value."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 0, 5, 10 = ?",
        "answer": "5",
        "choices": ["5", "3", "7", "15"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 0 + 5 + 10 = 15. "
            "Count: 3. Mean = 15 ÷ 3 = 5. Zero counts as a data point."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 7, 9, 11, 13 = ?",
        "answer": "10",
        "choices": ["10", "9", "11", "40"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 7 + 9 + 11 + 13 = 40. "
            "Count: 4. Mean = 40 ÷ 4 = 10. Forgot to divide → 40 (the sum)."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 50, 60, 70 = ?",
        "answer": "60",
        "choices": ["60", "55", "65", "180"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 50 + 60 + 70 = 180. "
            "Count: 3. Mean = 180 ÷ 3 = 60. Forgot to divide → 180."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 8, 10, 12, 14, 16 = ?",
        "answer": "12",
        "choices": ["12", "10", "14", "60"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 8 + 10 + 12 + 14 + 16 = 60. "
            "Count: 5. Mean = 60 ÷ 5 = 12. Mean of evenly-spaced = middle."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 100, 200, 300 = ?",
        "answer": "200",
        "choices": ["200", "150", "250", "600"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 100 + 200 + 300 = 600. "
            "Count: 3. Mean = 600 ÷ 3 = 200. Forgot to divide → 600."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 1, 3, 5, 7, 9 = ?",
        "answer": "5",
        "choices": ["5", "4", "6", "25"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 1 + 3 + 5 + 7 + 9 = 25. "
            "Count: 5. Mean = 25 ÷ 5 = 5. Mean of odd numbers 1–9 is 5."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 20, 40 = ?",
        "answer": "30",
        "choices": ["30", "20", "40", "60"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 20 + 40 = 60. Count: 2. "
            "Mean = 60 ÷ 2 = 30. Mean of two numbers = halfway between."
        ),
    },
    {
        "tier": 2,
        "question": "Mean of 2, 8 = ?",
        "answer": "5",
        "choices": ["5", "4", "6", "10"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 2 + 8 = 10. Count: 2. "
            "Mean = 10 ÷ 2 = 5. Mean of two numbers = midpoint."
        ),
    },
    # Median — 15 questions
    {
        "tier": 2,
        "question": "Median of 3, 5, 7, 9, 11 = ?",
        "answer": "7",
        "choices": ["7", "5", "9", "35"],
        "context": (
            "Median: middle value when sorted. Already sorted: 3, 5, 7, 9, "
            "11. Middle position is the 3rd (out of 5), which is 7. With "
            "odd count, the median is the exact middle."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 4, 6, 8, 10 = ?",
        "answer": "7",
        "choices": ["7", "6", "8", "28"],
        "context": (
            "Median: middle value when sorted. With 4 values, average "
            "the two middle values: (6 + 8) ÷ 2 = 7. Even-count data "
            "uses the mean of the middle pair."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 2, 5, 8, 11, 14 = ?",
        "answer": "8",
        "choices": ["8", "5", "11", "40"],
        "context": (
            "Median: middle value when sorted. Sorted: 2, 5, 8, 11, 14. "
            "Middle position is the 3rd: 8. Odd count → exact middle."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 10, 20, 30 = ?",
        "answer": "20",
        "choices": ["20", "10", "30", "60"],
        "context": (
            "Median: middle value when sorted. Sorted: 10, 20, 30. "
            "Middle is 20. With odd count, just pick the middle value."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 8, 2, 5, 9, 6 = ?",
        "answer": "6",
        "choices": ["6", "5", "8", "30"],
        "context": (
            "Median: middle value when sorted. Sort first: 2, 5, 6, 8, 9. "
            "Middle of 5 values is the 3rd: 6. Always sort BEFORE finding "
            "the median."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 4, 4, 4, 4 = ?",
        "answer": "4",
        "choices": ["4", "0", "8", "16"],
        "context": (
            "Median: middle value when sorted. All values equal, so any "
            "of them is the middle: 4. When values repeat, the median can "
            "equal the mode."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 3, 6, 9, 12, 15, 18 = ?",
        "answer": "10.5",
        "choices": ["10.5", "9", "12", "63"],
        "context": (
            "Median: middle value when sorted. With 6 values, average "
            "the two middle values: (9 + 12) ÷ 2 = 10.5. Even count → "
            "mean of middle pair."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 15, 22, 8, 30, 12 = ?",
        "answer": "15",
        "choices": ["15", "12", "22", "87"],
        "context": (
            "Median: middle value when sorted. Sort first: 8, 12, 15, 22, "
            "30. Middle of 5 is the 3rd: 15. Sort, then pick middle."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 5, 5, 5 = ?",
        "answer": "5",
        "choices": ["5", "0", "10", "15"],
        "context": (
            "Median: middle value when sorted. All three are 5, so "
            "middle is 5. Repeated values stay repeated through the sort."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 7, 14, 21 = ?",
        "answer": "14",
        "choices": ["14", "7", "21", "42"],
        "context": (
            "Median: middle value when sorted. Sorted: 7, 14, 21. Middle "
            "of 3 is 14. Skip-count-by-7 sequence: middle is the 2nd term."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 120, 40, 80 = ?",
        "answer": "80",
        "choices": ["80", "40", "120", "240"],
        "context": (
            "Median: middle value when sorted. Sort first: 40, 80, 120. "
            "Middle of 3 is 80. Always sort BEFORE finding median."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 3, 3, 6, 9 = ?",
        "answer": "4.5",
        "choices": ["4.5", "3", "6", "21"],
        "context": (
            "Median: middle value when sorted. With 4 values, average the "
            "two middle values: (3 + 6) ÷ 2 = 4.5. Repeated values still "
            "count in their positions."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 11, 13, 15, 17 = ?",
        "answer": "14",
        "choices": ["14", "13", "15", "56"],
        "context": (
            "Median: middle value when sorted. With 4 values: (13 + 15) "
            "÷ 2 = 14. Even count → mean of the two middle values."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 9, 1, 5 = ?",
        "answer": "5",
        "choices": ["5", "1", "9", "15"],
        "context": (
            "Median: middle value when sorted. Sort first: 1, 5, 9. "
            "Middle of 3 is 5. Without sorting, you'd wrongly pick the "
            "middle of the unsorted list."
        ),
    },
    {
        "tier": 2,
        "question": "Median of 25, 30, 35, 40, 45 = ?",
        "answer": "35",
        "choices": ["35", "30", "40", "175"],
        "context": (
            "Median: middle value when sorted. Already sorted: middle of "
            "5 is the 3rd value, 35. Mean of this data is also 35 — they "
            "agree for evenly-spaced sets."
        ),
    },
    # Mode — 10 questions
    {
        "tier": 2,
        "question": "Mode of 4, 5, 5, 7, 9 = ?",
        "answer": "5",
        "choices": ["5", "4", "7", "30"],
        "context": (
            "Mode: most frequent value. The 5 appears twice; every other "
            "value appears once. Mode is the value, not its count."
        ),
    },
    {
        "tier": 2,
        "question": "Mode of 4, 4, 4, 6, 8 = ?",
        "answer": "4",
        "choices": ["4", "6", "8", "26"],
        "context": (
            "Mode: most frequent value. The 4 appears three times — more "
            "than any other value. Mode reports the value itself, not 'three'."
        ),
    },
    {
        "tier": 2,
        "question": "Mode of 1, 3, 3, 5, 7, 7, 7 = ?",
        "answer": "7",
        "choices": ["7", "3", "5", "33"],
        "context": (
            "Mode: most frequent value. The 7 appears 3 times; 3 appears "
            "twice. Highest frequency wins: 7 is the mode."
        ),
    },
    {
        "tier": 2,
        "question": "Mode of 5, 5, 7, 9, 9, 9 = ?",
        "answer": "9",
        "choices": ["9", "5", "7", "44"],
        "context": (
            "Mode: most frequent value. The 9 appears 3 times; 5 appears "
            "twice. Mode is the value with the most repetitions: 9."
        ),
    },
    {
        "tier": 2,
        "question": "Mode of 10, 20, 30, 30, 40 = ?",
        "answer": "30",
        "choices": ["30", "20", "40", "130"],
        "context": (
            "Mode: most frequent value. The 30 appears twice; every other "
            "value appears once. Mode = 30."
        ),
    },
    {
        "tier": 2,
        "question": "Mode of 6, 6, 6, 6 = ?",
        "answer": "6",
        "choices": ["6", "4", "12", "24"],
        "context": (
            "Mode: most frequent value. Every value is 6, so 6 is the "
            "mode. When all values are the same, mode = mean = median = "
            "that value."
        ),
    },
    {
        "tier": 2,
        "question": "Mode of 1, 1, 2, 3, 3, 3 = ?",
        "answer": "3",
        "choices": ["3", "1", "2", "13"],
        "context": (
            "Mode: most frequent value. The 3 appears 3 times; 1 appears "
            "twice. Mode goes to the value with the highest count: 3."
        ),
    },
    {
        "tier": 2,
        "question": "Mode of 7, 8, 7, 9, 7, 10 = ?",
        "answer": "7",
        "choices": ["7", "8", "9", "48"],
        "context": (
            "Mode: most frequent value. Count: 7 appears 3 times; 8, 9, "
            "10 each appear once. Mode = 7. Sort the list first to spot "
            "repeats faster."
        ),
    },
    {
        "tier": 2,
        "question": "Mode of 12, 15, 15, 18, 20 = ?",
        "answer": "15",
        "choices": ["15", "12", "18", "80"],
        "context": (
            "Mode: most frequent value. The 15 appears twice; every other "
            "value appears once. Mode = 15."
        ),
    },
    {
        "tier": 2,
        "question": "Mode of 50, 60, 70, 60, 50, 60 = ?",
        "answer": "60",
        "choices": ["60", "50", "70", "350"],
        "context": (
            "Mode: most frequent value. The 60 appears 3 times; 50 twice; "
            "70 once. Highest count wins: mode = 60."
        ),
    },
    # Range — 5 questions
    {
        "tier": 2,
        "question": "Range of 3, 8, 12, 5, 9 = ?",
        "answer": "9",
        "choices": ["9", "12", "3", "37"],
        "context": (
            "Range: max − min. Max = 12, min = 3. Range = 12 − 3 = 9. "
            "Range measures spread, not a typical value."
        ),
    },
    {
        "tier": 2,
        "question": "Range of 15, 20, 25 = ?",
        "answer": "10",
        "choices": ["10", "5", "25", "60"],
        "context": (
            "Range: max − min. Max = 25, min = 15. Range = 25 − 15 = 10. "
            "Range tells you how spread out the data is."
        ),
    },
    {
        "tier": 2,
        "question": "Range of 90, 60, 80, 30 = ?",
        "answer": "60",
        "choices": ["60", "90", "30", "260"],
        "context": (
            "Range: max − min. Max = 90, min = 30. Range = 90 − 30 = 60. "
            "Use the highest and lowest values, not the middle."
        ),
    },
    {
        "tier": 2,
        "question": "Range of 7, 7, 7, 7 = ?",
        "answer": "0",
        "choices": ["0", "7", "28", "1"],
        "context": (
            "Range: max − min. Max = 7, min = 7. Range = 7 − 7 = 0. "
            "When all values equal, the range is 0 — no spread."
        ),
    },
    {
        "tier": 2,
        "question": "Range of 4, 11, 6, 2, 9 = ?",
        "answer": "9",
        "choices": ["9", "11", "2", "32"],
        "context": (
            "Range: max − min. Max = 11, min = 2. Range = 11 − 2 = 9. "
            "Always find both extremes before subtracting."
        ),
    },
    # Fundamental counting principle — 5 questions
    {
        "tier": 2,
        "question": "3 shirts × 4 pants. How many outfits?",
        "answer": "12",
        "choices": ["12", "7", "10", "16"],
        "context": (
            "Counting principle (multiply choices). For independent "
            "choices, multiply: 3 shirts × 4 pants = 12 outfits. Common "
            "error: adding (3 + 4 = 7) instead of multiplying."
        ),
    },
    {
        "tier": 2,
        "question": "2 entrees × 3 sides × 2 drinks. How many meals?",
        "answer": "12",
        "choices": ["12", "7", "6", "8"],
        "context": (
            "Counting principle (multiply choices). Three independent "
            "choices: 2 × 3 × 2 = 12 meals. Adding (2 + 3 + 2 = 7) is the "
            "common error."
        ),
    },
    {
        "tier": 2,
        "question": "5 routes from A to B; 4 routes from B to C. Total A→C?",
        "answer": "20",
        "choices": ["20", "9", "10", "25"],
        "context": (
            "Counting principle (multiply choices). Each A→B can pair "
            "with each B→C, so multiply: 5 × 4 = 20 routes total. Adding "
            "(5 + 4 = 9) is the common error."
        ),
    },
    {
        "tier": 2,
        "question": "4 hats, 3 scarves, 2 pairs of gloves. Sets?",
        "answer": "24",
        "choices": ["24", "9", "12", "14"],
        "context": (
            "Counting principle (multiply choices). For independent "
            "picks, multiply choices: 4 × 3 × 2 = 24 sets. Adding "
            "(4 + 3 + 2 = 9) is the common error."
        ),
    },
    {
        "tier": 2,
        "question": "6 flavors of ice cream × 3 cones. Combos?",
        "answer": "18",
        "choices": ["18", "9", "12", "21"],
        "context": (
            "Counting principle (multiply choices). Each flavor pairs "
            "with each cone: 6 × 3 = 18 combos. Adding (6 + 3 = 9) is "
            "wrong."
        ),
    },
]


# ---------------------------------------------------------------------------
# T3 — 80 questions: probability basics + compound + complement + sample
# ---------------------------------------------------------------------------
T3_QUESTIONS = [
    # Probability basics — 30 questions
    {
        "tier": 3,
        "question": "Roll a fair die. P(rolling a 4)?",
        "answer": "1/6",
        "choices": ["1/6", "1/4", "4/6", "1/2"],
        "context": (
            "Probability: favorable outcomes / total outcomes. One face "
            "shows 4; six faces total. P = 1/6. A fair die has equally "
            "likely outcomes for each face."
        ),
    },
    {
        "tier": 3,
        "question": "Roll a fair die. P(rolling an even number)?",
        "answer": "1/2",
        "choices": ["1/2", "1/6", "1/3", "2/6"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Even "
            "faces: 2, 4, 6 (three favorable). Total: 6. P = 3/6 = 1/2. "
            "Always reduce probability fractions."
        ),
    },
    {
        "tier": 3,
        "question": "Roll a fair die. P(rolling a number > 4)?",
        "answer": "1/3",
        "choices": ["1/3", "1/6", "2/3", "4/6"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Faces > 4: "
            "5 and 6 (two favorable). Total: 6. P = 2/6 = 1/3. Strict "
            "inequality > 4 excludes 4."
        ),
    },
    {
        "tier": 3,
        "question": "Roll a fair die. P(rolling a 1 or 6)?",
        "answer": "1/3",
        "choices": ["1/3", "1/6", "2/3", "1/2"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Two "
            "favorable faces (1 and 6). Total: 6. P = 2/6 = 1/3. "
            "Reduce: 2/6 = 1/3."
        ),
    },
    {
        "tier": 3,
        "question": "Standard 52-card deck. P(drawing a king)?",
        "answer": "1/13",
        "choices": ["1/13", "1/4", "4/52", "1/52"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Four kings "
            "in 52 cards. P = 4/52 = 1/13. Always reduce — 4/52 is "
            "correct but unreduced."
        ),
    },
    {
        "tier": 3,
        "question": "Standard 52-card deck. P(drawing a heart)?",
        "answer": "1/4",
        "choices": ["1/4", "1/13", "13/52", "1/2"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 13 hearts "
            "in 52 cards. P = 13/52 = 1/4. The four suits each have 13 "
            "cards, so any single suit is 1/4."
        ),
    },
    {
        "tier": 3,
        "question": "Standard 52-card deck. P(drawing a red card)?",
        "answer": "1/2",
        "choices": ["1/2", "1/4", "1/13", "26/52"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Red cards "
            "= hearts + diamonds = 26 of 52. P = 26/52 = 1/2. Always "
            "reduce probability fractions."
        ),
    },
    {
        "tier": 3,
        "question": "Standard 52-card deck. P(drawing an ace)?",
        "answer": "1/13",
        "choices": ["1/13", "1/4", "1/52", "4/13"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Four aces "
            "in 52 cards. P = 4/52 = 1/13. The deck has four of each "
            "rank, so any single rank is 1/13."
        ),
    },
    {
        "tier": 3,
        "question": "Flip a fair coin. P(heads)?",
        "answer": "1/2",
        "choices": ["1/2", "1/4", "1/3", "2/2"],
        "context": (
            "Probability: favorable outcomes / total outcomes. One "
            "favorable side (heads); two sides total. P = 1/2. A fair "
            "coin has equal heads/tails probability."
        ),
    },
    {
        "tier": 3,
        "question": "Bag: 3 red, 2 blue marbles. P(red)?",
        "answer": "3/5",
        "choices": ["3/5", "2/5", "1/3", "3/2"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 3 red; "
            "total = 3 + 2 = 5. P(red) = 3/5. Always add to get total "
            "marbles before computing."
        ),
    },
    {
        "tier": 3,
        "question": "Bag: 4 red, 6 blue marbles. P(blue)?",
        "answer": "3/5",
        "choices": ["3/5", "2/5", "6/10", "3/2"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 6 blue; "
            "total = 10. P = 6/10 = 3/5. Reduce: divide top and bottom "
            "by 2."
        ),
    },
    {
        "tier": 3,
        "question": "Bag: 5 red, 3 green, 2 blue. P(green)?",
        "answer": "3/10",
        "choices": ["3/10", "1/3", "3/5", "2/10"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 3 green; "
            "total = 5 + 3 + 2 = 10. P = 3/10 (already reduced)."
        ),
    },
    {
        "tier": 3,
        "question": "Spinner has 8 equal sections, 3 are red. P(red)?",
        "answer": "3/8",
        "choices": ["3/8", "1/3", "5/8", "1/8"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 3 red "
            "sections; 8 total sections. P = 3/8. Each section equally "
            "likely on a fair spinner."
        ),
    },
    {
        "tier": 3,
        "question": "Spinner has 5 equal sections, 2 win. P(win)?",
        "answer": "2/5",
        "choices": ["2/5", "1/5", "3/5", "2/3"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 2 "
            "favorable; 5 total. P = 2/5. Equal-area spinners use "
            "section counts directly."
        ),
    },
    {
        "tier": 3,
        "question": "Random integer 1-10. P(picking 7)?",
        "answer": "1/10",
        "choices": ["1/10", "1/7", "7/10", "1/2"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 1 way to "
            "pick 7; 10 possible integers. P = 1/10. Each integer "
            "equally likely."
        ),
    },
    {
        "tier": 3,
        "question": "Random integer 1-10. P(picking a multiple of 3)?",
        "answer": "3/10",
        "choices": ["3/10", "1/3", "2/10", "1/10"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Multiples "
            "of 3 in 1-10: 3, 6, 9 (three favorable). P = 3/10."
        ),
    },
    {
        "tier": 3,
        "question": "Random letter from MISSISSIPPI. P(letter is S)?",
        "answer": "4/11",
        "choices": ["4/11", "1/4", "1/11", "4/4"],
        "context": (
            "Probability: favorable outcomes / total outcomes. S appears "
            "4 times; total letters = 11. P = 4/11. Count carefully — "
            "MISSISSIPPI has 4 S's, 4 I's, 2 P's, 1 M."
        ),
    },
    {
        "tier": 3,
        "question": "Random letter from BANANA. P(letter is A)?",
        "answer": "1/2",
        "choices": ["1/2", "1/3", "3/6", "2/6"],
        "context": (
            "Probability: favorable outcomes / total outcomes. A appears "
            "3 times; total letters = 6. P = 3/6 = 1/2. Always reduce."
        ),
    },
    {
        "tier": 3,
        "question": "Bag: 7 cards numbered 1-7. P(picking a 5)?",
        "answer": "1/7",
        "choices": ["1/7", "1/5", "5/7", "2/7"],
        "context": (
            "Probability: favorable outcomes / total outcomes. One 5; "
            "seven cards. P = 1/7. Each numbered card equally likely."
        ),
    },
    {
        "tier": 3,
        "question": "Bag: 7 cards numbered 1-7. P(picking odd)?",
        "answer": "4/7",
        "choices": ["4/7", "3/7", "1/2", "1/7"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Odd "
            "numbers in 1-7: 1, 3, 5, 7 (four favorable). P = 4/7."
        ),
    },
    {
        "tier": 3,
        "question": "Roll a die. P(prime number)?",
        "answer": "1/2",
        "choices": ["1/2", "1/3", "2/6", "1/6"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Primes "
            "on a die: 2, 3, 5 (three favorable). P = 3/6 = 1/2. Note 1 "
            "is NOT prime."
        ),
    },
    {
        "tier": 3,
        "question": "Roll a die. P(rolling less than 3)?",
        "answer": "1/3",
        "choices": ["1/3", "1/6", "1/2", "2/3"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Faces "
            "< 3: 1 and 2 (two favorable). P = 2/6 = 1/3. Strict "
            "inequality excludes 3."
        ),
    },
    {
        "tier": 3,
        "question": "Deck of 52. P(drawing a face card)?",
        "answer": "3/13",
        "choices": ["3/13", "1/4", "12/52", "1/13"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Face "
            "cards (J, Q, K) × 4 suits = 12 cards. P = 12/52 = 3/13. "
            "Always reduce."
        ),
    },
    {
        "tier": 3,
        "question": "Deck of 52. P(drawing a spade)?",
        "answer": "1/4",
        "choices": ["1/4", "1/13", "13/52", "1/2"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 13 "
            "spades in 52 cards. P = 13/52 = 1/4. Reduce: divide top "
            "and bottom by 13."
        ),
    },
    {
        "tier": 3,
        "question": "Jar: 8 marbles, 3 are green. P(green)?",
        "answer": "3/8",
        "choices": ["3/8", "1/3", "5/8", "1/8"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 3 green; "
            "8 total. P = 3/8 (already reduced)."
        ),
    },
    {
        "tier": 3,
        "question": "Jar: 10 marbles, 4 are red. P(red)?",
        "answer": "2/5",
        "choices": ["2/5", "1/4", "4/10", "1/2"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 4 red; "
            "10 total. P = 4/10 = 2/5. Always reduce probability "
            "fractions."
        ),
    },
    {
        "tier": 3,
        "question": "Spinner: 6 sections, 1 wins. P(win)?",
        "answer": "1/6",
        "choices": ["1/6", "1/3", "5/6", "1/5"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 1 "
            "favorable; 6 total. P = 1/6. Equal-area spinner = each "
            "section equally likely."
        ),
    },
    {
        "tier": 3,
        "question": "5 students, 1 chosen at random. P(specific student)?",
        "answer": "1/5",
        "choices": ["1/5", "1/4", "4/5", "1/2"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 1 "
            "specific student; 5 total. P = 1/5. Each student equally "
            "likely on fair random choice."
        ),
    },
    {
        "tier": 3,
        "question": "Roll a 12-sided die. P(rolling a 7)?",
        "answer": "1/12",
        "choices": ["1/12", "1/7", "7/12", "1/6"],
        "context": (
            "Probability: favorable outcomes / total outcomes. One "
            "favorable; 12 sides. P = 1/12. D12 has equal probability "
            "for each face."
        ),
    },
    {
        "tier": 3,
        "question": "Roll a 12-sided die. P(rolling > 8)?",
        "answer": "1/3",
        "choices": ["1/3", "1/4", "1/2", "1/12"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Faces "
            "> 8: 9, 10, 11, 12 (four favorable). P = 4/12 = 1/3. "
            "Reduce fractions."
        ),
    },
    # Compound probability — independent events — 20 questions
    {
        "tier": 3,
        "question": "Flip 2 coins. P(both tails)?",
        "answer": "1/4",
        "choices": ["1/4", "1/2", "1", "2/4"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). P(tails on "
            "coin 1) = 1/2; P(tails on coin 2) = 1/2. P(both) = 1/2 × "
            "1/2 = 1/4. Adding (1/2 + 1/2 = 1) is the common error."
        ),
    },
    {
        "tier": 3,
        "question": "Roll 2 dice. P(both show 6)?",
        "answer": "1/36",
        "choices": ["1/36", "1/6", "1/12", "2/12"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). P(6 on die 1) "
            "= 1/6; P(6 on die 2) = 1/6. P(both 6) = 1/6 × 1/6 = 1/36. "
            "Multiply, don't add."
        ),
    },
    {
        "tier": 3,
        "question": "Roll 2 dice. P(both show 1)?",
        "answer": "1/36",
        "choices": ["1/36", "1/6", "1/12", "2/12"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). P(1 on die 1) "
            "= 1/6; same for die 2. P(both 1) = 1/6 × 1/6 = 1/36. Two "
            "snake-eyes is rare for this reason."
        ),
    },
    {
        "tier": 3,
        "question": "Flip 3 coins. P(all heads)?",
        "answer": "1/8",
        "choices": ["1/8", "1/6", "1/4", "3/8"],
        "context": (
            "Independent events: P(A and B and C) = P(A) × P(B) × P(C). "
            "Each coin: 1/2. P(all heads) = 1/2 × 1/2 × 1/2 = 1/8. "
            "Three independents → cube the single-event probability."
        ),
    },
    {
        "tier": 3,
        "question": "Roll 2 dice. P(both show even)?",
        "answer": "1/4",
        "choices": ["1/4", "1/2", "1/3", "1/6"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). P(even on die "
            "1) = 1/2; same for die 2. P(both even) = 1/2 × 1/2 = 1/4. "
            "Adding (1) is the common error."
        ),
    },
    {
        "tier": 3,
        "question": "Spinner 50% wins. Spin twice. P(both win)?",
        "answer": "1/4",
        "choices": ["1/4", "1/2", "1", "3/4"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). Each spin: "
            "1/2. P(both wins) = 1/2 × 1/2 = 1/4. Adding (1) misses the "
            "multiplication rule."
        ),
    },
    {
        "tier": 3,
        "question": "Coin and die. P(heads AND 6)?",
        "answer": "1/12",
        "choices": ["1/12", "1/6", "1/8", "2/12"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). P(heads) = "
            "1/2; P(6 on die) = 1/6. P(both) = 1/2 × 1/6 = 1/12. "
            "Multiply across different experiments."
        ),
    },
    {
        "tier": 3,
        "question": "Two bags, each 1/3 chance of red. P(both red)?",
        "answer": "1/9",
        "choices": ["1/9", "2/3", "1/3", "2/9"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). Each bag: "
            "1/3. P(both red) = 1/3 × 1/3 = 1/9. Adding (2/3) is the "
            "common error."
        ),
    },
    {
        "tier": 3,
        "question": "Roll 2 dice. P(die 1 is 3 AND die 2 is 5)?",
        "answer": "1/36",
        "choices": ["1/36", "1/6", "2/12", "1/12"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). Each "
            "specific face: 1/6. P(specific pair) = 1/6 × 1/6 = 1/36. "
            "Each ordered pair has probability 1/36."
        ),
    },
    {
        "tier": 3,
        "question": "Flip 2 coins. P(HT in order)?",
        "answer": "1/4",
        "choices": ["1/4", "1/2", "1/8", "2/4"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). P(H first) = "
            "1/2; P(T second) = 1/2. P(HT) = 1/2 × 1/2 = 1/4. Each "
            "ordered 2-flip outcome is 1/4."
        ),
    },
    {
        "tier": 3,
        "question": "Spinner: P(red) = 1/4. Spin 2 times. P(both red)?",
        "answer": "1/16",
        "choices": ["1/16", "1/2", "1/8", "2/4"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). Each spin: "
            "1/4. P(both red) = 1/4 × 1/4 = 1/16. Adding (1/2) misses "
            "the multiplication."
        ),
    },
    {
        "tier": 3,
        "question": "P(win) = 2/3. Play 2 times. P(both wins)?",
        "answer": "4/9",
        "choices": ["4/9", "2/3", "1/3", "4/3"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). P(each "
            "win) = 2/3. P(both wins) = 2/3 × 2/3 = 4/9. Multiply tops "
            "and bottoms."
        ),
    },
    {
        "tier": 3,
        "question": "P(rain) = 1/3 each day. P(rain both days)?",
        "answer": "1/9",
        "choices": ["1/9", "2/3", "1/3", "2/9"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). Each day: "
            "1/3 if independent. P(both rainy) = 1/3 × 1/3 = 1/9. Real "
            "weather isn't fully independent, but the math assumes it."
        ),
    },
    {
        "tier": 3,
        "question": "Flip 5 coins. P(all heads)?",
        "answer": "1/32",
        "choices": ["1/32", "1/16", "1/10", "5/32"],
        "context": (
            "Independent events: P(A and B and C and D and E) = product. "
            "Each coin: 1/2. P(all heads) = (1/2)⁵ = 1/32. Each "
            "additional flip halves the probability."
        ),
    },
    {
        "tier": 3,
        "question": "Roll 2 dice. P(sum equals 2)?",
        "answer": "1/36",
        "choices": ["1/36", "1/6", "1/12", "2/36"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). Sum equals "
            "2 requires both dice show 1. P = 1/6 × 1/6 = 1/36. Only "
            "one (1,1) pair gives sum 2."
        ),
    },
    {
        "tier": 3,
        "question": "Bag: 1/2 chance red. Draw with replacement, twice. P(both red)?",
        "answer": "1/4",
        "choices": ["1/4", "1/2", "1", "3/4"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). With "
            "replacement keeps probabilities independent. P(both red) "
            "= 1/2 × 1/2 = 1/4."
        ),
    },
    {
        "tier": 3,
        "question": "Coin and spinner (1/3 win). P(heads AND win)?",
        "answer": "1/6",
        "choices": ["1/6", "1/2", "1/3", "5/6"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). P(heads) = "
            "1/2; P(win) = 1/3. P(both) = 1/2 × 1/3 = 1/6. Multiply "
            "across different experiments."
        ),
    },
    {
        "tier": 3,
        "question": "Three dice. P(all show 6)?",
        "answer": "1/216",
        "choices": ["1/216", "1/36", "1/6", "3/216"],
        "context": (
            "Independent events: product of three single-event "
            "probabilities. Each die: 1/6. P(all 6) = (1/6)³ = 1/216. "
            "Triple sixes is very rare."
        ),
    },
    {
        "tier": 3,
        "question": "P(A) = 1/2, P(B) = 1/3, independent. P(A and B)?",
        "answer": "1/6",
        "choices": ["1/6", "5/6", "1/3", "1/2"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B) = 1/2 × 1/3 "
            "= 1/6. Multiply tops, multiply bottoms. Adding (5/6) is "
            "the OR error."
        ),
    },
    {
        "tier": 3,
        "question": "Two spinners, each 1/2 red. P(both red)?",
        "answer": "1/4",
        "choices": ["1/4", "1/2", "1", "3/4"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). Each "
            "spinner: 1/2. P(both red) = 1/2 × 1/2 = 1/4. Multiply, "
            "don't add."
        ),
    },
    # Complement rule — 10 questions
    {
        "tier": 3,
        "question": "P(A) = 1/4. P(not A)?",
        "answer": "3/4",
        "choices": ["3/4", "1/4", "1/2", "4/3"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 1/4 = 3/4. The "
            "complement is everything OTHER than A. Probabilities of A "
            "and not A sum to 1."
        ),
    },
    {
        "tier": 3,
        "question": "P(rain) = 0.3. P(no rain)?",
        "answer": "0.7",
        "choices": ["0.7", "0.3", "0.6", "1.3"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 0.3 = 0.7. "
            "Decimal form works the same as fractions — A and not A "
            "sum to 1.0."
        ),
    },
    {
        "tier": 3,
        "question": "P(win) = 2/5. P(not win)?",
        "answer": "3/5",
        "choices": ["3/5", "2/5", "1/5", "5/2"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 2/5 = 5/5 − 2/5 "
            "= 3/5. Subtract from 1 by converting 1 to the same "
            "denominator first."
        ),
    },
    {
        "tier": 3,
        "question": "P(rolling 6) = 1/6. P(NOT rolling 6)?",
        "answer": "5/6",
        "choices": ["5/6", "1/6", "1/2", "6/5"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 1/6 = 6/6 − 1/6 "
            "= 5/6. Five faces aren't 6, out of six total."
        ),
    },
    {
        "tier": 3,
        "question": "P(heads) = 1/2. P(NOT heads)?",
        "answer": "1/2",
        "choices": ["1/2", "0", "1", "3/2"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 1/2 = 1/2. "
            "For a fair coin, heads and tails are each other's "
            "complement."
        ),
    },
    {
        "tier": 3,
        "question": "P(red marble) = 3/8. P(NOT red)?",
        "answer": "5/8",
        "choices": ["5/8", "3/8", "1/8", "8/3"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 3/8 = 8/8 − 3/8 "
            "= 5/8. Five marbles are not red, out of 8 total."
        ),
    },
    {
        "tier": 3,
        "question": "P(picking ace) = 1/13. P(NOT ace)?",
        "answer": "12/13",
        "choices": ["12/13", "1/13", "4/13", "13/12"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 1/13 = 13/13 − "
            "1/13 = 12/13. 12 out of 13 ranks are not aces."
        ),
    },
    {
        "tier": 3,
        "question": "P(team wins) = 0.6. P(team loses)?",
        "answer": "0.4",
        "choices": ["0.4", "0.6", "1", "0.5"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 0.6 = 0.4. "
            "If wins and losses are the only outcomes, they're "
            "complements that sum to 1."
        ),
    },
    {
        "tier": 3,
        "question": "P(blue) = 7/10. P(NOT blue)?",
        "answer": "3/10",
        "choices": ["3/10", "7/10", "1/10", "10/3"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 7/10 = 3/10. "
            "Three out of ten are not blue."
        ),
    },
    {
        "tier": 3,
        "question": "P(prime on die) = 1/2. P(NOT prime)?",
        "answer": "1/2",
        "choices": ["1/2", "1/3", "1/6", "2/3"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 1/2 = 1/2. "
            "Primes on a die are 2, 3, 5 (three faces); non-primes are "
            "1, 4, 6 (also three faces)."
        ),
    },
    # Theoretical vs experimental — 5 questions
    {
        "tier": 3,
        "question": "Coin flipped 100 times: 53 heads. Experimental P(heads)?",
        "answer": "53/100",
        "choices": ["53/100", "1/2", "47/100", "53/47"],
        "context": (
            "Experimental probability: observed outcomes / trials. 53 "
            "heads in 100 flips → 53/100. Theoretical P(heads) for a "
            "fair coin = 1/2; experimental wobbles around it."
        ),
    },
    {
        "tier": 3,
        "question": "Die rolled 60 times: 12 sixes. Experimental P(6)?",
        "answer": "1/5",
        "choices": ["1/5", "1/6", "12/60", "1/12"],
        "context": (
            "Experimental probability: observed / trials. 12/60 = 1/5. "
            "Theoretical P(6) for fair die = 1/6; experimental of 1/5 "
            "is slightly high — small samples wobble."
        ),
    },
    {
        "tier": 3,
        "question": "200 spins, 50 wins. Experimental P(win)?",
        "answer": "1/4",
        "choices": ["1/4", "1/2", "1/5", "50/200"],
        "context": (
            "Experimental probability: observed / trials. 50/200 = 1/4. "
            "Always reduce. Experimental probability gets closer to "
            "theoretical with more trials."
        ),
    },
    {
        "tier": 3,
        "question": "Bag drawn 40 times, 8 red. Experimental P(red)?",
        "answer": "1/5",
        "choices": ["1/5", "1/8", "8/40", "1/4"],
        "context": (
            "Experimental probability: observed / trials. 8/40 = 1/5. "
            "Reduce by dividing top and bottom by 8."
        ),
    },
    {
        "tier": 3,
        "question": "Theoretical P(red) = 1/3. 90 trials. Expected reds?",
        "answer": "30",
        "choices": ["30", "60", "10", "90"],
        "context": (
            "Expected count = probability × trials. 1/3 × 90 = 30. "
            "Theoretical probability predicts long-run frequencies — "
            "actual experimental counts will wobble around 30."
        ),
    },
    # Sample-based estimation — 5 questions
    {
        "tier": 3,
        "question": "Sample of 50 fish: 10 tagged. Tagged proportion?",
        "answer": "1/5",
        "choices": ["1/5", "1/10", "10/50", "1/50"],
        "context": (
            "Sample-based estimation: tagged proportion = tagged / "
            "sample size = 10/50 = 1/5. Used in capture-recapture to "
            "estimate total population size."
        ),
    },
    {
        "tier": 3,
        "question": "Poll of 200: 150 yes. Estimated P(yes)?",
        "answer": "3/4",
        "choices": ["3/4", "1/2", "150/200", "1/4"],
        "context": (
            "Sample-based estimation: yes-proportion = 150/200 = 3/4. "
            "Reduce fractions. Larger samples give more reliable "
            "estimates of true population proportion."
        ),
    },
    {
        "tier": 3,
        "question": "100 surveyed, 65 said yes. Estimated yes-percentage?",
        "answer": "65%",
        "choices": ["65%", "35%", "50%", "13%"],
        "context": (
            "Sample-based estimation. Yes-percentage = 65/100 = 65%. "
            "Converting fraction to percent: multiply by 100. The "
            "complement (35%) said no."
        ),
    },
    {
        "tier": 3,
        "question": "30 cars sampled; 6 are red. Estimated P(red car)?",
        "answer": "1/5",
        "choices": ["1/5", "1/6", "6/30", "1/3"],
        "context": (
            "Sample-based estimation: red proportion = 6/30 = 1/5. "
            "Reduce fractions. Sample estimates the true proportion in "
            "the population of all cars."
        ),
    },
    {
        "tier": 3,
        "question": "Sample of 80: 20 left-handed. Estimated proportion?",
        "answer": "1/4",
        "choices": ["1/4", "1/5", "20/80", "1/20"],
        "context": (
            "Sample-based estimation: left-handed proportion = 20/80 = "
            "1/4. Reduce fractions. National data suggests ~10% are "
            "left-handed — this sample is high."
        ),
    },
    # Additional T3 — more probability + compound + complement
    {
        "tier": 3,
        "question": "Roll a die. P(rolling 1 or 2)?",
        "answer": "1/3",
        "choices": ["1/3", "1/6", "2/3", "1/2"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Two "
            "favorable faces (1 and 2); total 6. P = 2/6 = 1/3. Reduce "
            "the fraction."
        ),
    },
    {
        "tier": 3,
        "question": "Deck of 52. P(drawing a club)?",
        "answer": "1/4",
        "choices": ["1/4", "1/13", "1/52", "13/52"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 13 clubs "
            "in 52 cards. P = 13/52 = 1/4. Each suit covers a quarter "
            "of the deck."
        ),
    },
    {
        "tier": 3,
        "question": "Bag: 5 red, 5 blue, 3 yellow. P(yellow)?",
        "answer": "3/13",
        "choices": ["3/13", "1/4", "3/10", "1/3"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 3 "
            "yellow; total = 13. P = 3/13 (already reduced — 3 and 13 "
            "share no factor)."
        ),
    },
    {
        "tier": 3,
        "question": "Spinner: 10 sections, 7 win. P(win)?",
        "answer": "7/10",
        "choices": ["7/10", "3/10", "1/7", "1/10"],
        "context": (
            "Probability: favorable outcomes / total outcomes. 7 "
            "favorable; 10 total. P = 7/10 (already reduced)."
        ),
    },
    {
        "tier": 3,
        "question": "Roll 2 dice. P(both odd)?",
        "answer": "1/4",
        "choices": ["1/4", "1/2", "1/3", "1/6"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). P(odd on "
            "die 1) = 3/6 = 1/2; same for die 2. P(both odd) = 1/2 × "
            "1/2 = 1/4."
        ),
    },
    {
        "tier": 3,
        "question": "P(rolling 3) = 1/6. P(NOT rolling 3)?",
        "answer": "5/6",
        "choices": ["5/6", "1/6", "1/2", "6/5"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 1/6 = 5/6. "
            "Five out of six faces are not 3."
        ),
    },
    {
        "tier": 3,
        "question": "P(picking face card) = 3/13. P(NOT face card)?",
        "answer": "10/13",
        "choices": ["10/13", "3/13", "1/13", "13/10"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 3/13 = 13/13 − "
            "3/13 = 10/13. Most cards (10/13 of ranks) are not face "
            "cards."
        ),
    },
    {
        "tier": 3,
        "question": "Flip a coin and roll a die. P(tails AND 4)?",
        "answer": "1/12",
        "choices": ["1/12", "1/6", "1/2", "2/12"],
        "context": (
            "Independent events: P(A and B) = P(A) × P(B). P(tails) = "
            "1/2; P(4) = 1/6. P(both) = 1/2 × 1/6 = 1/12. Multiply "
            "across different experiments."
        ),
    },
    {
        "tier": 3,
        "question": "Roll 2 dice. P(sum equals 8)?",
        "answer": "5/36",
        "choices": ["5/36", "1/6", "1/36", "8/36"],
        "context": (
            "Probability: favorable outcomes / total outcomes. Pairs "
            "summing to 8: (2,6), (3,5), (4,4), (5,3), (6,2) — five "
            "pairs. Total: 36. P = 5/36."
        ),
    },
    {
        "tier": 3,
        "question": "P(rain) = 0.4. P(no rain)?",
        "answer": "0.6",
        "choices": ["0.6", "0.4", "0.5", "1.4"],
        "context": (
            "Complement rule: P(not A) = 1 − P(A). 1 − 0.4 = 0.6. "
            "Decimal form follows same rule — A and not A sum to 1.0."
        ),
    },
]


# ---------------------------------------------------------------------------
# T4 — 70 questions: simple interest, scatterplots, bivariate, outliers
# ---------------------------------------------------------------------------
T4_QUESTIONS = [
    # Simple interest — 25 questions
    {
        "tier": 4,
        "question": "$1000 at 5% simple interest for 2 years. Interest earned?",
        "answer": "$100",
        "choices": ["$100", "$50", "$200", "$1100"],
        "context": (
            "Simple interest: I = Prt. P = 1000, r = 0.05, t = 2. "
            "I = 1000 × 0.05 × 2 = 100. Common error: forgetting to "
            "multiply by time (gives $50 — one year's interest)."
        ),
    },
    {
        "tier": 4,
        "question": "$500 at 4% simple interest for 3 years. Interest?",
        "answer": "$60",
        "choices": ["$60", "$20", "$120", "$240"],
        "context": (
            "Simple interest: I = Prt. P = 500, r = 0.04, t = 3. "
            "I = 500 × 0.04 × 3 = 60. Common error: applying compound "
            "interest formula gives a slightly different number."
        ),
    },
    {
        "tier": 4,
        "question": "$2000 at 3% simple interest for 5 years. Interest?",
        "answer": "$300",
        "choices": ["$300", "$60", "$200", "$600"],
        "context": (
            "Simple interest: I = Prt. P = 2000, r = 0.03, t = 5. "
            "I = 2000 × 0.03 × 5 = 300. Common error: $60 (one year's "
            "interest only)."
        ),
    },
    {
        "tier": 4,
        "question": "$800 at 6% simple interest for 4 years. Interest?",
        "answer": "$192",
        "choices": ["$192", "$48", "$96", "$384"],
        "context": (
            "Simple interest: I = Prt. P = 800, r = 0.06, t = 4. "
            "I = 800 × 0.06 × 4 = 192. Convert percent to decimal: 6% "
            "= 0.06."
        ),
    },
    {
        "tier": 4,
        "question": "$1500 at 8% simple interest for 1 year. Interest?",
        "answer": "$120",
        "choices": ["$120", "$60", "$240", "$1620"],
        "context": (
            "Simple interest: I = Prt. P = 1500, r = 0.08, t = 1. "
            "I = 1500 × 0.08 × 1 = 120. Common error: $1620 mixes up "
            "interest with total amount."
        ),
    },
    {
        "tier": 4,
        "question": "$2500 at 4% simple interest for 2 years. Interest?",
        "answer": "$200",
        "choices": ["$200", "$100", "$400", "$300"],
        "context": (
            "Simple interest: I = Prt. P = 2500, r = 0.04, t = 2. "
            "I = 2500 × 0.04 × 2 = 200. Always convert the percent to "
            "decimal before multiplying."
        ),
    },
    {
        "tier": 4,
        "question": "$400 at 7% simple interest for 3 years. Interest?",
        "answer": "$84",
        "choices": ["$84", "$28", "$112", "$168"],
        "context": (
            "Simple interest: I = Prt. P = 400, r = 0.07, t = 3. "
            "I = 400 × 0.07 × 3 = 84. Common error: $28 (one year) or "
            "$168 (six years)."
        ),
    },
    {
        "tier": 4,
        "question": "$1200 at 5% simple interest for 4 years. Interest?",
        "answer": "$240",
        "choices": ["$240", "$60", "$120", "$480"],
        "context": (
            "Simple interest: I = Prt. P = 1200, r = 0.05, t = 4. "
            "I = 1200 × 0.05 × 4 = 240. Common error: $60 (one year)."
        ),
    },
    {
        "tier": 4,
        "question": "$600 at 10% simple interest for 2 years. Interest?",
        "answer": "$120",
        "choices": ["$120", "$60", "$240", "$720"],
        "context": (
            "Simple interest: I = Prt. P = 600, r = 0.10, t = 2. "
            "I = 600 × 0.10 × 2 = 120. The 10% trick: 10% of 600 = 60; "
            "times 2 years = 120."
        ),
    },
    {
        "tier": 4,
        "question": "$3000 at 4% simple interest for 1 year. Interest?",
        "answer": "$120",
        "choices": ["$120", "$60", "$240", "$3120"],
        "context": (
            "Simple interest: I = Prt. P = 3000, r = 0.04, t = 1. "
            "I = 3000 × 0.04 × 1 = 120. Common error: $3120 mixes "
            "interest with total."
        ),
    },
    {
        "tier": 4,
        "question": "$5000 at 2% simple interest for 3 years. Interest?",
        "answer": "$300",
        "choices": ["$300", "$100", "$500", "$600"],
        "context": (
            "Simple interest: I = Prt. P = 5000, r = 0.02, t = 3. "
            "I = 5000 × 0.02 × 3 = 300. Common error: $100 (one year's "
            "interest)."
        ),
    },
    {
        "tier": 4,
        "question": "$750 at 6% simple interest for 2 years. Interest?",
        "answer": "$90",
        "choices": ["$90", "$45", "$180", "$135"],
        "context": (
            "Simple interest: I = Prt. P = 750, r = 0.06, t = 2. "
            "I = 750 × 0.06 × 2 = 90. Convert: 6% = 0.06."
        ),
    },
    {
        "tier": 4,
        "question": "$10000 at 3% simple interest for 5 years. Interest?",
        "answer": "$1500",
        "choices": ["$1500", "$300", "$500", "$3000"],
        "context": (
            "Simple interest: I = Prt. P = 10000, r = 0.03, t = 5. "
            "I = 10000 × 0.03 × 5 = 1500. Common error: $300 (one "
            "year's interest)."
        ),
    },
    {
        "tier": 4,
        "question": "$200 at 5% simple interest for 6 years. Interest?",
        "answer": "$60",
        "choices": ["$60", "$10", "$30", "$120"],
        "context": (
            "Simple interest: I = Prt. P = 200, r = 0.05, t = 6. "
            "I = 200 × 0.05 × 6 = 60. Common error: $10 (one year)."
        ),
    },
    {
        "tier": 4,
        "question": "$4000 at 5% simple interest for 3 years. Interest?",
        "answer": "$600",
        "choices": ["$600", "$200", "$400", "$1200"],
        "context": (
            "Simple interest: I = Prt. P = 4000, r = 0.05, t = 3. "
            "I = 4000 × 0.05 × 3 = 600. Common error: $200 (one year)."
        ),
    },
    {
        "tier": 4,
        "question": "$900 at 4% simple interest for 5 years. Interest?",
        "answer": "$180",
        "choices": ["$180", "$36", "$90", "$360"],
        "context": (
            "Simple interest: I = Prt. P = 900, r = 0.04, t = 5. "
            "I = 900 × 0.04 × 5 = 180. Common error: $36 (one year)."
        ),
    },
    {
        "tier": 4,
        "question": "$1000 at 6% simple interest for 2 years. Total amount?",
        "answer": "$1120",
        "choices": ["$1120", "$120", "$1060", "$1200"],
        "context": (
            "Simple interest total: A = P + I = P + Prt. P = 1000, "
            "I = 1000 × 0.06 × 2 = 120. A = 1000 + 120 = 1120. The $120 "
            "alone is only the interest."
        ),
    },
    {
        "tier": 4,
        "question": "$500 at 4% simple interest for 2 years. Total?",
        "answer": "$540",
        "choices": ["$540", "$40", "$520", "$580"],
        "context": (
            "Simple interest total: A = P + I. I = 500 × 0.04 × 2 = "
            "40. A = 500 + 40 = 540. Common error: $40 reports interest "
            "only, not total."
        ),
    },
    {
        "tier": 4,
        "question": "$1000 at 5% simple interest for 3 years. Total amount?",
        "answer": "$1150",
        "choices": ["$1150", "$150", "$1050", "$1500"],
        "context": (
            "Simple interest total: A = P + I = P + Prt. I = 1000 × "
            "0.05 × 3 = 150. A = 1000 + 150 = 1150. Always check "
            "whether the problem asks for interest or total."
        ),
    },
    {
        "tier": 4,
        "question": "$2000 at 4% simple interest for 5 years. Total amount?",
        "answer": "$2400",
        "choices": ["$2400", "$400", "$2080", "$3000"],
        "context": (
            "Simple interest total: A = P + I. I = 2000 × 0.04 × 5 = "
            "400. A = 2000 + 400 = 2400. Common error: $400 reports "
            "only interest."
        ),
    },
    {
        "tier": 4,
        "question": "$1500 at 6% simple interest for 4 years. Total amount?",
        "answer": "$1860",
        "choices": ["$1860", "$360", "$1590", "$2000"],
        "context": (
            "Simple interest total: A = P + I. I = 1500 × 0.06 × 4 = "
            "360. A = 1500 + 360 = 1860. Don't confuse with compound "
            "interest."
        ),
    },
    {
        "tier": 4,
        "question": "$800 at 5% simple interest for 4 years. Total amount?",
        "answer": "$960",
        "choices": ["$960", "$160", "$840", "$1000"],
        "context": (
            "Simple interest total: A = P + I. I = 800 × 0.05 × 4 = "
            "160. A = 800 + 160 = 960. Total = principal + interest."
        ),
    },
    {
        "tier": 4,
        "question": "$2500 at 3% simple interest for 6 years. Total amount?",
        "answer": "$2950",
        "choices": ["$2950", "$450", "$2575", "$3000"],
        "context": (
            "Simple interest total: A = P + I. I = 2500 × 0.03 × 6 = "
            "450. A = 2500 + 450 = 2950. The $450 alone is interest."
        ),
    },
    {
        "tier": 4,
        "question": "$1000 at 4% simple interest for 6 months. Interest?",
        "answer": "$20",
        "choices": ["$20", "$40", "$10", "$240"],
        "context": (
            "Simple interest: I = Prt. P = 1000, r = 0.04, t = 0.5 "
            "year. I = 1000 × 0.04 × 0.5 = 20. Convert months to years "
            "first: 6 months = 0.5 years."
        ),
    },
    {
        "tier": 4,
        "question": "$2000 at 5% simple interest for 18 months. Interest?",
        "answer": "$150",
        "choices": ["$150", "$100", "$300", "$1800"],
        "context": (
            "Simple interest: I = Prt. P = 2000, r = 0.05, t = 1.5 "
            "years (18 months = 1.5 years). I = 2000 × 0.05 × 1.5 = "
            "150. Convert months to years first."
        ),
    },
    # Mean/median for data sets — 10 questions
    {
        "tier": 4,
        "question": "Mean of 12, 18, 22, 28, 30 = ?",
        "answer": "22",
        "choices": ["22", "20", "24", "110"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 12 + 18 + 22 + 28 + 30 = "
            "110. Count: 5. Mean = 110 ÷ 5 = 22. Common error: $110 "
            "reports the sum."
        ),
    },
    {
        "tier": 4,
        "question": "Median of test scores 65, 78, 82, 91, 95 = ?",
        "answer": "82",
        "choices": ["82", "78", "91", "411"],
        "context": (
            "Median: middle value when sorted. Already sorted: 65, 78, "
            "82, 91, 95. Middle of 5 is the 3rd: 82. Common error: 411 "
            "is the sum, not the median."
        ),
    },
    {
        "tier": 4,
        "question": "Mean of 5, 10, 15, 20, 25, 30 = ?",
        "answer": "17.5",
        "choices": ["17.5", "15", "20", "105"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 5 + 10 + 15 + 20 + 25 + "
            "30 = 105. Count: 6. Mean = 105 ÷ 6 = 17.5. Even count "
            "with evenly-spaced data → mean between two middle values."
        ),
    },
    {
        "tier": 4,
        "question": "Median of 2, 4, 6, 8, 10, 12, 14 = ?",
        "answer": "8",
        "choices": ["8", "7", "9", "56"],
        "context": (
            "Median: middle value when sorted. Already sorted: 7 values, "
            "middle is the 4th: 8. Odd count → exact middle. Common "
            "error: 56 is the sum."
        ),
    },
    {
        "tier": 4,
        "question": "Mean of 8, 12, 16, 20, 24 = ?",
        "answer": "16",
        "choices": ["16", "12", "20", "80"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 8 + 12 + 16 + 20 + 24 = "
            "80. Count: 5. Mean = 80 ÷ 5 = 16. Evenly-spaced → mean = "
            "middle value."
        ),
    },
    {
        "tier": 4,
        "question": "Median of 100, 200, 300, 400 = ?",
        "answer": "250",
        "choices": ["250", "200", "300", "1000"],
        "context": (
            "Median: middle value when sorted. Even count of 4: average "
            "the two middle values: (200 + 300) ÷ 2 = 250. Common error: "
            "1000 is the sum."
        ),
    },
    {
        "tier": 4,
        "question": "Mean of 15, 25, 35, 45 = ?",
        "answer": "30",
        "choices": ["30", "25", "35", "120"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 15 + 25 + 35 + 45 = 120. "
            "Count: 4. Mean = 120 ÷ 4 = 30. Mean of evenly-spaced = "
            "average of first and last."
        ),
    },
    {
        "tier": 4,
        "question": "Median of 50, 70, 90, 110, 130 = ?",
        "answer": "90",
        "choices": ["90", "70", "110", "450"],
        "context": (
            "Median: middle value when sorted. Already sorted: 5 values, "
            "middle is the 3rd: 90. Common error: 450 is the sum."
        ),
    },
    {
        "tier": 4,
        "question": "Mean of 21, 33, 45, 57, 69 = ?",
        "answer": "45",
        "choices": ["45", "33", "57", "225"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 21 + 33 + 45 + 57 + 69 = "
            "225. Count: 5. Mean = 225 ÷ 5 = 45. Evenly-spaced → mean "
            "= middle."
        ),
    },
    {
        "tier": 4,
        "question": "Median of 11, 23, 35, 47, 59, 71 = ?",
        "answer": "41",
        "choices": ["41", "35", "47", "246"],
        "context": (
            "Median: middle value when sorted. Even count of 6: average "
            "two middle values: (35 + 47) ÷ 2 = 41. Common error: 246 "
            "is the sum."
        ),
    },
    # Bivariate data / scatterplots conceptually — 10 questions
    {
        "tier": 4,
        "question": "Scatterplot: as x grows, y grows. Correlation type?",
        "answer": "positive",
        "choices": ["positive", "negative", "no correlation", "perfect"],
        "context": (
            "Scatterplot correlation: positive correlation means the line "
            "of best fit has positive slope (rise over run > 0) — both "
            "variables increase together. Negative correlation means "
            "negative slope. No correlation means no trend."
        ),
    },
    {
        "tier": 4,
        "question": "Scatterplot: as x grows, y drops. Correlation type?",
        "answer": "negative",
        "choices": ["negative", "positive", "no correlation", "zero"],
        "context": (
            "Scatterplot correlation: negative correlation means line of "
            "best fit has negative slope (rise over run < 0). Positive "
            "correlation has positive slope. The slope sign tells you "
            "the correlation direction."
        ),
    },
    {
        "tier": 4,
        "question": "Scatterplot: points scattered randomly. Correlation?",
        "answer": "no correlation",
        "choices": ["no correlation", "positive", "negative", "perfect"],
        "context": (
            "Scatterplot correlation: random scatter means no slope "
            "trend — no correlation. Knowing x tells you nothing about "
            "y. Correlation requires a visible direction in the cloud "
            "of points (positive or negative slope)."
        ),
    },
    {
        "tier": 4,
        "question": "Hours studied vs test score, upward trend. Correlation?",
        "answer": "positive",
        "choices": ["positive", "negative", "no correlation", "causal"],
        "context": (
            "Scatterplot correlation: upward trend → positive slope → "
            "positive correlation. Both variables grow together. Note: "
            "correlation ≠ causation; the trend doesn't prove study "
            "time CAUSES the score."
        ),
    },
    {
        "tier": 4,
        "question": "Outside temperature vs hot-cocoa sales. Correlation?",
        "answer": "negative",
        "choices": ["negative", "positive", "no correlation", "zero"],
        "context": (
            "Scatterplot correlation: as temperature rises, cocoa sales "
            "fall → downward trend → negative slope → negative "
            "correlation. Real-world variables often have intuitive "
            "directions you can predict."
        ),
    },
    {
        "tier": 4,
        "question": "Line of best fit: y = 2x + 5. Predict y when x = 10.",
        "answer": "25",
        "choices": ["25", "20", "15", "30"],
        "context": (
            "Line of best fit: substitute x = 10 into y = 2x + 5. y = "
            "2(10) + 5 = 20 + 5 = 25. Slope-intercept form lets you "
            "predict y from x."
        ),
    },
    {
        "tier": 4,
        "question": "Line of best fit: y = 3x − 4. Predict y when x = 6.",
        "answer": "14",
        "choices": ["14", "18", "22", "10"],
        "context": (
            "Line of best fit: substitute x = 6 into y = 3x − 4. y = "
            "3(6) − 4 = 18 − 4 = 14. Slope-intercept form for "
            "predictions."
        ),
    },
    {
        "tier": 4,
        "question": "Scatterplot of shoe size vs height: positive trend. Best fit?",
        "answer": "linear with positive slope",
        "choices": [
            "linear with positive slope",
            "linear with negative slope",
            "no relationship",
            "perfectly horizontal",
        ],
        "context": (
            "Line of best fit captures the trend's slope. Positive "
            "trend → positive slope. Real shoe size and height data "
            "have a strong positive correlation, so the fit line rises "
            "left to right."
        ),
    },
    {
        "tier": 4,
        "question": "Plot: ice cream sales vs sunny-day count. Correlation?",
        "answer": "positive",
        "choices": ["positive", "negative", "no correlation", "causal"],
        "context": (
            "Scatterplot correlation: more sunny days → more ice "
            "cream sales → positive slope → positive correlation. Both "
            "grow together. Correlation alone doesn't prove which "
            "causes which."
        ),
    },
    {
        "tier": 4,
        "question": "Scatterplot of TV hours vs test grades, downward trend. Correlation?",
        "answer": "negative",
        "choices": ["negative", "positive", "no correlation", "perfect"],
        "context": (
            "Scatterplot correlation: downward trend → negative slope "
            "→ negative correlation. As TV hours grow, test grades "
            "drop. Real datasets often show this pattern in the line "
            "of best fit."
        ),
    },
    # Box-and-whisker basics — 5 questions
    {
        "tier": 4,
        "question": "Five-number summary 10, 20, 30, 40, 50. Median?",
        "answer": "30",
        "choices": ["30", "20", "40", "10"],
        "context": (
            "Five-number summary: min, Q1, median, Q3, max. Middle "
            "value is the median = 30. Box-and-whisker plots show all "
            "five numbers visually."
        ),
    },
    {
        "tier": 4,
        "question": "Min 5, Q1 15, median 25, Q3 35, max 45. IQR?",
        "answer": "20",
        "choices": ["20", "40", "30", "10"],
        "context": (
            "Interquartile range (IQR) = Q3 − Q1 = 35 − 15 = 20. IQR "
            "measures the spread of the middle 50% of data — less "
            "sensitive to outliers than the full range."
        ),
    },
    {
        "tier": 4,
        "question": "Five-number summary 2, 6, 10, 14, 18. Range?",
        "answer": "16",
        "choices": ["16", "8", "20", "10"],
        "context": (
            "Range = max − min = 18 − 2 = 16. Range covers all data; "
            "IQR (Q3 − Q1 = 14 − 6 = 8) covers just the middle 50%."
        ),
    },
    {
        "tier": 4,
        "question": "Q1 = 12, Q3 = 28. IQR = ?",
        "answer": "16",
        "choices": ["16", "40", "20", "8"],
        "context": (
            "Interquartile range (IQR) = Q3 − Q1 = 28 − 12 = 16. The "
            "middle 50% of data spans 16 units. Adding Q1 + Q3 gives "
            "40 — the common error."
        ),
    },
    {
        "tier": 4,
        "question": "Five-number summary 1, 4, 7, 12, 20. IQR?",
        "answer": "8",
        "choices": ["8", "19", "11", "6"],
        "context": (
            "Interquartile range (IQR) = Q3 − Q1 = 12 − 4 = 8. Range "
            "is max − min = 19. IQR ignores the extremes; range "
            "includes them."
        ),
    },
    # Outlier identification — 5 questions
    {
        "tier": 4,
        "question": "Data: 10, 12, 14, 13, 11, 95. Outlier present?",
        "answer": "yes, 95",
        "choices": ["yes, 95", "no outlier", "yes, 14", "yes, 10"],
        "context": (
            "Outlier: a value far from the bulk of the data. Range = "
            "95 − 10 = 85. Most values cluster around 10-14; 95 is far "
            "away. Outliers distort the mean but barely move the median."
        ),
    },
    {
        "tier": 4,
        "question": "Set: 50, 52, 51, 49, 5, 53. Outlier present?",
        "answer": "yes, 5",
        "choices": ["yes, 5", "no outlier", "yes, 53", "yes, 50"],
        "context": (
            "Outlier: a value far from the bulk of the data. Range = "
            "53 − 5 = 48. Most values cluster around 50; 5 is far "
            "below. Outliers pull the mean toward them but barely move "
            "the median."
        ),
    },
    {
        "tier": 4,
        "question": "Data: 8, 9, 10, 11, 12, 200. Mean vs median impact?",
        "answer": "mean affected more",
        "choices": [
            "mean affected more",
            "median affected more",
            "both affected equally",
            "neither affected",
        ],
        "context": (
            "Outliers like 200 pull the mean toward themselves but "
            "barely move the median (the middle position is robust). "
            "Median resists outliers; mean does not."
        ),
    },
    {
        "tier": 4,
        "question": "Outlier rule of thumb: more than 1.5 × ___ from Q1 or Q3?",
        "answer": "IQR",
        "choices": ["IQR", "median", "mean", "range"],
        "context": (
            "Outlier rule: a value beyond Q1 − 1.5(IQR) or Q3 + 1.5(IQR) "
            "is flagged. Example: IQR = 8 → fence at 1.5 × 8 = 12 from "
            "Q1 or Q3. IQR-based detection ignores extremes when "
            "defining 'far'."
        ),
    },
    {
        "tier": 4,
        "question": "Data: 20, 22, 21, 23, 22, 100. Outlier present?",
        "answer": "yes, 100",
        "choices": ["yes, 100", "no outlier", "yes, 20", "yes, 22"],
        "context": (
            "Outlier: a value far from the bulk of the data. Range = "
            "100 − 20 = 80. Most values cluster at 20-23; 100 is far "
            "above. Outliers distort the mean but barely affect the "
            "median."
        ),
    },
    # Additional T4 — 15 more questions across simple interest + scatter + mean/median
    {
        "tier": 4,
        "question": "$1000 at 4.5% simple interest for 2 years. Interest?",
        "answer": "$90",
        "choices": ["$90", "$45", "$180", "$135"],
        "context": (
            "Simple interest: I = Prt. P = 1000, r = 0.045, t = 2. "
            "I = 1000 × 0.045 × 2 = 90. Decimal percent: 4.5% = 0.045."
        ),
    },
    {
        "tier": 4,
        "question": "$1500 at 3% simple interest for 6 years. Interest?",
        "answer": "$270",
        "choices": ["$270", "$45", "$90", "$540"],
        "context": (
            "Simple interest: I = Prt. P = 1500, r = 0.03, t = 6. "
            "I = 1500 × 0.03 × 6 = 270. Common error: $45 (one year)."
        ),
    },
    {
        "tier": 4,
        "question": "$2400 at 5% simple interest for 4 years. Interest?",
        "answer": "$480",
        "choices": ["$480", "$120", "$240", "$960"],
        "context": (
            "Simple interest: I = Prt. P = 2400, r = 0.05, t = 4. "
            "I = 2400 × 0.05 × 4 = 480. Common error: $120 (one year)."
        ),
    },
    {
        "tier": 4,
        "question": "$3500 at 4% simple interest for 2 years. Interest?",
        "answer": "$280",
        "choices": ["$280", "$140", "$560", "$700"],
        "context": (
            "Simple interest: I = Prt. P = 3500, r = 0.04, t = 2. "
            "I = 3500 × 0.04 × 2 = 280. Common error: $140 (one year)."
        ),
    },
    {
        "tier": 4,
        "question": "$1000 at 5% simple interest for 4 years. Total amount?",
        "answer": "$1200",
        "choices": ["$1200", "$200", "$1050", "$1250"],
        "context": (
            "Simple interest total: A = P + I = P + Prt. I = 1000 × "
            "0.05 × 4 = 200. A = 1000 + 200 = 1200."
        ),
    },
    {
        "tier": 4,
        "question": "$5000 at 6% simple interest for 2 years. Total amount?",
        "answer": "$5600",
        "choices": ["$5600", "$600", "$5300", "$6200"],
        "context": (
            "Simple interest total: A = P + I. I = 5000 × 0.06 × 2 = "
            "600. A = 5000 + 600 = 5600. The $600 alone is only "
            "interest."
        ),
    },
    {
        "tier": 4,
        "question": "Mean of 14, 18, 22, 26, 30 = ?",
        "answer": "22",
        "choices": ["22", "20", "24", "110"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 14 + 18 + 22 + 26 + 30 = "
            "110. Count: 5. Mean = 110 ÷ 5 = 22. Evenly-spaced → mean = "
            "middle value."
        ),
    },
    {
        "tier": 4,
        "question": "Median of 14, 18, 22, 26, 30 = ?",
        "answer": "22",
        "choices": ["22", "18", "26", "110"],
        "context": (
            "Median: middle value when sorted. Already sorted: 5 "
            "values, middle is the 3rd: 22. Mean = median here for "
            "evenly-spaced data."
        ),
    },
    {
        "tier": 4,
        "question": "Mean of 6, 12, 18, 24, 30, 36 = ?",
        "answer": "21",
        "choices": ["21", "18", "24", "126"],
        "context": (
            "Mean (average): sum ÷ count. Sum: 6 + 12 + 18 + 24 + 30 + "
            "36 = 126. Count: 6. Mean = 126 ÷ 6 = 21. Mean of evenly-"
            "spaced data = average of first and last."
        ),
    },
    {
        "tier": 4,
        "question": "Scatterplot of age vs grip strength shows upward trend. Correlation?",
        "answer": "positive",
        "choices": ["positive", "negative", "no correlation", "perfect"],
        "context": (
            "Scatterplot correlation: upward trend → positive slope "
            "→ positive correlation. Real-world: grip strength does "
            "grow with age into adulthood. Correlation alone doesn't "
            "establish causation."
        ),
    },
    {
        "tier": 4,
        "question": "Line of best fit: y = 5x + 10. Predict y when x = 4.",
        "answer": "30",
        "choices": ["30", "20", "40", "14"],
        "context": (
            "Line of best fit uses slope-intercept form y = mx + b. "
            "Substitute x = 4: y = 5(4) + 10 = 20 + 10 = 30. Slope-"
            "intercept lets you predict y from any x."
        ),
    },
    {
        "tier": 4,
        "question": "Line of best fit: y = −2x + 20. Predict y when x = 7.",
        "answer": "6",
        "choices": ["6", "14", "27", "9"],
        "context": (
            "Line of best fit uses slope-intercept form y = mx + b. "
            "Substitute x = 7: y = −2(7) + 20 = −14 + 20 = 6. Negative "
            "slope means y drops as x grows."
        ),
    },
    {
        "tier": 4,
        "question": "Five-number summary 8, 16, 24, 32, 40. IQR?",
        "answer": "16",
        "choices": ["16", "32", "24", "8"],
        "context": (
            "Interquartile range (IQR) = Q3 − Q1 = 32 − 16 = 16. IQR "
            "is the spread of the middle 50% of data — robust to "
            "outliers."
        ),
    },
    {
        "tier": 4,
        "question": "Min 0, Q1 5, median 10, Q3 15, max 20. IQR?",
        "answer": "10",
        "choices": ["10", "20", "15", "5"],
        "context": (
            "Interquartile range (IQR) = Q3 − Q1 = 15 − 5 = 10. The "
            "middle 50% of data spans 10 units. Range = max − min = "
            "20 (wider, includes extremes)."
        ),
    },
    {
        "tier": 4,
        "question": "Five-number summary 5, 10, 20, 30, 60. Range?",
        "answer": "55",
        "choices": ["55", "20", "30", "25"],
        "context": (
            "Range = max − min = 60 − 5 = 55. Range captures the full "
            "spread including extremes; IQR (30 − 10 = 20) is the "
            "robust middle 50%."
        ),
    },
]


# ---------------------------------------------------------------------------
# T5 — 30 questions: compound interest, arithmetic+geometric sequences, growth
# ---------------------------------------------------------------------------
T5_QUESTIONS = [
    # Compound interest — 15 questions
    {
        "tier": 5,
        "question": "$1000 at 6% compounded yearly for 2 years. Amount?",
        "answer": "$1123.60",
        "choices": ["$1123.60", "$1120.00", "$1060.00", "$1180.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=1000, r=0.06, "
            "n=1, t=2. A = 1000(1.06)² = 1000 × 1.1236 = 1123.60. "
            "Simple interest would give 1120 — compound adds interest "
            "on interest."
        ),
    },
    {
        "tier": 5,
        "question": "$2000 at 5% compounded yearly for 3 years. Amount?",
        "answer": "$2315.25",
        "choices": ["$2315.25", "$2300.00", "$2100.00", "$2400.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=2000, r=0.05, "
            "n=1, t=3. A = 2000(1.05)³ = 2000 × 1.157625 = 2315.25. "
            "Simple interest would give 2300."
        ),
    },
    {
        "tier": 5,
        "question": "$500 at 4% compounded yearly for 2 years. Amount?",
        "answer": "$540.80",
        "choices": ["$540.80", "$540.00", "$520.00", "$560.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=500, r=0.04, "
            "n=1, t=2. A = 500(1.04)² = 500 × 1.0816 = 540.80. Simple "
            "gives 540 — compound is 0.80 higher."
        ),
    },
    {
        "tier": 5,
        "question": "$1000 at 8% compounded yearly for 1 year. Amount?",
        "answer": "$1080",
        "choices": ["$1080", "$1160", "$1040", "$1100"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). For one year "
            "compounded once, compound = simple = 1000 × 1.08 = 1080. "
            "Compounding only diverges from simple after multiple years."
        ),
    },
    {
        "tier": 5,
        "question": "$1000 at 10% compounded yearly for 2 years. Amount?",
        "answer": "$1210",
        "choices": ["$1210", "$1200", "$1100", "$1100.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=1000, r=0.10, "
            "n=1, t=2. A = 1000(1.10)² = 1000 × 1.21 = 1210. Simple "
            "interest would give 1200."
        ),
    },
    {
        "tier": 5,
        "question": "$1000 at 5% compounded yearly for 10 years. Amount?",
        "answer": "$1628.89",
        "choices": ["$1628.89", "$1500.00", "$1550.00", "$1700.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=1000, r=0.05, "
            "n=1, t=10. A = 1000(1.05)¹⁰ ≈ 1628.89. Simple interest "
            "gives 1500 — over 10 years compound is much higher."
        ),
    },
    {
        "tier": 5,
        "question": "$1500 at 4% compounded yearly for 2 years. Amount?",
        "answer": "$1622.40",
        "choices": ["$1622.40", "$1620.00", "$1560.00", "$1700.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=1500, r=0.04, "
            "n=1, t=2. A = 1500(1.04)² = 1500 × 1.0816 = 1622.40. "
            "Simple gives 1620 — compound adds 2.40."
        ),
    },
    {
        "tier": 5,
        "question": "$2500 at 6% compounded yearly for 2 years. Amount?",
        "answer": "$2809",
        "choices": ["$2809", "$2800", "$2650", "$3000"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=2500, r=0.06, "
            "n=1, t=2. A = 2500(1.06)² = 2500 × 1.1236 = 2809. Simple "
            "gives 2800 — compound adds 9 from interest-on-interest."
        ),
    },
    {
        "tier": 5,
        "question": "$3000 at 5% compounded yearly for 2 years. Amount?",
        "answer": "$3307.50",
        "choices": ["$3307.50", "$3300.00", "$3150.00", "$3400.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=3000, r=0.05, "
            "n=1, t=2. A = 3000(1.05)² = 3000 × 1.1025 = 3307.50. "
            "Simple gives 3300."
        ),
    },
    {
        "tier": 5,
        "question": "$1000 at 4% compounded yearly for 5 years. Amount?",
        "answer": "$1216.65",
        "choices": ["$1216.65", "$1200.00", "$1160.00", "$1300.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=1000, r=0.04, "
            "n=1, t=5. A = 1000(1.04)⁵ ≈ 1216.65. Simple gives 1200 — "
            "compound is higher because interest earns interest."
        ),
    },
    {
        "tier": 5,
        "question": "$800 at 10% compounded yearly for 3 years. Amount?",
        "answer": "$1064.80",
        "choices": ["$1064.80", "$1040.00", "$1100.00", "$1200.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=800, r=0.10, "
            "n=1, t=3. A = 800(1.10)³ = 800 × 1.331 = 1064.80. Simple "
            "gives 1040."
        ),
    },
    {
        "tier": 5,
        "question": "$5000 at 3% compounded yearly for 4 years. Amount?",
        "answer": "$5627.54",
        "choices": ["$5627.54", "$5600.00", "$5450.00", "$5700.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=5000, r=0.03, "
            "n=1, t=4. A = 5000(1.03)⁴ ≈ 5627.54. Simple interest "
            "would give 5600 — compound earns a bit more."
        ),
    },
    {
        "tier": 5,
        "question": "$1000 at 12% compounded yearly for 2 years. Amount?",
        "answer": "$1254.40",
        "choices": ["$1254.40", "$1240.00", "$1120.00", "$1300.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=1000, r=0.12, "
            "n=1, t=2. A = 1000(1.12)² = 1000 × 1.2544 = 1254.40. "
            "Simple gives 1240 — compound adds 14.40."
        ),
    },
    {
        "tier": 5,
        "question": "$2000 at 6% compounded yearly for 3 years. Amount?",
        "answer": "$2382.03",
        "choices": ["$2382.03", "$2360.00", "$2200.00", "$2500.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=2000, r=0.06, "
            "n=1, t=3. A = 2000(1.06)³ ≈ 2382.03. Simple interest "
            "would give 2360."
        ),
    },
    {
        "tier": 5,
        "question": "$1000 at 7% compounded yearly for 2 years. Amount?",
        "answer": "$1144.90",
        "choices": ["$1144.90", "$1140.00", "$1070.00", "$1200.00"],
        "context": (
            "Compound interest: A = P(1 + r/n)^(nt). P=1000, r=0.07, "
            "n=1, t=2. A = 1000(1.07)² = 1000 × 1.1449 = 1144.90. "
            "Simple interest gives 1140."
        ),
    },
    # Arithmetic sequence nth term — 8 questions
    {
        "tier": 5,
        "question": "Arithmetic sequence 5, 8, 11, 14, ... 10th term?",
        "answer": "32",
        "choices": ["32", "35", "29", "30"],
        "context": (
            "Arithmetic sequence: aₙ = a₁ + (n − 1)d. a₁ = 5, d = 3. "
            "a₁₀ = 5 + 9 × 3 = 5 + 27 = 32. Common error: forgetting "
            "the (n − 1) gives 35."
        ),
    },
    {
        "tier": 5,
        "question": "Arithmetic sequence 2, 7, 12, 17, ... 12th term?",
        "answer": "57",
        "choices": ["57", "60", "62", "52"],
        "context": (
            "Arithmetic sequence: aₙ = a₁ + (n − 1)d. a₁ = 2, d = 5. "
            "a₁₂ = 2 + 11 × 5 = 2 + 55 = 57. Common error: 60 (using n "
            "instead of n−1)."
        ),
    },
    {
        "tier": 5,
        "question": "Arithmetic sequence 10, 15, 20, 25, ... 8th term?",
        "answer": "45",
        "choices": ["45", "40", "50", "55"],
        "context": (
            "Arithmetic sequence: aₙ = a₁ + (n − 1)d. a₁ = 10, d = 5. "
            "a₈ = 10 + 7 × 5 = 10 + 35 = 45. Common error: 50 (using "
            "n instead of n−1)."
        ),
    },
    {
        "tier": 5,
        "question": "Arithmetic sequence 1, 4, 7, 10, ... 20th term?",
        "answer": "58",
        "choices": ["58", "60", "61", "55"],
        "context": (
            "Arithmetic sequence: aₙ = a₁ + (n − 1)d. a₁ = 1, d = 3. "
            "a₂₀ = 1 + 19 × 3 = 1 + 57 = 58. Common error: 61 (used "
            "20 instead of 19)."
        ),
    },
    {
        "tier": 5,
        "question": "Arithmetic sequence 20, 17, 14, 11, ... 10th term?",
        "answer": "−7",
        "choices": ["−7", "−10", "−4", "−13"],
        "context": (
            "Arithmetic sequence: aₙ = a₁ + (n − 1)d. a₁ = 20, d = −3 "
            "(decreasing). a₁₀ = 20 + 9 × (−3) = 20 − 27 = −7. Negative "
            "common difference shrinks the sequence."
        ),
    },
    {
        "tier": 5,
        "question": "Arithmetic sequence 6, 11, 16, 21, ... 15th term?",
        "answer": "76",
        "choices": ["76", "81", "75", "71"],
        "context": (
            "Arithmetic sequence: aₙ = a₁ + (n − 1)d. a₁ = 6, d = 5. "
            "a₁₅ = 6 + 14 × 5 = 6 + 70 = 76. Common error: 81 (off "
            "by one)."
        ),
    },
    {
        "tier": 5,
        "question": "Arithmetic sequence 0, 4, 8, 12, ... 25th term?",
        "answer": "96",
        "choices": ["96", "100", "92", "104"],
        "context": (
            "Arithmetic sequence: aₙ = a₁ + (n − 1)d. a₁ = 0, d = 4. "
            "a₂₅ = 0 + 24 × 4 = 96. Common error: 100 (used 25 instead "
            "of 24)."
        ),
    },
    {
        "tier": 5,
        "question": "Arithmetic sequence 3, 7, 11, 15, ... 50th term?",
        "answer": "199",
        "choices": ["199", "200", "203", "195"],
        "context": (
            "Arithmetic sequence: aₙ = a₁ + (n − 1)d. a₁ = 3, d = 4. "
            "a₅₀ = 3 + 49 × 4 = 3 + 196 = 199. Common error: 203 (used "
            "n instead of n − 1)."
        ),
    },
    # Geometric sequence nth term — 5 questions
    {
        "tier": 5,
        "question": "Geometric sequence 2, 6, 18, 54, ... 5th term?",
        "answer": "162",
        "choices": ["162", "108", "216", "486"],
        "context": (
            "Geometric sequence: aₙ = a₁ · r^(n−1). a₁ = 2, r = 3. "
            "a₅ = 2 · 3⁴ = 2 · 81 = 162. Common error: 486 (used n "
            "instead of n − 1)."
        ),
    },
    {
        "tier": 5,
        "question": "Geometric sequence 3, 6, 12, 24, ... 6th term?",
        "answer": "96",
        "choices": ["96", "48", "192", "144"],
        "context": (
            "Geometric sequence: aₙ = a₁ · r^(n−1). a₁ = 3, r = 2. "
            "a₆ = 3 · 2⁵ = 3 · 32 = 96. Common error: 192 (used n "
            "instead of n − 1)."
        ),
    },
    {
        "tier": 5,
        "question": "Geometric sequence 5, 10, 20, 40, ... 7th term?",
        "answer": "320",
        "choices": ["320", "160", "640", "280"],
        "context": (
            "Geometric sequence: aₙ = a₁ · r^(n−1). a₁ = 5, r = 2. "
            "a₇ = 5 · 2⁶ = 5 · 64 = 320. Common error: 640 (used n "
            "instead of n − 1)."
        ),
    },
    {
        "tier": 5,
        "question": "Geometric sequence 1, 4, 16, 64, ... 6th term?",
        "answer": "1024",
        "choices": ["1024", "256", "4096", "512"],
        "context": (
            "Geometric sequence: aₙ = a₁ · r^(n−1). a₁ = 1, r = 4. "
            "a₆ = 1 · 4⁵ = 1024. Common error: 4096 (used n instead "
            "of n − 1, would be 4⁶)."
        ),
    },
    {
        "tier": 5,
        "question": "Geometric sequence 100, 50, 25, ... 5th term?",
        "answer": "6.25",
        "choices": ["6.25", "12.5", "3.125", "5"],
        "context": (
            "Geometric sequence: aₙ = a₁ · r^(n−1). a₁ = 100, r = 1/2. "
            "a₅ = 100 · (1/2)⁴ = 100 · 1/16 = 6.25. Ratio < 1 means "
            "the sequence shrinks."
        ),
    },
    # Linear vs exponential growth recognition — 2 questions
    {
        "tier": 5,
        "question": "Sequence 5, 10, 20, 40, 80. Linear or geometric growth?",
        "answer": "geometric",
        "choices": ["geometric", "arithmetic", "neither", "both"],
        "context": (
            "Geometric sequence: each term × constant ratio (r = 2 "
            "here). Arithmetic sequences add a constant difference. "
            "Doubling repeatedly is exponential/geometric growth."
        ),
    },
    {
        "tier": 5,
        "question": "Sequence 7, 10, 13, 16, 19. Arithmetic or geometric?",
        "answer": "arithmetic",
        "choices": ["arithmetic", "geometric", "neither", "both"],
        "context": (
            "Arithmetic sequence: each term adds a constant (d = 3 "
            "here). Geometric would multiply by a constant. Adding the "
            "same number each step is linear/arithmetic growth."
        ),
    },
]


# ---------------------------------------------------------------------------
# Main: validate all, save incrementally
# ---------------------------------------------------------------------------
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bank = json.load(open(BANK_PATH, encoding="utf-8"))
    print(f"bank size: {len(bank)}")
    dup_idx, ans_idx = build_bank_indices(bank)
    print("indices built")

    all_qs = T1_QUESTIONS + T2_QUESTIONS + T3_QUESTIONS + T4_QUESTIONS + T5_QUESTIONS
    print(f"total drafted: {len(all_qs)}")
    print(f"  T1: {sum(1 for q in all_qs if q['tier'] == 1)}")
    print(f"  T2: {sum(1 for q in all_qs if q['tier'] == 2)}")
    print(f"  T3: {sum(1 for q in all_qs if q['tier'] == 3)}")
    print(f"  T4: {sum(1 for q in all_qs if q['tier'] == 4)}")
    print(f"  T5: {sum(1 for q in all_qs if q['tier'] == 5)}")
    print()

    passed = []
    failed = []
    soft_warned = []

    for i, q in enumerate(all_qs):
        result = validate_rewrite(
            "math", q,
            bank=bank,
            dup_index=dup_idx,
            answer_index=ans_idx,
            replace_idx=None,
        )
        verdict = result["verdict"]
        if verdict == "PASS":
            passed.append(q)
        elif verdict == "SOFT_WARN":
            soft_warned.append((q, result["soft_warns"]))
            passed.append(q)
        else:
            failed.append((i, q, result["hard_fails"]))

    print(f"PASS: {len(passed) - len(soft_warned)}")
    print(f"SOFT_WARN: {len(soft_warned)}")
    print(f"FAIL: {len(failed)}")
    print()

    if failed:
        print("FAILURES (first 20):")
        for idx, q, fails in failed[:20]:
            print(f"  #{idx} T{q['tier']}: {q['question'][:60]}")
            for gate, reason in fails:
                print(f"    - [{gate}] {reason[:200]}")
        print()

    if soft_warned:
        print(f"SOFT WARNS (first 10):")
        for q, warns in soft_warned[:10]:
            print(f"  T{q['tier']}: {q['question'][:60]}")
            for gate, reason in warns:
                print(f"    - [{gate}] {reason[:200]}")
        print()

    # Save passing questions
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    json.dump(passed, open(OUT_PATH, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"saved {len(passed)} → {OUT_PATH}")

    return passed, failed, soft_warned


if __name__ == "__main__":
    main()
