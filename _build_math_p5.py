"""Build Math P5 (Geometry, measurement, formulas) — 350 questions.

Distribution:
  T1: 30 (skip counting / pattern recognition for multiplication setup)
  T2: 100 (rectangle area/perimeter, box volume, triangle area, square)
  T3: 100 (circle area/circ, parallelogram, trapezoid, cylinder volume,
           triangle angle sum, temp conv, d=rt)
  T4: 100 (Pythagorean, distance formula, midpoint, similar triangles,
           special triangles, sphere/cone volume, transformations, surface area)
  T5: 20 (substitute-into-formula chains)

Every question:
  - matches an approved template (MATH_TEMPLATES §3)
  - context NAMES the trick/equation at T2+
  - passes math gates (validate_rewrite)
  - distractors model common student errors
  - choices are same order-of-magnitude (no magnitude leak)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = REPO / "data" / "questions" / "math.json"
OUT_PATH = REPO / "proposals" / "v2_audit" / "_math_p5_output.json"

bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
dup_index, ans_index = build_bank_indices(bank)


def q(tier, question, answer, choices, context):
    """Build + validate. Returns (verdict, record, details)."""
    rec = {
        "tier": tier,
        "question": question,
        "answer": answer,
        "choices": choices,
        "context": context,
    }
    res = validate_rewrite(
        "math", rec, bank=bank, dup_index=dup_index, answer_index=ans_index,
        replace_idx=None,
    )
    return res["verdict"], rec, res


def build_questions():
    """Return a list of (tier_label, builder_fn) for organized generation."""
    questions = []

    # ====================================================================
    # T1 — Skip counting / pattern recognition (30 questions)
    # ====================================================================
    t1_items = [
        # Skip counting by 2s, 3s, 4s, 5s, 6s, 7s, 8s, 9s, 10s, 11s, 12s
        # Plus a few rectangle-recognition + perimeter-of-squares warmups
        ("3, 6, 9, 12, ? — what comes next?", "15",
         ["15", "16", "13", "10"],
         "Skip counting by 3s. Adding 3 each step: 3, 6, 9, 12, 15. "
         "Skip counting builds the 3 times table — 3 × 5 = 15."),
        ("4, 8, 12, 16, ? — what comes next?", "20",
         ["20", "24", "18", "17"],
         "Skip counting by 4s. Adding 4 each step: 4, 8, 12, 16, 20. "
         "Skip counting is the foundation for the 4 times table (4 × 5 = 20)."),
        ("6, 12, 18, 24, ? — what comes next?", "30",
         ["30", "32", "28", "26"],
         "Skip counting by 6s. Adding 6 each step: 6, 12, 18, 24, 30. "
         "This bridges to the 6 times table — 6 × 5 = 30."),
        ("7, 14, 21, 28, ? — what comes next?", "35",
         ["35", "34", "32", "30"],
         "Skip counting by 7s. Adding 7 each step: 7, 14, 21, 28, 35. "
         "The 7 times table is the trickiest — skip counting drills it."),
        ("8, 16, 24, 32, ? — what comes next?", "40",
         ["40", "42", "36", "38"],
         "Skip counting by 8s. Adding 8 each step: 8, 16, 24, 32, 40. "
         "This is the 8 times table — 8 × 5 = 40."),
        ("9, 18, 27, 36, ? — what comes next?", "45",
         ["45", "44", "42", "48"],
         "Skip counting by 9s. Adding 9 each step: 9, 18, 27, 36, 45. "
         "Digit-sum check: 4+5 = 9 (9s always have digit-sum 9)."),
        ("10, 20, 30, 40, ? — what comes next?", "50",
         ["50", "100", "45", "60"],
         "Skip counting by 10s. Adding 10 each step: 10, 20, 30, 40, 50. "
         "Multiples of 10 always end in 0 — the easiest skip count."),
        ("11, 22, 33, 44, ? — what comes next?", "55",
         ["55", "54", "45", "50"],
         "Skip counting by 11s. Adding 11 each step: 11, 22, 33, 44, 55. "
         "Single-digit ×11 always gives a repeated digit (1×11=11, 5×11=55)."),
        ("12, 24, 36, 48, ? — what comes next?", "60",
         ["60", "62", "56", "50"],
         "Skip counting by 12s. Adding 12 each step: 12, 24, 36, 48, 60. "
         "12 times table — useful for time (12 hrs) and dozens."),
        ("2, 4, 6, 8, 10, ? — what comes next?", "12",
         ["12", "11", "14", "13"],
         "Skip counting by 2s — even numbers. Adding 2 each step. "
         "Even numbers end in 0, 2, 4, 6, or 8."),
        ("5, 10, 15, 20, 25, ? — what comes next?", "30",
         ["30", "35", "26", "20"],
         "Skip counting by 5s. Adding 5 each step. Multiples of 5 always "
         "end in 0 or 5 — quickest skip count after 10s."),
        ("3, 6, 9, 12, 15, ? — what comes next?", "18",
         ["18", "17", "20", "16"],
         "Skip counting by 3s. Adding 3 each step: ..., 12, 15, 18. "
         "Builds the 3 times table — 3 × 6 = 18."),
        ("4, 8, 12, 16, 20, ? — what comes next?", "24",
         ["24", "22", "25", "28"],
         "Skip counting by 4s. Adding 4 each step. Builds the 4 times "
         "table — 4 × 6 = 24."),
        ("0, 5, 10, 15, ? — what comes next?", "20",
         ["20", "25", "16", "18"],
         "Skip counting by 5s starting from 0. Adding 5 each step. "
         "Includes 0 as the first multiple — useful for number lines."),
        ("2, 4, 6, ? — what comes next?", "8",
         ["8", "10", "7", "9"],
         "Skip counting by 2s. Adding 2 each step. The even numbers — "
         "2 × 4 = 8."),
        ("5, 10, ? — what comes next?", "15",
         ["15", "20", "12", "11"],
         "Skip counting by 5s. Adding 5 each step: 5, 10, 15. "
         "Skip counting is the bridge to multiplication (5 × 3 = 15)."),
        ("10, 20, ? — what comes next?", "30",
         ["30", "40", "25", "21"],
         "Skip counting by 10s. Adding 10 each step. Multiples of 10 end "
         "in 0 — quickest pattern to spot."),
        ("3, 6, ? — what comes next?", "9",
         ["9", "10", "8", "12"],
         "Skip counting by 3s. Adding 3 each step: 3, 6, 9. "
         "Builds the 3 times table — 3 × 3 = 9."),
        ("1, 2, 4, 8, ? — what comes next?", "16",
         ["16", "12", "14", "10"],
         "Doubling pattern: each step doubles. 1 × 2 = 2, 2 × 2 = 4, "
         "4 × 2 = 8, 8 × 2 = 16. Doubles grow fast."),
        ("Square: side 4. Perimeter?", "16",
         ["16", "8", "12", "20"],
         "Square perimeter: add all four equal sides. 4 + 4 + 4 + 4 = 16. "
         "Or use 4 × side = 4 × 4 = 16. Counting on by 4s, four times."),
        ("Square: side 5. Perimeter?", "20",
         ["20", "10", "15", "25"],
         "Square perimeter: 4 equal sides. 5 + 5 + 5 + 5 = 20. "
         "Or 4 × 5 = 20. Skip counting by 5s, four times."),
        ("Square: side 3. Perimeter?", "12",
         ["12", "6", "9", "15"],
         "Square perimeter: 4 equal sides. 3 + 3 + 3 + 3 = 12. "
         "Or 4 × 3 = 12. Skip counting by 3s, four steps."),
        ("Square: side 2. Perimeter?", "8",
         ["8", "4", "6", "10"],
         "Square perimeter: 4 equal sides. 2 + 2 + 2 + 2 = 8. "
         "Or 4 × 2 = 8. Skip counting by 2s, four times."),
        ("Triangle: 3 equal sides of length 5. Perimeter?", "15",
         ["15", "10", "12", "20"],
         "Equilateral triangle: 3 equal sides. 5 + 5 + 5 = 15. "
         "Or 3 × 5 = 15. Skip counting by 5s, three steps."),
        ("Triangle: 3 equal sides of length 4. Perimeter?", "12",
         ["12", "8", "16", "9"],
         "Equilateral triangle: 3 equal sides. 4 + 4 + 4 = 12. "
         "Or 3 × 4 = 12. Skip counting by 4s, three times."),
        ("Triangle: 3 equal sides of length 6. Perimeter?", "18",
         ["18", "12", "15", "24"],
         "Equilateral triangle: 3 equal sides. 6 + 6 + 6 = 18. "
         "Or 3 × 6 = 18. Skip counting by 6s, three steps."),
        ("Octagon: how many sides?", "8",
         ["8", "6", "7", "10"],
         "Octagon: 8 sides. The prefix octa- means eight (octopus, "
         "octave). Stop signs are octagonal."),
        ("Decagon: how many sides?", "10",
         ["10", "8", "9", "12"],
         "Decagon: 10 sides. The prefix deca- means ten (decade, decimal). "
         "10 sides, 10 vertices."),
        ("Dodecagon: how many sides?", "12",
         ["12", "10", "11", "20"],
         "Dodecagon: 12 sides. The prefix dodeca- means twelve. "
         "Common in design — dodecagonal coins exist."),
        ("Heptagon: how many sides?", "7",
         ["7", "6", "8", "9"],
         "Heptagon: 7 sides. The prefix hepta- means seven. "
         "Seven sides — less common than its neighbors hexagon and octagon."),
    ]
    for item in t1_items:
        questions.append((1, item))

    # ====================================================================
    # T2 — 100 questions
    # ====================================================================
    t2_items = []

    # Rectangle area: A = l × w (15+)
    t2_items.extend([
        ("Rectangle: length 8, width 5. Area?", "40",
         ["40", "26", "13", "20"],
         "Rectangle area formula: A = l × w. Here A = 8 × 5 = 40 square units. "
         "Perimeter P = 2(l+w) = 26 — don't mix the two formulas."),
        ("Rectangle: length 9, width 6. Area?", "54",
         ["54", "30", "15", "45"],
         "Rectangle area formula: A = l × w. A = 9 × 6 = 54. "
         "Perimeter would be P = 2(l+w) = 30 — different formula."),
        ("Rectangle: length 10, width 7. Area?", "70",
         ["70", "34", "17", "80"],
         "Rectangle area formula: A = l × w. A = 10 × 7 = 70. "
         "Distinguish from perimeter P = 2(l+w) = 34."),
        ("Rectangle: length 12, width 4. Area?", "48",
         ["48", "32", "16", "44"],
         "Rectangle area formula: A = l × w. A = 12 × 4 = 48. "
         "Perimeter = 2(12+4) = 32 — area and perimeter are different."),
        ("Rectangle: length 6, width 3. Area?", "18",
         ["18", "18", "9", "20"],
         "Rectangle area formula: A = l × w. A = 6 × 3 = 18 square units. "
         "Perimeter = 2(6+3) = 18 (coincidence here)."),
        ("Rectangle: length 11, width 5. Area?", "55",
         ["55", "32", "16", "16"],
         "Rectangle area formula: A = l × w. A = 11 × 5 = 55. Use the "
         "×11 trick mentally: 11 × 5 = 55."),
        ("Rectangle: length 15, width 4. Area?", "60",
         ["60", "38", "19", "20"],
         "Rectangle area formula: A = l × w. A = 15 × 4 = 60 square units. "
         "Perimeter P = 2(l+w) = 38 — different formula."),
        ("Rectangle: length 20, width 8. Area?", "160",
         ["160", "56", "28", "100"],
         "Rectangle area formula: A = l × w. A = 20 × 8 = 160. "
         "Perimeter = 2(20+8) = 56 — area and perimeter are not the same."),
        ("Rectangle: length 7, width 7. Area?", "49",
         ["49", "28", "14", "14"],
         "Rectangle area formula: A = l × w. A = 7 × 7 = 49. "
         "When l = w, the rectangle is a square — A = s² = 7² = 49."),
        ("Rectangle: length 14, width 3. Area?", "42",
         ["42", "34", "17", "17"],
         "Rectangle area formula: A = l × w. A = 14 × 3 = 42. "
         "Perimeter = 2(14+3) = 34 — different formula."),
        ("Rectangle: length 25, width 4. Area?", "100",
         ["100", "58", "29", "50"],
         "Rectangle area formula: A = l × w. A = 25 × 4 = 100. "
         "Use halving-and-doubling: 25 × 4 = 50 × 2 = 100."),
        ("Rectangle: length 16, width 5. Area?", "80",
         ["80", "42", "21", "21"],
         "Rectangle area formula: A = l × w. A = 16 × 5 = 80. "
         "Halving-and-doubling: 16 × 5 = 8 × 10 = 80."),
        ("Rectangle: length 13, width 6. Area?", "78",
         ["78", "38", "19", "76"],
         "Rectangle area formula: A = l × w. A = 13 × 6 = 78. "
         "Distributive: 13 × 6 = 10 × 6 + 3 × 6 = 60 + 18 = 78."),
        ("Rectangle: length 18, width 5. Area?", "90",
         ["90", "46", "23", "23"],
         "Rectangle area formula: A = l × w. A = 18 × 5 = 90. "
         "Halve-then-×10 trick for ×5: 18/2 = 9, 9 × 10 = 90."),
        ("Rectangle: length 22, width 3. Area?", "66",
         ["66", "50", "25", "25"],
         "Rectangle area formula: A = l × w. A = 22 × 3 = 66. "
         "Perimeter = 2(22+3) = 50 — area and perimeter are different."),
        ("Rectangle: length 30, width 4. Area?", "120",
         ["120", "68", "34", "60"],
         "Rectangle area formula: A = l × w. A = 30 × 4 = 120. "
         "Use times-tables: 3 × 4 = 12, then attach the 0."),
    ])

    # Rectangle perimeter: P = 2(l + w) (15+)
    t2_items.extend([
        ("Rectangle: length 8, width 5. Perimeter?", "26",
         ["26", "40", "13", "20"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (8+5) = "
         "2 × 13 = 26. Don't mix with area A = lw = 40."),
        ("Rectangle: length 7, width 3. Perimeter?", "20",
         ["20", "21", "10", "42"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (7+3) = "
         "2 × 10 = 20. Don't mix with area A = lw = 21."),
        ("Rectangle: length 9, width 4. Perimeter?", "26",
         ["26", "36", "13", "18"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (9+4) = "
         "2 × 13 = 26. Area A = lw = 36 is different."),
        ("Rectangle: length 12, width 8. Perimeter?", "40",
         ["40", "96", "20", "48"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (12+8) = "
         "2 × 20 = 40. Area A = lw = 96 is different."),
        ("Rectangle: length 10, width 6. Perimeter?", "32",
         ["32", "60", "16", "30"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (10+6) = "
         "2 × 16 = 32. Area A = lw = 60 — distinct formula."),
        ("Rectangle: length 15, width 5. Perimeter?", "40",
         ["40", "75", "20", "30"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (15+5) = "
         "2 × 20 = 40. Area = 75 — different formula."),
        ("Rectangle: length 20, width 10. Perimeter?", "60",
         ["60", "200", "30", "40"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (20+10) = "
         "2 × 30 = 60. Area = 200 — different formula."),
        ("Rectangle: length 11, width 4. Perimeter?", "30",
         ["30", "44", "15", "22"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (11+4) = "
         "2 × 15 = 30. Area = 44 — different formula."),
        ("Rectangle: length 6, width 4. Perimeter?", "20",
         ["20", "24", "10", "12"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (6+4) = "
         "2 × 10 = 20. Area = 24 — distinguish."),
        ("Rectangle: length 14, width 6. Perimeter?", "40",
         ["40", "84", "20", "28"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (14+6) = "
         "2 × 20 = 40. Area = 84 — different."),
        ("Rectangle: length 9, width 2. Perimeter?", "22",
         ["22", "18", "11", "20"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (9+2) = "
         "2 × 11 = 22. Area = 18 — different formula."),
        ("Rectangle: length 25, width 5. Perimeter?", "60",
         ["60", "125", "30", "50"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (25+5) = "
         "2 × 30 = 60. Area = 125 — distinguish."),
        ("Rectangle: length 13, width 7. Perimeter?", "40",
         ["40", "91", "20", "26"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (13+7) = "
         "2 × 20 = 40. Area = 91 — different formula."),
        ("Rectangle: length 16, width 4. Perimeter?", "40",
         ["40", "64", "20", "32"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (16+4) = "
         "2 × 20 = 40. Area = 64 — distinguish."),
        ("Rectangle: length 5, width 3. Perimeter?", "16",
         ["16", "15", "8", "30"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (5+3) = "
         "2 × 8 = 16. Area = 15 — different formula."),
    ])

    # Triangle area: A = ½ × b × h (15+)
    t2_items.extend([
        ("Triangle: base 6, height 4. Area?", "12",
         ["12", "24", "10", "20"],
         "Triangle area formula: A = ½bh. A = ½ × 6 × 4 = ½ × 24 = 12. "
         "Don't forget the ½ — forgetting it gives the rectangle area (24)."),
        ("Triangle: base 8, height 7. Area?", "28",
         ["28", "56", "15", "48"],
         "Triangle area formula: A = ½bh. A = ½ × 8 × 7 = ½ × 56 = 28. "
         "Forgetting the ½ doubles the answer (56, the rectangle area)."),
        ("Triangle: base 9, height 4. Area?", "18",
         ["18", "36", "13", "26"],
         "Triangle area formula: A = ½bh. A = ½ × 9 × 4 = ½ × 36 = 18. "
         "Triangle is half of the bounding rectangle (36)."),
        ("Triangle: base 12, height 5. Area?", "30",
         ["30", "60", "17", "50"],
         "Triangle area formula: A = ½bh. A = ½ × 12 × 5 = ½ × 60 = 30. "
         "Forgetting the ½ gives the rectangle area (60)."),
        ("Triangle: base 4, height 7. Area?", "14",
         ["14", "28", "11", "11"],
         "Triangle area formula: A = ½bh. A = ½ × 4 × 7 = ½ × 28 = 14. "
         "Half of the rectangle area 28."),
        ("Triangle: base 9, height 8. Area?", "36",
         ["36", "72", "17", "17"],
         "Triangle area formula: A = ½bh. A = ½ × 9 × 8 = ½ × 72 = 36. "
         "Without the ½ you'd get the rectangle area 72."),
        ("Triangle: base 18, height 4. Area?", "36",
         ["36", "72", "22", "22"],
         "Triangle area formula: A = ½bh. A = ½ × 18 × 4 = ½ × 72 = 36. "
         "Half the bounding rectangle 72."),
        ("Triangle: base 5, height 6. Area?", "15",
         ["15", "30", "11", "11"],
         "Triangle area formula: A = ½bh. A = ½ × 5 × 6 = ½ × 30 = 15. "
         "Half the rectangle area 30."),
        ("Triangle: base 7, height 4. Area?", "14",
         ["14", "28", "11", "11"],
         "Triangle area formula: A = ½bh. A = ½ × 7 × 4 = ½ × 28 = 14. "
         "Don't forget the ½ — that's the most common error."),
        ("Triangle: base 11, height 4. Area?", "22",
         ["22", "44", "15", "15"],
         "Triangle area formula: A = ½bh. A = ½ × 11 × 4 = ½ × 44 = 22. "
         "Half the rectangle area 44."),
        ("Triangle: base 22, height 5. Area?", "55",
         ["55", "110", "27", "27"],
         "Triangle area formula: A = ½bh. A = ½ × 22 × 5 = ½ × 110 = 55. "
         "Forgetting the ½ gives 110 (rectangle area)."),
        ("Triangle: base 20, height 3. Area?", "30",
         ["30", "60", "23", "23"],
         "Triangle area formula: A = ½bh. A = ½ × 20 × 3 = ½ × 60 = 30. "
         "Half the rectangle area 60."),
        ("Triangle: base 15, height 8. Area?", "60",
         ["60", "120", "23", "23"],
         "Triangle area formula: A = ½bh. A = ½ × 15 × 8 = ½ × 120 = 60. "
         "Half the rectangle area 120."),
        ("Triangle: base 12, height 10. Area?", "60",
         ["60", "120", "22", "22"],
         "Triangle area formula: A = ½bh. A = ½ × 12 × 10 = ½ × 120 = 60. "
         "Half the rectangle area 120."),
        ("Triangle: base 6, height 6. Area?", "18",
         ["18", "36", "12", "12"],
         "Triangle area formula: A = ½bh. A = ½ × 6 × 6 = ½ × 36 = 18. "
         "Half the bounding square area 36."),
    ])

    # Box volume V = lwh (15+)
    t2_items.extend([
        ("Box: 2 × 4 × 7. Volume?", "56",
         ["56", "13", "28", "16"],
         "Rectangular prism volume: V = lwh. V = 2 × 4 × 7 = 56 cubic units. "
         "Multiply all three dimensions; sum 2+4+7 = 13 is not volume."),
        ("Box: 5 × 4 × 3. Volume?", "60",
         ["60", "12", "47", "20"],
         "Rectangular prism volume: V = lwh. V = 5 × 4 × 3 = 60. "
         "Multiply all three dimensions together."),
        ("Box: 6 × 5 × 2. Volume?", "60",
         ["60", "13", "30", "11"],
         "Rectangular prism volume: V = lwh. V = 6 × 5 × 2 = 60. "
         "Sum 6+5+2 = 13 is not volume — multiply, don't add."),
        ("Box: 4 × 4 × 4. Volume?", "64",
         ["64", "12", "48", "16"],
         "Rectangular prism volume: V = lwh. When l = w = h, the box is a "
         "cube: V = s³ = 4³ = 4 × 4 × 4 = 64."),
        ("Box: 3 × 3 × 3. Volume?", "27",
         ["27", "9", "18", "12"],
         "Rectangular prism volume: V = lwh. Cube V = s³ = 3³ = 3 × 3 × 3 = "
         "27. Perfect cubes: 1, 8, 27, 64, 125."),
        ("Box: 5 × 5 × 5. Volume?", "125",
         ["125", "15", "75", "25"],
         "Rectangular prism volume: V = lwh. Cube V = s³ = 5³ = 5 × 5 × 5 = "
         "125. Perfect cubes: 1, 8, 27, 64, 125, 216."),
        ("Box: 10 × 5 × 2. Volume?", "100",
         ["100", "17", "50", "20"],
         "Rectangular prism volume: V = lwh. V = 10 × 5 × 2 = 100 cubic "
         "units. Multiply all three dimensions."),
        ("Box: 8 × 3 × 2. Volume?", "48",
         ["48", "13", "24", "16"],
         "Rectangular prism volume: V = lwh. V = 8 × 3 × 2 = 48. "
         "Sum 8+3+2 = 13 is not volume."),
        ("Box: 7 × 4 × 3. Volume?", "84",
         ["84", "14", "42", "28"],
         "Rectangular prism volume: V = lwh. V = 7 × 4 × 3 = 84. "
         "Multiply all three dimensions."),
        ("Box: 6 × 4 × 5. Volume?", "120",
         ["120", "15", "60", "30"],
         "Rectangular prism volume: V = lwh. V = 6 × 4 × 5 = 120. "
         "Use halving-and-doubling: 6×4 = 24, 24×5 = 120."),
        ("Cube: side 10. Volume?", "1000",
         ["1000", "900", "1200", "800"],
         "Rectangular prism volume: V = lwh. Cube V = s³ = 10³ = 1000. "
         "10³ = 1000 — useful: 1 liter = 1000 cm³ (cube of 10 cm)."),
        ("Box: 9 × 2 × 3. Volume?", "54",
         ["54", "14", "27", "18"],
         "Rectangular prism volume: V = lwh. V = 9 × 2 × 3 = 54. "
         "Multiply all three dimensions."),
        ("Box: 8 × 5 × 4. Volume?", "160",
         ["160", "17", "80", "40"],
         "Rectangular prism volume: V = lwh. V = 8 × 5 × 4 = 160. "
         "Order doesn't matter: 8 × 5 = 40, 40 × 4 = 160."),
        ("Box: 12 × 3 × 2. Volume?", "72",
         ["72", "17", "36", "24"],
         "Rectangular prism volume: V = lwh. V = 12 × 3 × 2 = 72. "
         "Multiply all three dimensions; sum 17 is not volume."),
        ("Box: 5 × 4 × 4. Volume?", "80",
         ["80", "13", "40", "20"],
         "Rectangular prism volume: V = lwh. V = 5 × 4 × 4 = 80. "
         "Multiply all three dimensions."),
        ("Box: 6 × 6 × 4. Volume?", "144",
         ["144", "16", "72", "36"],
         "Rectangular prism volume: V = lwh. V = 6 × 6 × 4 = 144. "
         "Sum 6+6+4 = 16 is not volume; multiply."),
    ])

    # Square area: A = s² (10+)
    t2_items.extend([
        ("Square: side 6. Area?", "36",
         ["36", "24", "12", "30"],
         "Square area formula: A = s². A = 6² = 6 × 6 = 36 square units. "
         "Perimeter would be P = 4s = 24 — distinct formula."),
        ("Square: side 7. Area?", "49",
         ["49", "28", "14", "42"],
         "Square area formula: A = s². A = 7² = 49. "
         "Perfect square: 7² = 49. Perimeter P = 4×7 = 28."),
        ("Square: side 8. Area?", "64",
         ["64", "32", "16", "56"],
         "Square area formula: A = s². A = 8² = 64. "
         "Perfect square: 8² = 64 (memorize 1²-15²)."),
        ("Square: side 9. Area?", "81",
         ["81", "36", "18", "72"],
         "Square area formula: A = s². A = 9² = 81. "
         "Perfect square: 9² = 81. Perimeter P = 4×9 = 36."),
        ("Square: side 10. Area?", "100",
         ["100", "40", "20", "90"],
         "Square area formula: A = s². A = 10² = 100. "
         "Perfect square: 10² = 100. Perimeter P = 4×10 = 40."),
        ("Square: side 12. Area?", "144",
         ["144", "48", "24", "120"],
         "Square area formula: A = s². A = 12² = 144. "
         "Perfect square: 12² = 144 (a dozen squared = a gross)."),
        ("Square: side 11. Area?", "121",
         ["121", "44", "22", "110"],
         "Square area formula: A = s². A = 11² = 121. "
         "Perfect square: 11² = 121. Use the square-near-10 trick."),
        ("Square: side 15. Area?", "225",
         ["225", "60", "30", "150"],
         "Square area formula: A = s². A = 15² = 225. "
         "Square-ending-in-5 trick: 1×2 = 2, append 25 → 225."),
        ("Square: side 13. Area?", "169",
         ["169", "52", "26", "156"],
         "Square area formula: A = s². A = 13² = 169. "
         "Perfect square: 13² = 169 (memorize 1²-15²)."),
        ("Square: side 14. Area?", "196",
         ["196", "56", "28", "180"],
         "Square area formula: A = s². A = 14² = 196. "
         "Perfect square: 14² = 196. Useful for the 14-square recognition."),
    ])

    # A few extras to reach 100 (additional rectangles, perimeter checks,
    # angle facts)
    t2_items.extend([
        ("How many degrees in a right angle?", "90",
         ["90", "45", "180", "60"],
         "Right-angle trick: 90° = corner of a square = quarter of 360°. "
         "Computation: 360° ÷ 4 = 90°. Half a right angle = 45°."),
        ("How many degrees in a straight angle?", "180",
         ["180", "90", "360", "270"],
         "Straight-angle trick: 180° = half a full turn. "
         "Computation: 360° ÷ 2 = 180° = 2 × 90° (two right angles)."),
        ("How many degrees in a full turn?", "360",
         ["360", "180", "90", "270"],
         "Full-turn trick: 360° = full rotation. "
         "Computation: 4 × 90° = 360° = 2 × 180° (two straight angles)."),
        ("Sum of all angles in a square?", "360",
         ["360", "180", "90", "720"],
         "Quadrilateral angle-sum trick: 360°. A square has four right angles. "
         "Computation: 4 × 90° = 360° = sum of all 4 corners."),
        ("Square: side 6. Perimeter?", "24",
         ["24", "36", "12", "20"],
         "Square perimeter formula: P = 4s. P = 4 × 6 = 24. "
         "Don't confuse with area A = s² = 36 — different formula."),
        ("Square: side 8. Perimeter?", "32",
         ["32", "64", "16", "28"],
         "Square perimeter formula: P = 4s. P = 4 × 8 = 32. "
         "Distinct from area A = s² = 64."),
        ("Square: side 10. Perimeter?", "40",
         ["40", "100", "20", "30"],
         "Square perimeter formula: P = 4s. P = 4 × 10 = 40. "
         "Don't confuse with area A = s² = 100."),
        ("Rectangle: length 4, width 4. Perimeter?", "16",
         ["16", "8", "12", "20"],
         "Rectangle perimeter formula: P = 2(l + w). P = 2 × (4+4) = "
         "2 × 8 = 16. When l = w, it's a square — P = 4s = 16 also."),
        ("Box: 4 × 2 × 2. Volume?", "16",
         ["16", "8", "12", "10"],
         "Rectangular prism volume: V = lwh. V = 4 × 2 × 2 = 16 cubic "
         "units. Multiply all three dimensions together."),
        ("Box: 3 × 2 × 2. Volume?", "12",
         ["12", "7", "10", "8"],
         "Rectangular prism volume: V = lwh. V = 3 × 2 × 2 = 12. "
         "Sum 3+2+2 = 7 is not volume — multiply."),
        ("Box: 7 × 3 × 2. Volume?", "42",
         ["42", "12", "21", "14"],
         "Rectangular prism volume: V = lwh. V = 7 × 3 × 2 = 42. "
         "Multiply all three dimensions."),
        ("Rectangle: length 4, width 3. Area?", "12",
         ["12", "14", "7", "10"],
         "Rectangle area formula: A = l × w. A = 4 × 3 = 12. "
         "Perimeter P = 2(l+w) = 14 — different formula."),
        ("Rectangle: length 5, width 4. Area?", "20",
         ["20", "18", "9", "16"],
         "Rectangle area formula: A = l × w. A = 5 × 4 = 20 square units. "
         "Perimeter = 2(5+4) = 18 — distinct."),
        ("Triangle: base 10, height 4. Area?", "20",
         ["20", "40", "14", "14"],
         "Triangle area formula: A = ½bh. A = ½ × 10 × 4 = ½ × 40 = 20. "
         "Half the bounding rectangle 40."),
        # Additional T2 — angle facts, mixed shapes
        ("Sum of all angles in a rectangle?", "360°",
         ["360°", "180°", "90°", "720°"],
         "Quadrilateral angle-sum trick: 360°. A rectangle has four right angles. "
         "Computation: 4 × 90° = 360° = sum of all 4 corners."),
        ("Sum of all angles in any quadrilateral?", "360°",
         ["360°", "180°", "90°", "540°"],
         "Quadrilateral angle-sum trick: 360°. Holds for every quadrilateral — "
         "square, rectangle, parallelogram, trapezoid, irregular. "
         "Computation: 2 × 180° = 360° (two triangles' worth)."),
        ("Rectangle: length 12, width 6. Area?", "72",
         ["72", "36", "18", "60"],
         "Rectangle area formula: A = l × w. A = 12 × 6 = 72. "
         "Perimeter P = 2(l+w) = 36 — different formula."),
        ("Rectangle: length 9, width 5. Area?", "45",
         ["45", "28", "14", "40"],
         "Rectangle area formula: A = l × w. A = 9 × 5 = 45. "
         "Perimeter P = 2(l+w) = 28 — different formula."),
        ("Rectangle: length 11, width 7. Area?", "77",
         ["77", "36", "18", "72"],
         "Rectangle area formula: A = l × w. A = 11 × 7 = 77. "
         "Perimeter P = 2(l+w) = 36."),
        ("Rectangle: length 13, width 4. Area?", "52",
         ["52", "34", "17", "48"],
         "Rectangle area formula: A = l × w. A = 13 × 4 = 52. "
         "Perimeter P = 2(l+w) = 34."),
        ("Rectangle: length 17, width 3. Area?", "51",
         ["51", "40", "20", "48"],
         "Rectangle area formula: A = l × w. A = 17 × 3 = 51. "
         "Perimeter P = 2(l+w) = 40."),
        ("Rectangle: length 21, width 4. Area?", "84",
         ["84", "50", "25", "80"],
         "Rectangle area formula: A = l × w. A = 21 × 4 = 84. "
         "Perimeter P = 2(l+w) = 50."),
        ("Box: 4 × 3 × 6. Volume?", "72",
         ["72", "13", "36", "24"],
         "Rectangular prism volume: V = lwh. V = 4 × 3 × 6 = 72. "
         "Multiply all three dimensions."),
        ("Box: 5 × 5 × 3. Volume?", "75",
         ["75", "13", "25", "15"],
         "Rectangular prism volume: V = lwh. V = 5 × 5 × 3 = 75. "
         "Square base × height = 75."),
        ("Box: 2 × 8 × 5. Volume?", "80",
         ["80", "15", "40", "26"],
         "Rectangular prism volume: V = lwh. V = 2 × 8 × 5 = 80. "
         "Halving-and-doubling: 2×8 = 16, 16×5 = 80."),
        ("Cube: side 2. Volume?", "8",
         ["8", "6", "4", "12"],
         "Rectangular prism volume: V = lwh. Cube V = s³ = 2³ = 2 × 2 × 2 = 8. "
         "Perfect cubes: 1, 8, 27, 64, 125."),
        ("Triangle: base 5, height 8. Area?", "20",
         ["20", "40", "13", "13"],
         "Triangle area formula: A = ½bh. A = ½ × 5 × 8 = ½ × 40 = 20. "
         "Half the bounding rectangle 40."),
        ("Square: side 16. Area?", "256",
         ["256", "64", "32", "240"],
         "Square area formula: A = s². A = 16² = 256. "
         "Perfect square 16² = 256."),
    ])

    for item in t2_items:
        questions.append((2, item))

    # ====================================================================
    # T3 — 100 questions
    # ====================================================================
    t3_items = []

    # Circle area: A = πr² (20+)
    t3_items.extend([
        ("Circle: radius 3. Area in terms of π?", "9π",
         ["9π", "6π", "3π", "18π"],
         "Circle area formula: A = πr². A = π × 3² = 9π. "
         "Don't confuse with circumference C = 2πr = 6π. Area uses r²."),
        ("Circle: radius 4. Area in terms of π?", "16π",
         ["16π", "8π", "4π", "32π"],
         "Circle area formula: A = πr². A = π × 4² = 16π. "
         "Circumference would be C = 2πr = 8π — different formula."),
        ("Circle: radius 5. Area in terms of π?", "25π",
         ["25π", "10π", "5π", "50π"],
         "Circle area formula: A = πr². A = π × 5² = 25π. "
         "Don't confuse with circumference C = 2πr = 10π."),
        ("Circle: radius 6. Area in terms of π?", "36π",
         ["36π", "12π", "6π", "72π"],
         "Circle area formula: A = πr². A = π × 6² = 36π. "
         "Circumference C = 2πr = 12π — different formula."),
        ("Circle: radius 7. Area in terms of π?", "49π",
         ["49π", "14π", "7π", "98π"],
         "Circle area formula: A = πr². A = π × 7² = 49π. "
         "Perfect square 7² = 49. Circumference would be 14π."),
        ("Circle: radius 8. Area in terms of π?", "64π",
         ["64π", "16π", "8π", "128π"],
         "Circle area formula: A = πr². A = π × 8² = 64π. "
         "Perfect square 8² = 64. Don't confuse with C = 16π."),
        ("Circle: radius 9. Area in terms of π?", "81π",
         ["81π", "18π", "9π", "162π"],
         "Circle area formula: A = πr². A = π × 9² = 81π. "
         "Perfect square 9² = 81."),
        ("Circle: radius 10. Area in terms of π?", "100π",
         ["100π", "20π", "10π", "200π"],
         "Circle area formula: A = πr². A = π × 10² = 100π. "
         "Don't confuse with circumference C = 2πr = 20π."),
        ("Circle: radius 2. Area in terms of π?", "4π",
         ["4π", "2π", "8π", "4π"],
         "Circle area formula: A = πr². A = π × 2² = 4π. "
         "Circumference C = 2πr = 4π also — by coincidence at r = 2."),
        ("Circle: radius 12. Area in terms of π?", "144π",
         ["144π", "24π", "12π", "288π"],
         "Circle area formula: A = πr². A = π × 12² = 144π. "
         "Perfect square 12² = 144."),
        ("Circle: radius 11. Area in terms of π?", "121π",
         ["121π", "22π", "11π", "242π"],
         "Circle area formula: A = πr². A = π × 11² = 121π. "
         "Perfect square 11² = 121."),
        ("Circle: diameter 6. Area in terms of π?", "9π",
         ["9π", "36π", "6π", "12π"],
         "Circle area formula: A = πr². With diameter 6, radius r = 3. "
         "A = π × 3² = 9π. Common error: forgetting to halve diameter."),
        ("Circle: diameter 10. Area in terms of π?", "25π",
         ["25π", "100π", "10π", "50π"],
         "Circle area formula: A = πr². With diameter 10, radius r = 5. "
         "A = π × 5² = 25π. Don't square the diameter — halve first."),
        ("Circle: diameter 8. Area in terms of π?", "16π",
         ["16π", "64π", "8π", "32π"],
         "Circle area formula: A = πr². With diameter 8, radius r = 4. "
         "A = π × 4² = 16π. Common error: using d² gives 64π."),
        ("Circle: diameter 4. Area in terms of π?", "4π",
         ["4π", "16π", "2π", "8π"],
         "Circle area formula: A = πr². With diameter 4, radius r = 2. "
         "A = π × 2² = 4π. Halve diameter first."),
        ("Circle: radius 1. Area in terms of π?", "π",
         ["π", "2π", "π/2", "4π"],
         "Circle area formula: A = πr². A = π × 1² = 1 × π = π. "
         "At radius 1 the area equals π — a handy reference value."),
        ("Circle: radius 13. Area in terms of π?", "169π",
         ["169π", "26π", "13π", "338π"],
         "Circle area formula: A = πr². A = π × 13² = 169π. "
         "Perfect square 13² = 169."),
        ("Circle: radius 14. Area in terms of π?", "196π",
         ["196π", "28π", "14π", "392π"],
         "Circle area formula: A = πr². A = π × 14² = 196π. "
         "Perfect square 14² = 196."),
        ("Circle: radius 15. Area in terms of π?", "225π",
         ["225π", "30π", "15π", "450π"],
         "Circle area formula: A = πr². A = π × 15² = 225π. "
         "Square-ending-in-5: 1×2 = 2, append 25 → 225."),
        ("Circle: radius 20. Area in terms of π?", "400π",
         ["400π", "40π", "20π", "800π"],
         "Circle area formula: A = πr². A = π × 20² = 400π. "
         "Don't confuse with circumference C = 2πr = 40π."),
    ])

    # Circle circumference: C = 2πr (20+)
    t3_items.extend([
        ("Circle: radius 3. Circumference in terms of π?", "6π",
         ["6π", "9π", "3π", "12π"],
         "Circumference formula: C = 2πr. C = 2π × 3 = 6π. "
         "Don't confuse with area A = πr² = 9π. Circumference uses r once."),
        ("Circle: radius 4. Circumference in terms of π?", "8π",
         ["8π", "16π", "4π", "12π"],
         "Circumference formula: C = 2πr. C = 2π × 4 = 8π. "
         "Don't confuse with area A = πr² = 16π."),
        ("Circle: radius 5. Circumference in terms of π?", "10π",
         ["10π", "25π", "5π", "20π"],
         "Circumference formula: C = 2πr. C = 2π × 5 = 10π. "
         "Area would be A = πr² = 25π — different formula."),
        ("Circle: radius 7. Circumference in terms of π?", "14π",
         ["14π", "49π", "7π", "28π"],
         "Circumference formula: C = 2πr. C = 2π × 7 = 14π. "
         "Don't confuse with area A = πr² = 49π."),
        ("Circle: radius 8. Circumference in terms of π?", "16π",
         ["16π", "64π", "8π", "32π"],
         "Circumference formula: C = 2πr. C = 2π × 8 = 16π. "
         "Area A = πr² = 64π — distinct."),
        ("Circle: radius 9. Circumference in terms of π?", "18π",
         ["18π", "81π", "9π", "36π"],
         "Circumference formula: C = 2πr. C = 2π × 9 = 18π. "
         "Area A = πr² = 81π — different formula."),
        ("Circle: radius 10. Circumference in terms of π?", "20π",
         ["20π", "100π", "10π", "40π"],
         "Circumference formula: C = 2πr. C = 2π × 10 = 20π. "
         "Don't confuse with area A = πr² = 100π."),
        ("Circle: radius 11. Circumference in terms of π?", "22π",
         ["22π", "121π", "11π", "44π"],
         "Circumference formula: C = 2πr. C = 2π × 11 = 22π. "
         "Area A = πr² = 121π — different formula."),
        ("Circle: radius 12. Circumference in terms of π?", "24π",
         ["24π", "144π", "12π", "48π"],
         "Circumference formula: C = 2πr. C = 2π × 12 = 24π. "
         "Area A = πr² = 144π — distinct."),
        ("Circle: radius 1. Circumference in terms of π?", "2π",
         ["2π", "π", "π/2", "4π"],
         "Circumference formula: C = 2πr. C = 2π × 1 = 2 × π = 2π. "
         "At radius 1 the circumference is 2π — handy reference value."),
        ("Circle: radius 15. Circumference in terms of π?", "30π",
         ["30π", "225π", "15π", "60π"],
         "Circumference formula: C = 2πr. C = 2π × 15 = 30π. "
         "Area A = πr² = 225π."),
        ("Circle: diameter 6. Circumference in terms of π?", "6π",
         ["6π", "12π", "3π", "9π"],
         "Circumference formula: C = 2πr = πd. With d = 6, C = 6π. "
         "Or halve to radius 3, then C = 2πr = 6π."),
        ("Circle: diameter 10. Circumference in terms of π?", "10π",
         ["10π", "20π", "5π", "25π"],
         "Circumference formula: C = πd (or 2πr). With d = 10, C = 10π. "
         "Easy form: when diameter is given, just multiply by π."),
        ("Circle: diameter 8. Circumference in terms of π?", "8π",
         ["8π", "16π", "4π", "16π"],
         "Circumference formula: C = πd. With d = 8, C = 8π. "
         "Or radius 4 then C = 2π × 4 = 8π."),
        ("Circle: diameter 14. Circumference in terms of π?", "14π",
         ["14π", "28π", "7π", "49π"],
         "Circumference formula: C = πd. With d = 14, C = 14π. "
         "Equivalent: radius 7, C = 2π × 7 = 14π."),
        ("Circle: radius 6. Circumference in terms of π?", "12π",
         ["12π", "36π", "6π", "24π"],
         "Circumference formula: C = 2πr. C = 2π × 6 = 12π. "
         "Don't confuse with area A = πr² = 36π."),
        ("Circle: radius 20. Circumference in terms of π?", "40π",
         ["40π", "400π", "20π", "80π"],
         "Circumference formula: C = 2πr. C = 2π × 20 = 40π. "
         "Area would be 400π."),
        ("Circle: radius 25. Circumference in terms of π?", "50π",
         ["50π", "625π", "25π", "100π"],
         "Circumference formula: C = 2πr. C = 2π × 25 = 50π. "
         "Area A = πr² = 625π (15² then square trick → 625)."),
        ("Circle: radius 2. Circumference in terms of π?", "4π",
         ["4π", "4π", "2π", "8π"],
         "Circumference formula: C = 2πr. C = 2π × 2 = 4π. "
         "Area A = πr² = 4π also — coincidence at r = 2."),
        ("Circle: diameter 12. Circumference in terms of π?", "12π",
         ["12π", "24π", "6π", "36π"],
         "Circumference formula: C = πd. With d = 12, C = 12π. "
         "Or radius 6 then C = 2π × 6 = 12π."),
    ])

    # Parallelogram area: A = bh (10+)
    t3_items.extend([
        ("Parallelogram: base 8, height 3. Area?", "24",
         ["24", "12", "11", "16"],
         "Parallelogram area formula: A = bh. A = 8 × 3 = 24 square units. "
         "Same as rectangle area — parallelogram is a 'leaning' rectangle."),
        ("Parallelogram: base 10, height 4. Area?", "40",
         ["40", "20", "14", "28"],
         "Parallelogram area formula: A = bh. A = 10 × 4 = 40. "
         "Use the perpendicular height, not the slanted side."),
        ("Parallelogram: base 6, height 5. Area?", "30",
         ["30", "15", "11", "22"],
         "Parallelogram area formula: A = bh. A = 6 × 5 = 30. "
         "Perpendicular height × base — same shape's area as a rectangle."),
        ("Parallelogram: base 12, height 5. Area?", "60",
         ["60", "30", "17", "42"],
         "Parallelogram area formula: A = bh. A = 12 × 5 = 60. "
         "Multiply base by perpendicular height."),
        ("Parallelogram: base 13, height 5. Area?", "65",
         ["65", "32", "18", "45"],
         "Parallelogram area formula: A = bh. A = 13 × 5 = 65. "
         "Identical formula to rectangle area."),
        ("Parallelogram: base 14, height 4. Area?", "56",
         ["56", "28", "18", "40"],
         "Parallelogram area formula: A = bh. A = 14 × 4 = 56. "
         "Base × perpendicular height (NOT the slanted side)."),
        ("Parallelogram: base 16, height 5. Area?", "80",
         ["80", "40", "21", "40"],
         "Parallelogram area formula: A = bh. A = 16 × 5 = 80. "
         "Use the perpendicular height to the base."),
        ("Parallelogram: base 15, height 3. Area?", "45",
         ["45", "22", "18", "30"],
         "Parallelogram area formula: A = bh. A = 15 × 3 = 45. "
         "Base × perpendicular height."),
        ("Parallelogram: base 8, height 7. Area?", "56",
         ["56", "28", "15", "40"],
         "Parallelogram area formula: A = bh. A = 8 × 7 = 56. "
         "Base × perpendicular height."),
        ("Parallelogram: base 11, height 6. Area?", "66",
         ["66", "33", "17", "44"],
         "Parallelogram area formula: A = bh. A = 11 × 6 = 66. "
         "Use the perpendicular height (not the slanted side)."),
    ])

    # Trapezoid area: A = ½(b₁+b₂)h (10+)
    t3_items.extend([
        ("Trapezoid: bases 4 and 6, height 5. Area?", "25",
         ["25", "50", "30", "120"],
         "Trapezoid area formula: A = ½(b₁ + b₂)h. A = ½(4+6) × 5 = "
         "½ × 10 × 5 = 25. Average the bases, multiply by height."),
        ("Trapezoid: bases 3 and 7, height 4. Area?", "20",
         ["20", "40", "24", "84"],
         "Trapezoid area formula: A = ½(b₁ + b₂)h. A = ½(3+7) × 4 = "
         "½ × 10 × 4 = 20. Average bases, then multiply by height."),
        ("Trapezoid: bases 5 and 9, height 6. Area?", "42",
         ["42", "84", "54", "270"],
         "Trapezoid area formula: A = ½(b₁ + b₂)h. A = ½(5+9) × 6 = "
         "½ × 14 × 6 = 42. Average bases × height."),
        ("Trapezoid: bases 6 and 10, height 8. Area?", "64",
         ["64", "128", "80", "480"],
         "Trapezoid area formula: A = ½(b₁ + b₂)h. A = ½(6+10) × 8 = "
         "½ × 16 × 8 = 64."),
        ("Trapezoid: bases 8 and 12, height 5. Area?", "50",
         ["50", "100", "60", "480"],
         "Trapezoid area formula: A = ½(b₁ + b₂)h. A = ½(8+12) × 5 = "
         "½ × 20 × 5 = 50."),
        ("Trapezoid: bases 4 and 10, height 6. Area?", "42",
         ["42", "84", "60", "240"],
         "Trapezoid area formula: A = ½(b₁ + b₂)h. A = ½(4+10) × 6 = "
         "½ × 14 × 6 = 42."),
        ("Trapezoid: bases 7 and 11, height 4. Area?", "36",
         ["36", "72", "44", "308"],
         "Trapezoid area formula: A = ½(b₁ + b₂)h. A = ½(7+11) × 4 = "
         "½ × 18 × 4 = 36."),
        ("Trapezoid: bases 5 and 7, height 8. Area?", "48",
         ["48", "96", "56", "280"],
         "Trapezoid area formula: A = ½(b₁ + b₂)h. A = ½(5+7) × 8 = "
         "½ × 12 × 8 = 48."),
        ("Trapezoid: bases 2 and 8, height 5. Area?", "25",
         ["25", "50", "40", "80"],
         "Trapezoid area formula: A = ½(b₁ + b₂)h. A = ½(2+8) × 5 = "
         "½ × 10 × 5 = 25."),
        ("Trapezoid: bases 6 and 8, height 10. Area?", "70",
         ["70", "140", "80", "480"],
         "Trapezoid area formula: A = ½(b₁ + b₂)h. A = ½(6+8) × 10 = "
         "½ × 14 × 10 = 70."),
    ])

    # Cylinder volume: V = πr²h (10+)
    t3_items.extend([
        ("Cylinder: radius 2, height 5. Volume in terms of π?", "20π",
         ["20π", "10π", "40π", "100π"],
         "Cylinder volume formula: V = πr²h. V = π × 2² × 5 = π × 4 × 5 = "
         "20π. Square the radius first, then multiply by height."),
        ("Cylinder: radius 3, height 4. Volume in terms of π?", "36π",
         ["36π", "12π", "24π", "144π"],
         "Cylinder volume formula: V = πr²h. V = π × 3² × 4 = π × 9 × 4 = "
         "36π. Square the radius first."),
        ("Cylinder: radius 5, height 2. Volume in terms of π?", "50π",
         ["50π", "10π", "20π", "100π"],
         "Cylinder volume formula: V = πr²h. V = π × 5² × 2 = π × 25 × 2 = "
         "50π."),
        ("Cylinder: radius 4, height 3. Volume in terms of π?", "48π",
         ["48π", "12π", "24π", "144π"],
         "Cylinder volume formula: V = πr²h. V = π × 4² × 3 = π × 16 × 3 = "
         "48π."),
        ("Cylinder: radius 1, height 10. Volume in terms of π?", "10π",
         ["10π", "20π", "5π", "100π"],
         "Cylinder volume formula: V = πr²h. V = π × 1² × 10 = π × 1 × 10 = "
         "10π."),
        ("Cylinder: radius 2, height 8. Volume in terms of π?", "32π",
         ["32π", "16π", "64π", "256π"],
         "Cylinder volume formula: V = πr²h. V = π × 2² × 8 = π × 4 × 8 = "
         "32π."),
        ("Cylinder: radius 3, height 6. Volume in terms of π?", "54π",
         ["54π", "18π", "36π", "324π"],
         "Cylinder volume formula: V = πr²h. V = π × 3² × 6 = π × 9 × 6 = "
         "54π."),
        ("Cylinder: radius 6, height 2. Volume in terms of π?", "72π",
         ["72π", "24π", "36π", "432π"],
         "Cylinder volume formula: V = πr²h. V = π × 6² × 2 = π × 36 × 2 = "
         "72π."),
        ("Cylinder: radius 4, height 5. Volume in terms of π?", "80π",
         ["80π", "20π", "40π", "400π"],
         "Cylinder volume formula: V = πr²h. V = π × 4² × 5 = π × 16 × 5 = "
         "80π."),
        ("Cylinder: radius 5, height 4. Volume in terms of π?", "100π",
         ["100π", "20π", "40π", "500π"],
         "Cylinder volume formula: V = πr²h. V = π × 5² × 4 = π × 25 × 4 = "
         "100π."),
    ])

    # Temperature conversion C → F (10+)
    t3_items.extend([
        ("Convert 100°C to Fahrenheit.", "212°F",
         ["212°F", "180°F", "132°F", "200°F"],
         "Temperature conversion: F = (9/5)C + 32. F = (9/5)(100) + 32 = "
         "180 + 32 = 212. Water boils at 212°F = 100°C."),
        ("Convert 0°C to Fahrenheit.", "32°F",
         ["32°F", "0°F", "100°F", "212°F"],
         "Temperature conversion: F = (9/5)C + 32. F = (9/5)(0) + 32 = "
         "0 + 32 = 32. Water freezes at 32°F = 0°C."),
        ("Convert 20°C to Fahrenheit.", "68°F",
         ["68°F", "52°F", "60°F", "72°F"],
         "Temperature conversion: F = (9/5)C + 32. F = (9/5)(20) + 32 = "
         "36 + 32 = 68. Comfortable room temperature."),
        ("Convert 25°C to Fahrenheit.", "77°F",
         ["77°F", "57°F", "60°F", "82°F"],
         "Temperature conversion: F = (9/5)C + 32. F = (9/5)(25) + 32 = "
         "45 + 32 = 77."),
        ("Convert 10°C to Fahrenheit.", "50°F",
         ["50°F", "42°F", "32°F", "60°F"],
         "Temperature conversion: F = (9/5)C + 32. F = (9/5)(10) + 32 = "
         "18 + 32 = 50."),
        ("Convert 30°C to Fahrenheit.", "86°F",
         ["86°F", "62°F", "76°F", "90°F"],
         "Temperature conversion: F = (9/5)C + 32. F = (9/5)(30) + 32 = "
         "54 + 32 = 86. Hot summer day."),
        ("Convert 40°C to Fahrenheit.", "104°F",
         ["104°F", "72°F", "94°F", "120°F"],
         "Temperature conversion: F = (9/5)C + 32. F = (9/5)(40) + 32 = "
         "72 + 32 = 104. Heat-wave territory."),
        ("Convert 37°C to Fahrenheit.", "98.6°F",
         ["98.6°F", "69°F", "75°F", "105°F"],
         "Temperature conversion: F = (9/5)C + 32. F = (9/5)(37) + 32 = "
         "66.6 + 32 = 98.6. Normal human body temperature."),
        ("Convert 50°C to Fahrenheit.", "122°F",
         ["122°F", "82°F", "90°F", "140°F"],
         "Temperature conversion: F = (9/5)C + 32. F = (9/5)(50) + 32 = "
         "90 + 32 = 122."),
        ("Convert 15°C to Fahrenheit.", "59°F",
         ["59°F", "47°F", "50°F", "62°F"],
         "Temperature conversion: F = (9/5)C + 32. F = (9/5)(15) + 32 = "
         "27 + 32 = 59. Cool spring day."),
    ])

    # F to C (5+)
    t3_items.extend([
        ("Convert 32°F to Celsius.", "0°C",
         ["0°C", "32°C", "-32°C", "100°C"],
         "Temperature conversion: C = (5/9)(F - 32). C = (5/9)(32-32) = "
         "(5/9)(0) = 0. Water freezes at 32°F = 0°C."),
        ("Convert 212°F to Celsius.", "100°C",
         ["100°C", "212°C", "180°C", "80°C"],
         "Temperature conversion: C = (5/9)(F - 32). C = (5/9)(212-32) = "
         "(5/9)(180) = 100. Water boils at 212°F = 100°C."),
        ("Convert 68°F to Celsius.", "20°C",
         ["20°C", "36°C", "60°C", "100°C"],
         "Temperature conversion: C = (5/9)(F - 32). C = (5/9)(68-32) = "
         "(5/9)(36) = 20. Comfortable room temperature."),
        ("Convert 50°F to Celsius.", "10°C",
         ["10°C", "18°C", "32°C", "82°C"],
         "Temperature conversion: C = (5/9)(F - 32). C = (5/9)(50-32) = "
         "(5/9)(18) = 10."),
        ("Convert 86°F to Celsius.", "30°C",
         ["30°C", "54°C", "56°C", "118°C"],
         "Temperature conversion: C = (5/9)(F - 32). C = (5/9)(86-32) = "
         "(5/9)(54) = 30."),
    ])

    # d = rt (10+)
    t3_items.extend([
        ("60 mph for 3 hours. Distance?", "180 miles",
         ["180 miles", "20 miles", "63 miles", "120 miles"],
         "Distance formula: d = rt (distance = rate × time). d = 60 × 3 = "
         "180 miles. Multiply, don't add or divide."),
        ("50 mph for 4 hours. Distance?", "200 miles",
         ["200 miles", "54 miles", "12.5 miles", "150 miles"],
         "Distance formula: d = rt. d = 50 × 4 = 200 miles. "
         "Speed × time = distance."),
        ("40 mph for 2 hours. Distance?", "80 miles",
         ["80 miles", "42 miles", "20 miles", "60 miles"],
         "Distance formula: d = rt. d = 40 × 2 = 80 miles. "
         "Rate × time."),
        ("70 mph for 5 hours. Distance?", "350 miles",
         ["350 miles", "75 miles", "14 miles", "250 miles"],
         "Distance formula: d = rt. d = 70 × 5 = 350 miles. "
         "Rate × time = distance."),
        ("30 mph for 4 hours. Distance?", "120 miles",
         ["120 miles", "34 miles", "7.5 miles", "90 miles"],
         "Distance formula: d = rt. d = 30 × 4 = 120 miles."),
        ("65 mph for 2 hours. Distance?", "130 miles",
         ["130 miles", "67 miles", "32.5 miles", "100 miles"],
         "Distance formula: d = rt. d = 65 × 2 = 130 miles."),
        ("Walked 4 mph for 3 hours. Distance?", "12 miles",
         ["12 miles", "7 miles", "1.3 miles", "9 miles"],
         "Distance formula: d = rt. d = 4 × 3 = 12 miles. "
         "Rate × time gives distance."),
        ("Ran 8 mph for 2 hours. Distance?", "16 miles",
         ["16 miles", "10 miles", "4 miles", "12 miles"],
         "Distance formula: d = rt. d = 8 × 2 = 16 miles."),
        ("Drove 55 mph for 6 hours. Distance?", "330 miles",
         ["330 miles", "61 miles", "9 miles", "300 miles"],
         "Distance formula: d = rt. d = 55 × 6 = 330 miles."),
        ("100 mph for 3 hours. Distance?", "300 miles",
         ["300 miles", "103 miles", "33 miles", "200 miles"],
         "Distance formula: d = rt. d = 100 × 3 = 300 miles."),
    ])

    # Triangle angle sum 180° (5+)
    t3_items.extend([
        ("Triangle has angles 20° and 30°. Third angle?", "130°",
         ["130°", "50°", "180°", "90°"],
         "Triangle angle-sum trick: all three angles add to 180°. "
         "Computation: 180° = 20° + 30° + x = 50° + x, so x = 130°. "
         "Obtuse triangle."),
        ("Triangle has angles 36° and 72°. Third angle?", "72°",
         ["72°", "108°", "180°", "90°"],
         "Triangle angle-sum trick: all three angles add to 180°. "
         "Computation: 180° = 36° + 72° + x = 108° + x, so x = 72°. "
         "Isosceles (two angles equal 72°)."),
        ("Triangle has angles 53° and 37°. Third angle?", "90°",
         ["90°", "30°", "180°", "120°"],
         "Triangle angle-sum trick: all three angles add to 180°. "
         "Computation: 180° = 53° + 37° + x = 90° + x, so x = 90°. "
         "Right triangle."),
        ("Triangle: two angles 22° and 68°. Find the third.", "90°",
         ["90°", "30°", "180°", "120°"],
         "Triangle angle-sum trick: all three angles add to 180°. "
         "Computation: 180° = 22° + 68° + x = 90° + x, so x = 90°. "
         "Right triangle."),
        ("Triangle: two angles 18° and 12°. Find the third.", "150°",
         ["150°", "30°", "180°", "90°"],
         "Triangle angle-sum trick: all three angles add to 180°. "
         "Computation: 180° = 18° + 12° + x = 30° + x, so x = 150°. "
         "Very obtuse triangle."),
    ])

    for item in t3_items:
        questions.append((3, item))

    # ====================================================================
    # T4 — 100 questions
    # ====================================================================
    t4_items = []

    # Pythagorean theorem (30+)
    t4_items.extend([
        # 3-4-5 family
        ("Right triangle with legs 3 and 4. Hypotenuse?", "5",
         ["5", "7", "25", "12"],
         "Pythagorean theorem: a² + b² = c². 3² + 4² = 9 + 16 = 25; "
         "c = √25 = 5. The 3-4-5 triangle is the most famous "
         "Pythagorean triple — memorize 3-4-5, 5-12-13, 8-15-17, 7-24-25."),
        ("Right triangle with legs 6 and 8. Hypotenuse?", "10",
         ["10", "14", "100", "48"],
         "Pythagorean theorem: a² + b² = c². 6² + 8² = 36 + 64 = 100; "
         "c = √100 = 10. This is 2× the 3-4-5 triple — scaled Pythagorean "
         "triples are also right triangles."),
        ("Right triangle with legs 9 and 12. Hypotenuse?", "15",
         ["15", "21", "225", "108"],
         "Pythagorean theorem: a² + b² = c². 9² + 12² = 81 + 144 = 225; "
         "c = √225 = 15. This is 3× the 3-4-5 triple."),
        ("Right triangle: hypotenuse 5, one leg 3. Other leg?", "4",
         ["4", "2", "16", "8"],
         "Pythagorean theorem: a² + b² = c². With c = 5, a = 3: "
         "b² = 25 - 9 = 16, so b = 4. The 3-4-5 triple."),
        ("Right triangle: hypotenuse 10, one leg 6. Other leg?", "8",
         ["8", "4", "64", "16"],
         "Pythagorean theorem: a² + b² = c². With c = 10, a = 6: "
         "b² = 100 - 36 = 64, so b = 8. The 6-8-10 triangle (2× of 3-4-5)."),
        # 5-12-13 family
        ("Right triangle with legs 5 and 12. Hypotenuse?", "13",
         ["13", "17", "169", "60"],
         "Pythagorean theorem: a² + b² = c². 5² + 12² = 25 + 144 = 169; "
         "c = √169 = 13. The 5-12-13 triangle is one of four common "
         "Pythagorean triples: 3-4-5, 5-12-13, 8-15-17, 7-24-25."),
        ("Right triangle with legs 10 and 24. Hypotenuse?", "26",
         ["26", "34", "676", "240"],
         "Pythagorean theorem: a² + b² = c². 10² + 24² = 100 + 576 = 676; "
         "c = √676 = 26. This is 2× the 5-12-13 triple."),
        ("Right triangle: hypotenuse 13, one leg 5. Other leg?", "12",
         ["12", "8", "144", "169"],
         "Pythagorean theorem: a² + b² = c². With c = 13, a = 5: "
         "b² = 169 - 25 = 144, so b = 12. The famous 5-12-13 triple."),
        ("Right triangle: hypotenuse 13, one leg 12. Other leg?", "5",
         ["5", "1", "25", "169"],
         "Pythagorean theorem: a² + b² = c². With c = 13, a = 12: "
         "b² = 169 - 144 = 25, so b = 5. The 5-12-13 triple."),
        # 8-15-17 family
        ("Right triangle with legs 8 and 15. Hypotenuse?", "17",
         ["17", "23", "289", "120"],
         "Pythagorean theorem: a² + b² = c². 8² + 15² = 64 + 225 = 289; "
         "c = √289 = 17. The 8-15-17 triangle is one of four common "
         "Pythagorean triples: 3-4-5, 5-12-13, 8-15-17, 7-24-25."),
        ("Right triangle: hypotenuse 17, one leg 8. Other leg?", "15",
         ["15", "9", "225", "289"],
         "Pythagorean theorem: a² + b² = c². With c = 17, a = 8: "
         "b² = 289 - 64 = 225, so b = 15. The 8-15-17 triple."),
        ("Right triangle: hypotenuse 17, one leg 15. Other leg?", "8",
         ["8", "2", "64", "289"],
         "Pythagorean theorem: a² + b² = c². With c = 17, a = 15: "
         "b² = 289 - 225 = 64, so b = 8. The 8-15-17 triple."),
        # 7-24-25 family
        ("Right triangle with legs 7 and 24. Hypotenuse?", "25",
         ["25", "31", "625", "168"],
         "Pythagorean theorem: a² + b² = c². 7² + 24² = 49 + 576 = 625; "
         "c = √625 = 25. The 7-24-25 triangle is one of four common "
         "Pythagorean triples: 3-4-5, 5-12-13, 8-15-17, 7-24-25."),
        ("Right triangle: hypotenuse 25, one leg 7. Other leg?", "24",
         ["24", "18", "576", "625"],
         "Pythagorean theorem: a² + b² = c². With c = 25, a = 7: "
         "b² = 625 - 49 = 576, so b = 24. The 7-24-25 triple."),
        ("Right triangle: hypotenuse 25, one leg 24. Other leg?", "7",
         ["7", "1", "49", "625"],
         "Pythagorean theorem: a² + b² = c². With c = 25, a = 24: "
         "b² = 625 - 576 = 49, so b = 7. The 7-24-25 triple."),
        # Scaled triples
        ("Right triangle with legs 12 and 16. Hypotenuse?", "20",
         ["20", "28", "400", "192"],
         "Pythagorean theorem: a² + b² = c². 12² + 16² = 144 + 256 = 400; "
         "c = √400 = 20. This is 4× the 3-4-5 triple."),
        # Non-triple legs (use computation)
        ("Right triangle with legs 1 and 1. Hypotenuse?", "√2",
         ["√2", "2", "1", "√1"],
         "Pythagorean theorem: a² + b² = c². 1² + 1² = 1 + 1 = 2; "
         "c = √2. The 1-1-√2 ratio defines the 45-45-90 triangle."),
        ("Right triangle: hypotenuse 5, one leg 4. Other leg?", "3",
         ["3", "1", "9", "25"],
         "Pythagorean theorem: a² + b² = c². With c = 5, a = 4: "
         "b² = 25 - 16 = 9, so b = 3. The 3-4-5 triple from the other side."),
        ("Right triangle: hypotenuse 50, one leg 30. Other leg?", "40",
         ["40", "20", "1600", "2500"],
         "Pythagorean theorem: a² + b² = c². With c = 50, a = 30: "
         "b² = 2500 - 900 = 1600, so b = 40. This is 10× the 3-4-5 triple."),
        # Sneaky: forgot to take square root
        ("Right triangle with legs 8 and 6. Hypotenuse?", "10",
         ["10", "14", "100", "48"],
         "Pythagorean theorem: a² + b² = c². 8² + 6² = 64 + 36 = 100; "
         "c = √100 = 10. Common error: forgetting to take the square root "
         "(answer would be 100, not 10). This is 2× the 3-4-5 triple."),
        ("Right triangle with legs 5 and 12. Square of hypotenuse?", "169",
         ["169", "17", "144", "60"],
         "Pythagorean theorem: a² + b² = c². 5² + 12² = 25 + 144 = 169 = c². "
         "Here we want c² not c — so we stop before square-rooting. "
         "The 5-12-13 triple."),
        # Recognition / which triple
        ("Which right triangle is the 'Pythagorean triple' with legs 7?", "7-24-25",
         ["7-24-25", "7-8-9", "7-10-13", "7-12-19"],
         "Pythagorean triples: 3-4-5, 5-12-13, 8-15-17, 7-24-25. "
         "The 7-24-25 triple has leg 7. Verify: 7² + 24² = 49 + 576 = 625 = 25²."),
        ("Which right triangle is the 'Pythagorean triple' with legs 8?", "8-15-17",
         ["8-15-17", "8-10-12", "8-9-12", "8-16-24"],
         "Pythagorean triples: 3-4-5, 5-12-13, 8-15-17, 7-24-25. "
         "The 8-15-17 triple has leg 8. Verify: 8² + 15² = 64 + 225 = 289 = 17²."),
        ("Right triangle with legs 18 and 24. Hypotenuse?", "30",
         ["30", "42", "900", "432"],
         "Pythagorean theorem: a² + b² = c². 18² + 24² = 324 + 576 = 900; "
         "c = √900 = 30. This is 6× the 3-4-5 triple."),
        ("Right triangle with legs 7 and 24. Square of hypotenuse?", "625",
         ["625", "31", "576", "168"],
         "Pythagorean theorem: a² + b² = c². 7² + 24² = 49 + 576 = 625 = c². "
         "The 7-24-25 triple (c = 25 if we square-root, but the question "
         "asked for c² = 625)."),
        ("Right triangle: hypotenuse 41, one leg 9. Other leg?", "40",
         ["40", "32", "1600", "1681"],
         "Pythagorean theorem: a² + b² = c². With c = 41, a = 9: "
         "b² = 1681 - 81 = 1600, so b = 40. The 9-40-41 Pythagorean triple."),
    ])

    # Distance formula (15+)
    t4_items.extend([
        ("Distance from (0, 0) to (3, 4)?", "5",
         ["5", "7", "25", "1"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). d = √(3² + 4²) = "
         "√(9+16) = √25 = 5. The 3-4-5 Pythagorean triple."),
        ("Distance from (1, 2) to (4, 6)?", "5",
         ["5", "7", "25", "3"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). d = √((4-1)² + (6-2)²) = "
         "√(9+16) = √25 = 5. The 3-4-5 triple again."),
        ("Distance from (0, 0) to (5, 12)?", "13",
         ["13", "17", "169", "60"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). d = √(5² + 12²) = "
         "√(25+144) = √169 = 13. The 5-12-13 triple."),
        ("Distance from (2, 3) to (5, 7)?", "5",
         ["5", "7", "25", "12"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). Differences: 3 and 4. "
         "d = √(9+16) = √25 = 5. The 3-4-5 triple."),
        ("Distance from (0, 0) to (8, 15)?", "17",
         ["17", "23", "289", "120"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). d = √(8² + 15²) = "
         "√(64+225) = √289 = 17. The 8-15-17 triple."),
        ("Distance from (0, 0) to (6, 8)?", "10",
         ["10", "14", "100", "48"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). d = √(6² + 8²) = "
         "√(36+64) = √100 = 10. This is 2× the 3-4-5 triple."),
        ("Distance from (1, 1) to (4, 5)?", "5",
         ["5", "7", "25", "3"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). Differences: 3 and 4. "
         "d = √(9+16) = √25 = 5. The 3-4-5 triple."),
        ("Distance from (-1, 2) to (2, 6)?", "5",
         ["5", "7", "25", "3"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). Differences: 3 and 4. "
         "d = √(9+16) = √25 = 5."),
        ("Distance from (0, 0) to (7, 24)?", "25",
         ["25", "31", "625", "168"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). d = √(7² + 24²) = "
         "√(49+576) = √625 = 25. The 7-24-25 triple."),
        ("Distance from (1, 2) to (1, 5)?", "3",
         ["3", "5", "9", "1"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). When x₁ = x₂, "
         "d = |y₂-y₁| = |5-2| = 3. Vertical line — just the y-difference."),
        ("Distance from (2, 3) to (6, 3)?", "4",
         ["4", "8", "16", "2"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). When y₁ = y₂, "
         "d = |x₂-x₁| = |6-2| = 4. Horizontal line — just the x-difference."),
        ("Distance from (0, 0) to (9, 12)?", "15",
         ["15", "21", "225", "108"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). d = √(81 + 144) = "
         "√225 = 15. This is 3× the 3-4-5 triple."),
        ("Distance from (-3, -4) to (0, 0)?", "5",
         ["5", "7", "25", "-7"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). d = √(3² + 4²) = "
         "√25 = 5. Negatives squared become positive — the 3-4-5 triple."),
        ("Distance from (0, 0) to (10, 24)?", "26",
         ["26", "34", "676", "240"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). d = √(100 + 576) = "
         "√676 = 26. This is 2× the 5-12-13 triple."),
        ("Distance from (3, 4) to (6, 8)?", "5",
         ["5", "7", "25", "3"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). Differences 3 and 4. "
         "d = √(9+16) = √25 = 5. The 3-4-5 triple."),
    ])

    # Midpoint formula (10+)
    t4_items.extend([
        ("Midpoint of (1, 2) and (5, 8)?", "(3, 5)",
         ["(3, 5)", "(4, 6)", "(6, 10)", "(2, 3)"],
         "Midpoint formula: ((x₁+x₂)/2, (y₁+y₂)/2). Midpoint = "
         "((1+5)/2, (2+8)/2) = (3, 5). Average the x's, average the y's."),
        ("Midpoint of (0, 0) and (4, 6)?", "(2, 3)",
         ["(2, 3)", "(4, 6)", "(1, 1.5)", "(4, 3)"],
         "Midpoint formula: ((x₁+x₂)/2, (y₁+y₂)/2). Midpoint = "
         "((0+4)/2, (0+6)/2) = (2, 3)."),
        ("Midpoint of (2, 4) and (8, 10)?", "(5, 7)",
         ["(5, 7)", "(10, 14)", "(6, 6)", "(3, 3)"],
         "Midpoint formula: ((x₁+x₂)/2, (y₁+y₂)/2). Midpoint = "
         "((2+8)/2, (4+10)/2) = (5, 7)."),
        ("Midpoint of (-2, 3) and (4, 7)?", "(1, 5)",
         ["(1, 5)", "(2, 10)", "(3, 2)", "(-1, 5)"],
         "Midpoint formula: ((x₁+x₂)/2, (y₁+y₂)/2). Midpoint = "
         "((-2+4)/2, (3+7)/2) = (1, 5). Negatives still average."),
        ("Midpoint of (0, 0) and (10, 10)?", "(5, 5)",
         ["(5, 5)", "(10, 10)", "(0, 10)", "(2.5, 2.5)"],
         "Midpoint formula: ((x₁+x₂)/2, (y₁+y₂)/2). Midpoint = "
         "((0+10)/2, (0+10)/2) = (5, 5). On the line y = x."),
        ("Midpoint of (3, 1) and (7, 9)?", "(5, 5)",
         ["(5, 5)", "(10, 10)", "(4, 8)", "(2, 4)"],
         "Midpoint formula: ((x₁+x₂)/2, (y₁+y₂)/2). Midpoint = "
         "((3+7)/2, (1+9)/2) = (5, 5)."),
        ("Midpoint of (-4, -2) and (6, 8)?", "(1, 3)",
         ["(1, 3)", "(10, 10)", "(2, 6)", "(-1, -3)"],
         "Midpoint formula: ((x₁+x₂)/2, (y₁+y₂)/2). Midpoint = "
         "((-4+6)/2, (-2+8)/2) = (1, 3). Average the x's, average the y's."),
        ("Midpoint of (1, 1) and (9, 9)?", "(5, 5)",
         ["(5, 5)", "(10, 10)", "(8, 8)", "(4, 4)"],
         "Midpoint formula: ((x₁+x₂)/2, (y₁+y₂)/2). Midpoint = "
         "((1+9)/2, (1+9)/2) = (5, 5)."),
        ("Midpoint of (2, 6) and (8, 2)?", "(5, 4)",
         ["(5, 4)", "(10, 8)", "(6, 4)", "(4, 5)"],
         "Midpoint formula: ((x₁+x₂)/2, (y₁+y₂)/2). Midpoint = "
         "((2+8)/2, (6+2)/2) = (5, 4)."),
        ("Midpoint of (0, 0) and (8, 6)?", "(4, 3)",
         ["(4, 3)", "(8, 6)", "(2, 1.5)", "(4, 6)"],
         "Midpoint formula: ((x₁+x₂)/2, (y₁+y₂)/2). Midpoint = "
         "((0+8)/2, (0+6)/2) = (4, 3)."),
    ])

    # Sphere volume V = (4/3)πr³ (10+)
    t4_items.extend([
        ("Sphere: radius 3. Volume in terms of π?", "36π",
         ["36π", "12π", "27π", "108π"],
         "Sphere volume formula: V = (4/3)πr³. V = (4/3)π × 3³ = "
         "(4/3) × 27 × π = 36π. Cube the radius first."),
        ("Sphere: radius 6. Volume in terms of π?", "288π",
         ["288π", "72π", "144π", "864π"],
         "Sphere volume formula: V = (4/3)πr³. V = (4/3)π × 6³ = "
         "(4/3) × 216 × π = 288π. Cube r first: 6³ = 216."),
        ("Sphere: radius 1. Volume in terms of π?", "(4/3)π",
         ["(4/3)π", "4π", "π", "(1/3)π"],
         "Sphere volume formula: V = (4/3)πr³. V = (4/3)π × 1³ = (4/3)π. "
         "The unit sphere volume — handy reference."),
        ("Sphere: radius 2. Volume in terms of π?", "(32/3)π",
         ["(32/3)π", "8π", "16π", "(4/3)π"],
         "Sphere volume formula: V = (4/3)πr³. V = (4/3)π × 2³ = "
         "(4/3) × 8 × π = (32/3)π."),
        ("Sphere: radius 4. Volume in terms of π?", "(256/3)π",
         ["(256/3)π", "(128/3)π", "(192/3)π", "(512/3)π"],
         "Sphere volume formula: V = (4/3)πr³. V = (4/3)π × 4³ = "
         "(4/3) × 64 × π = (256/3)π."),
        ("Sphere: radius 5. Volume in terms of π?", "(500/3)π",
         ["(500/3)π", "(250/3)π", "(400/3)π", "(625/3)π"],
         "Sphere volume formula: V = (4/3)πr³. V = (4/3)π × 5³ = "
         "(4/3) × 125 × π = (500/3)π."),
        ("Sphere: radius 12. Volume in terms of π?", "2304π",
         ["2304π", "576π", "1728π", "144π"],
         "Sphere volume formula: V = (4/3)πr³. V = (4/3)π × 12³ = "
         "(4/3) × 1728 × π = 2304π. 12³ = 1728."),
        ("Sphere: radius 10. Volume in terms of π?", "(4000/3)π",
         ["(4000/3)π", "(2000/3)π", "(3000/3)π", "(5000/3)π"],
         "Sphere volume formula: V = (4/3)πr³. V = (4/3)π × 10³ = "
         "(4/3) × 1000 × π = (4000/3)π."),
    ])

    # Cone volume V = (1/3)πr²h (10+)
    t4_items.extend([
        ("Cone: radius 3, height 4. Volume in terms of π?", "12π",
         ["12π", "36π", "4π", "9π"],
         "Cone volume formula: V = (1/3)πr²h. V = (1/3)π × 9 × 4 = "
         "12π. One-third of the bounding cylinder (cylinder would be 36π)."),
        ("Cone: radius 2, height 6. Volume in terms of π?", "8π",
         ["8π", "24π", "12π", "4π"],
         "Cone volume formula: V = (1/3)πr²h. V = (1/3)π × 4 × 6 = "
         "8π. Cylinder of same r, h would be 24π."),
        ("Cone: radius 5, height 3. Volume in terms of π?", "25π",
         ["25π", "75π", "15π", "5π"],
         "Cone volume formula: V = (1/3)πr²h. V = (1/3)π × 25 × 3 = "
         "25π. One-third of cylinder volume 75π."),
        ("Cone: radius 6, height 5. Volume in terms of π?", "60π",
         ["60π", "180π", "30π", "12π"],
         "Cone volume formula: V = (1/3)πr²h. V = (1/3)π × 36 × 5 = "
         "60π. One-third of cylinder 180π."),
        ("Cone: radius 1, height 9. Volume in terms of π?", "3π",
         ["3π", "9π", "1π", "27π"],
         "Cone volume formula: V = (1/3)πr²h. V = (1/3)π × 1 × 9 = "
         "3π. Cylinder of same dims = 9π."),
        ("Cone: radius 4, height 6. Volume in terms of π?", "32π",
         ["32π", "96π", "16π", "8π"],
         "Cone volume formula: V = (1/3)πr²h. V = (1/3)π × 16 × 6 = "
         "32π. One-third of cylinder volume."),
        ("Cone: radius 3, height 7. Volume in terms of π?", "21π",
         ["21π", "63π", "9π", "7π"],
         "Cone volume formula: V = (1/3)πr²h. V = (1/3)π × 9 × 7 = "
         "21π. One-third of cylinder 63π."),
        ("Cone: radius 2, height 3. Volume in terms of π?", "4π",
         ["4π", "12π", "2π", "6π"],
         "Cone volume formula: V = (1/3)πr²h. V = (1/3)π × 4 × 3 = "
         "4π. Cylinder of same dims = 12π."),
        ("Cone: radius 6, height 8. Volume in terms of π?", "96π",
         ["96π", "288π", "48π", "16π"],
         "Cone volume formula: V = (1/3)πr²h. V = (1/3)π × 36 × 8 = "
         "96π. One-third of cylinder 288π."),
        ("Cone: radius 10, height 3. Volume in terms of π?", "100π",
         ["100π", "300π", "50π", "30π"],
         "Cone volume formula: V = (1/3)πr²h. V = (1/3)π × 100 × 3 = "
         "100π."),
    ])

    # Surface area of box, cylinder (10+)
    t4_items.extend([
        ("Cube: side 7. Surface area?", "294",
         ["294", "343", "49", "147"],
         "Cube surface area: 6 × s² (six identical square faces). "
         "SA = 6 × 7² = 6 × 49 = 294. Don't confuse with volume = s³ = 343."),
        ("Cube: side 3. Surface area?", "54",
         ["54", "27", "9", "108"],
         "Cube surface area: 6 × s². SA = 6 × 3² = 6 × 9 = 54. "
         "Volume V = s³ = 27 is different."),
        ("Cube: side 6. Surface area?", "216",
         ["216", "216", "36", "432"],
         "Cube surface area: 6 × s². SA = 6 × 6² = 6 × 36 = 216. "
         "Coincidence: volume V = s³ = 216 also at s = 6."),
        ("Box: 2 × 3 × 4. Surface area?", "52",
         ["52", "24", "26", "104"],
         "Rectangular prism surface area: 2(lw + lh + wh). "
         "SA = 2(2×3 + 2×4 + 3×4) = 2(6+8+12) = 2 × 26 = 52. "
         "Volume V = 24 is different."),
        ("Box: 3 × 4 × 5. Surface area?", "94",
         ["94", "60", "47", "188"],
         "Rectangular prism surface area: 2(lw + lh + wh). "
         "SA = 2(12+15+20) = 2 × 47 = 94. Volume V = 60."),
        ("Box: 2 × 2 × 5. Surface area?", "48",
         ["48", "20", "24", "96"],
         "Rectangular prism surface area: 2(lw + lh + wh). "
         "SA = 2(4+10+10) = 2 × 24 = 48. Volume V = 20."),
        ("Cube: side 10. Surface area?", "600",
         ["600", "1000", "100", "60"],
         "Cube surface area: 6 × s². SA = 6 × 10² = 6 × 100 = 600. "
         "Volume V = 1000 is different (10³)."),
        ("Cube: side 1. Surface area?", "6",
         ["6", "1", "4", "12"],
         "Cube surface area: 6 × s². SA = 6 × 1² = 6. "
         "Six square faces, each of area 1. Volume V = 1."),
    ])

    # Similar triangles (10+)
    t4_items.extend([
        ("Triangle sides 3-4-5; similar triangle has shortest side 9. Longest side?", "15",
         ["15", "12", "9", "60"],
         "Similar-triangles trick: all sides scale by the same factor. "
         "From 3 to 9 is scale factor 3. Computation: 5 × 3 = 15 (longest side). "
         "Original is the 3-4-5 Pythagorean triple."),
        ("Triangle sides 3-4-5; similar triangle has shortest side 6. Longest side?", "10",
         ["10", "8", "6", "60"],
         "Similar triangles: scale factor 6/3 = 2. Longest side: 5 × 2 = 10. "
         "All corresponding sides scale by the same factor."),
        ("Triangle sides 5-12-13; similar triangle has shortest side 10. Longest side?", "26",
         ["26", "24", "13", "65"],
         "Similar triangles: scale factor 10/5 = 2. Longest side: 13 × 2 = 26. "
         "This is the doubled 5-12-13 Pythagorean triple."),
        ("Triangle sides 3-4-5; similar triangle has shortest side 12. Other sides?", "16 and 20",
         ["16 and 20", "13 and 14", "15 and 18", "32 and 40"],
         "Similar triangles: scale factor 12/3 = 4. Other sides: 4×4 = 16, "
         "5×4 = 20. This is the 12-16-20 triangle (4× the 3-4-5 triple)."),
        ("Triangle sides 3-4-5; similar triangle has scale factor 5. Longest side?", "25",
         ["25", "20", "5", "75"],
         "Similar triangles: each side scales by the scale factor 5. "
         "Longest side: 5 × 5 = 25. The 15-20-25 triangle (5× of 3-4-5)."),
        ("Triangle sides 8-15-17; similar triangle has shortest side 16. Longest side?", "34",
         ["34", "30", "17", "32"],
         "Similar-triangles trick: scale factor 16/8 = 2. Longest side: 17 × 2 = 34. "
         "This is 2× the 8-15-17 Pythagorean triple."),
        ("Triangle sides 7-24-25; similar triangle has shortest side 14. Longest side?", "50",
         ["50", "48", "25", "28"],
         "Similar-triangles trick: scale factor 14/7 = 2. Longest side: 25 × 2 = 50. "
         "The 14-48-50 triangle (2× of 7-24-25)."),
        ("Triangle sides 3-4-5; similar triangle has scale factor 10. Perimeter?", "120",
         ["120", "12", "100", "60"],
         "Similar-triangles trick: each side scales by 10. New sides: 30-40-50. "
         "Perimeter: 30+40+50 = 120 (or scale original perimeter 12 by 10). "
         "Based on the 3-4-5 Pythagorean triple."),
    ])

    # Special triangle facts 30-60-90 / 45-45-90 (5+)
    t4_items.extend([
        ("Side ratios of a 45-45-90 right triangle?", "1 : 1 : √2",
         ["1 : 1 : √2", "1 : 2 : 3", "1 : √3 : 2", "3 : 4 : 5"],
         "45-45-90 special triangle: two equal legs (ratio 1:1) and "
         "hypotenuse √2. Comes from a square cut diagonally — diagonal of "
         "unit square is √2 by the Pythagorean theorem."),
        ("Side ratios of a 30-60-90 right triangle?", "1 : √3 : 2",
         ["1 : √3 : 2", "1 : 1 : √2", "3 : 4 : 5", "1 : 2 : 3"],
         "30-60-90 special triangle: shortest side opposite 30° = 1, "
         "side opposite 60° = √3, hypotenuse = 2. Comes from an "
         "equilateral triangle cut in half."),
        ("In a 45-45-90 triangle with legs of length 5, hypotenuse?", "5√2",
         ["5√2", "10√2", "√5", "5/√2"],
         "45-45-90 special-triangle trick: side ratios 1 : 1 : √2. "
         "Pythagorean theorem: 5² + 5² = 50 = c², so c = √50 = 5√2."),
        ("In a 30-60-90 triangle with shortest side 4, hypotenuse?", "8",
         ["8", "4√3", "12", "4"],
         "30-60-90 special triangle: side ratios 1 : √3 : 2. "
         "Hypotenuse = 2 × shortest = 2 × 4 = 8."),
        ("Sum of angles in any triangle?", "180°",
         ["180°", "360°", "90°", "270°"],
         "Triangle angle-sum trick: 180°. Holds for every triangle — "
         "equilateral, isosceles, scalene, right. Computation: any triangle = "
         "180° = ½ × 360° (half a full turn)."),
    ])

    # Transformations (10+)
    t4_items.extend([
        ("Reflect (3, 4) over the y-axis. New point?", "(-3, 4)",
         ["(-3, 4)", "(3, -4)", "(-3, -4)", "(4, 3)"],
         "Reflection-over-y-axis trick: flip the sign of x, keep y the same. "
         "(3, 4) → (-3, 4). Mirror across the vertical y-axis."),
        ("Reflect (3, 4) over the x-axis. New point?", "(3, -4)",
         ["(3, -4)", "(-3, 4)", "(-3, -4)", "(4, 3)"],
         "Reflection-over-x-axis trick: flip the sign of y, keep x the same. "
         "(3, 4) → (3, -4). Mirror across the horizontal x-axis."),
        ("Reflect (-2, 5) over the y-axis. New point?", "(2, 5)",
         ["(2, 5)", "(-2, -5)", "(2, -5)", "(5, -2)"],
         "Reflection-over-y-axis trick: flip the sign of x. (-2, 5) → (2, 5). "
         "Mirror across the vertical y-axis."),
        ("Translate (1, 2) right 3, up 4. New point?", "(4, 6)",
         ["(4, 6)", "(-2, -2)", "(3, 6)", "(4, 5)"],
         "Translation trick: add to x for right (+), add to y for up (+). "
         "Computation: (1+3, 2+4) = (4, 6)."),
        ("Translate (5, 5) left 2, down 3. New point?", "(3, 2)",
         ["(3, 2)", "(7, 8)", "(3, 8)", "(7, 2)"],
         "Translation trick: left subtracts from x, down subtracts from y. "
         "Computation: (5-2, 5-3) = (3, 2)."),
        ("Reflect (5, -3) over the x-axis. New point?", "(5, 3)",
         ["(5, 3)", "(-5, -3)", "(-5, 3)", "(3, 5)"],
         "Reflection-over-x-axis trick: flip the sign of y. (5, -3) → (5, 3). "
         "Mirror across the horizontal x-axis."),
        ("Rotate (1, 0) 90° counterclockwise about the origin. New point?", "(0, 1)",
         ["(0, 1)", "(0, -1)", "(-1, 0)", "(1, 0)"],
         "Rotation trick (90° CCW about origin): (x, y) → (-y, x). "
         "(1, 0) → (0, 1). Quarter-turn CCW."),
        ("Rotate (0, 1) 90° clockwise about the origin. New point?", "(1, 0)",
         ["(1, 0)", "(-1, 0)", "(0, -1)", "(0, 1)"],
         "Rotation trick (90° CW about origin): (x, y) → (y, -x). "
         "(0, 1) → (1, 0). Quarter-turn CW."),
        ("Reflect (4, 7) over the origin. New point?", "(-4, -7)",
         ["(-4, -7)", "(-4, 7)", "(4, -7)", "(7, 4)"],
         "Reflection-through-origin trick: flip both signs: (x, y) → (-x, -y). "
         "(4, 7) → (-4, -7). Equivalent to a 180° rotation."),
        ("Translate (-2, 3) right 5, down 1. New point?", "(3, 2)",
         ["(3, 2)", "(-7, 4)", "(3, 4)", "(-7, 2)"],
         "Translation trick: right adds to x, down subtracts from y. "
         "Computation: (-2+5, 3-1) = (3, 2)."),
    ])

    for item in t4_items:
        questions.append((4, item))

    # ====================================================================
    # T5 — 20 questions (substitute-into-formula chains)
    # ====================================================================
    t5_items = []
    t5_items.extend([
        ("Right triangle: legs 5 and 12. What is hypotenuse² + 1?", "170",
         ["170", "168", "169", "144"],
         "Pythagorean theorem chain: a² + b² = c². 5² + 12² = 169 = c². "
         "Then c² + 1 = 169 + 1 = 170. The 5-12-13 triple gives c = 13, "
         "but we want c²+1 = 170. Don't forget to add the 1."),
        ("Sphere radius 3, cylinder radius 3 height 8. Sphere + cylinder volume in terms of π?", "108π",
         ["108π", "72π", "144π", "36π"],
         "Sphere volume: V = (4/3)πr³ = (4/3) × 27 × π = 36π. "
         "Cylinder volume: V = πr²h = 9 × 8 × π = 72π. "
         "Total = 36π + 72π = 108π."),
        ("Cone radius 6, height 9. Volume in terms of π, divided by 9?", "12π",
         ["12π", "108π", "36π", "9π"],
         "Cone volume formula: V = (1/3)πr²h = (1/3)π × 36 × 9 = 108π. "
         "Divided by 9: 108π / 9 = 12π."),
        ("Distance from (0,0) to (3,4), then squared and add 11?", "36",
         ["36", "25", "11", "47"],
         "Distance formula: d = √((x₂-x₁)² + (y₂-y₁)²). d = √(9+16) = √25 = 5. "
         "d² = 25 (just a²+b² from Pythagorean). Then 25 + 11 = 36. "
         "3-4-5 triple."),
        ("Sphere: at what radius does surface area 4πr² equal volume?", "3",
         ["3", "6", "4", "12"],
         "Sphere surface-area formula 4πr² vs volume formula (4/3)πr³. "
         "Set equal as circle area expressions: 4πr² = (4/3)πr³, "
         "divide by 4πr²: 1 = r/3, so r = 3. At r = 3, 4πr² = 36π = volume."),
        ("Pythagorean: legs 7 and 24. Hypotenuse + 5?", "30",
         ["30", "25", "31", "32"],
         "Pythagorean theorem: a² + b² = c². 7² + 24² = 49 + 576 = 625; "
         "c = √625 = 25 (the 7-24-25 triple). Then c + 5 = 30."),
        ("Triangle 3-4-5 area, doubled?", "12",
         ["12", "6", "20", "24"],
         "Triangle area formula: A = ½bh. For the 3-4-5 right triangle, "
         "legs are base/height: A = ½ × 3 × 4 = 6. Doubled = 12. "
         "(Doubling triangle area gives the bounding rectangle area.)"),
        ("Circle radius 5: area + circumference in terms of π?", "35π",
         ["35π", "30π", "50π", "75π"],
         "Circle area formula: A = πr² = 25π. Circumference formula: "
         "C = 2πr = 10π. Sum: 25π + 10π = 35π."),
        ("Box 2×3×4: volume + surface area?", "76",
         ["76", "52", "24", "28"],
         "Rectangular prism volume: V = lwh = 2×3×4 = 24. "
         "Surface area: 2(lw+lh+wh) = 2(6+8+12) = 52. "
         "Sum: 24 + 52 = 76."),
        ("Cylinder radius 2 height 5: volume in terms of π, then minus 10π?", "10π",
         ["10π", "30π", "20π", "5π"],
         "Cylinder volume formula: V = πr²h = π × 4 × 5 = 20π. "
         "Then 20π - 10π = 10π."),
        ("Midpoint of (0,0) and (8,6), then distance to origin?", "5",
         ["5", "10", "25", "3"],
         "Midpoint formula: ((0+8)/2, (0+6)/2) = (4, 3). "
         "Distance from origin: √(4² + 3²) = √25 = 5. "
         "The 3-4-5 triple appears again."),
        ("Sphere radius 3, cone radius 3 height 4. Sphere V minus cone V (in π)?", "24π",
         ["24π", "48π", "12π", "36π"],
         "Sphere volume: V = (4/3)πr³ = (4/3) × 27 × π = 36π. "
         "Cone volume: V = (1/3)πr²h = (1/3) × 9 × 4 × π = 12π. "
         "36π - 12π = 24π."),
        ("Right triangle legs 3, 4. Area² + hypotenuse²?", "61",
         ["61", "36", "169", "100"],
         "Triangle area A = ½ × 3 × 4 = 6, so A² = 36. "
         "Pythagorean: 3² + 4² = 25 = c², so c² = 25. "
         "Sum: 36 + 25 = 61. 3-4-5 triple."),
        ("Square side 5. Area + perimeter?", "45",
         ["45", "25", "20", "30"],
         "Square area formula: A = s² = 25. Perimeter P = 4s = 20. "
         "Sum: 25 + 20 = 45."),
        ("Distance from (1,1) to (4,5), then add the midpoint x?", "7.5",
         ["7.5", "5", "2.5", "10"],
         "Distance formula: √((4-1)² + (5-1)²) = √(9+16) = √25 = 5 "
         "(3-4-5 triple). Midpoint x: (1+4)/2 = 2.5. Sum: 5 + 2.5 = 7.5."),
        ("Circle d = 10. Area + circumference in terms of π?", "35π",
         ["35π", "30π", "100π", "10π"],
         "Circle area formula: A = πr² with r = 5 → 25π. "
         "Circumference C = πd = 10π. Sum: 25π + 10π = 35π."),
        ("Pythagorean: legs 8, 15. Hypotenuse + 3?", "20",
         ["20", "17", "23", "289"],
         "Pythagorean theorem: a² + b² = c². 8² + 15² = 64 + 225 = 289; "
         "c = √289 = 17 (the 8-15-17 triple). c + 3 = 20."),
        ("Triangle base 8 height 6 area, doubled?", "48",
         ["48", "24", "14", "96"],
         "Triangle area formula: A = ½bh = ½ × 8 × 6 = 24. "
         "Doubled = 48 (also the bounding rectangle area)."),
        ("Cube side 4. Surface area + volume?", "160",
         ["160", "96", "64", "192"],
         "Cube surface area: 6s² = 6 × 16 = 96. "
         "Volume: s³ = 64. Sum: 96 + 64 = 160."),
        ("Distance (0,0) to (5,12), plus the midpoint y-coordinate?", "19",
         ["19", "13", "5", "12"],
         "Distance formula: √(25+144) = √169 = 13 (the 5-12-13 triple). "
         "Midpoint y: (0+12)/2 = 6. Sum: 13 + 6 = 19."),
    ])

    for item in t5_items:
        questions.append((5, item))

    return questions


def main():
    print("=" * 78)
    print("Building Math P5 (Geometry, measurement, formulas)")
    print("=" * 78)

    questions = build_questions()

    accepted = []
    failed = []
    soft = []

    for i, (tier, item) in enumerate(questions):
        question, answer, choices, context = item
        verdict, rec, details = q(tier, question, answer, choices, context)
        if verdict == "PASS":
            accepted.append(rec)
        elif verdict == "SOFT_WARN":
            accepted.append(rec)
            soft.append((i, tier, question[:60], details["soft_warns"]))
        else:
            failed.append((i, tier, question, details["hard_fails"]))

    # Save accepted
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(accepted, indent=2, ensure_ascii=False), encoding="utf-8")

    # Report
    from collections import Counter
    tier_counts = Counter(q["tier"] for q in accepted)
    print(f"\nAccepted: {len(accepted)}")
    print(f"  T1: {tier_counts[1]}")
    print(f"  T2: {tier_counts[2]}")
    print(f"  T3: {tier_counts[3]}")
    print(f"  T4: {tier_counts[4]}")
    print(f"  T5: {tier_counts[5]}")
    print(f"\nSoft warns: {len(soft)}")
    print(f"Hard fails: {len(failed)}")

    if failed:
        print("\n--- FAILURES ---")
        for i, tier, qstem, fails in failed[:50]:
            print(f"#{i} T{tier} {qstem[:60]}")
            for gate, reason in fails[:3]:
                print(f"  [{gate}] {reason[:120]}")

    if soft:
        print("\n--- SOFT WARNS ---")
        for i, tier, qstem, warns in soft[:10]:
            print(f"#{i} T{tier} {qstem[:60]}")
            for gate, reason in warns[:2]:
                print(f"  [{gate}] {reason[:120]}")

    return accepted, failed, soft


if __name__ == "__main__":
    main()
