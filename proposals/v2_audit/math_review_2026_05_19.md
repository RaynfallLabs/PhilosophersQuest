# Math Bank Review — 2026-05-19

Full audit of `data/questions/math.json`. Math is the most over-floor bank (all tiers ≥200), so the task here is quality cleanup, not gap-filling.

## Starting state

```
Tiers: T1=517, T2=773, T3=621, T4=266, T5=296 — total 2473
Validation: 2473 KEEP, 0 REPAIR, 0 DISCARD
Dropped/math.json: 289
```

## Ending state

```
Tiers: T1=471, T2=779, T3=623, T4=290, T5=292 — total 2455
Validation: 2455 KEEP, 0 REPAIR, 0 DISCARD
pytest -q: 598 passed
Dropped/math.json: 307 (+18)
```

Net: 18 questions dropped, 40 retiered, 2 grammar fixes, 78 metadata cleanups.

## 1. Drops — 18 questions → dropped/math.json

Math stance bans calculus, set-theory paradoxes, math-history biography (per `_regrade_math.py` DROP_MARKERS + `feedback_no_rote_wonder.md`). The bank had survivors that should never have remained at any tier.

### Math-history biography (11 items)
| idx | T | question | answer |
|-----|---|----------|--------|
| 522  | T1 | "Zero as a written numeral was developed by…" | "Indian mathematicians" |
| 1384 | T1 | "Newton's calculus rival was ___." | "Leibniz" |
| 2057 | T1 | "Sophie Germain corresponded with Gauss under what guise?" | "A male pseudonym (M. Le Blanc)" |
| 2208 | T5 | "Who named imaginary numbers 'imaginary'?" | "Descartes (dismissively)" |
| 2394 | T5 | "e was first studied by Bernoulli through which problem?" | "Compound interest" |
| 2397 | T3 | "How many digits of π are known computed by current records?" | "Trillions" |
| 2399 | T1 | "Who proved the parallel postulate independent of Euclid's other axioms?" | "Bolyai, Lobachevsky, Gauss" |
| 2400 | T2 | "Riemann generalized Euclidean geometry to?" | "Curved manifolds" |
| 2401 | T1 | "Carl Friedrich Gauss called number theory the?" | "Queen of mathematics" |
| 2402 | T1 | "David Hilbert's 1900 address listed how many open problems?" | "23" |
| 2403 | T2 | "Bernhard Riemann's 1859 paper introduced?" | "The Riemann hypothesis" |

These are wonder/trivia stems with mathematician names. They violate math stance (math is rote-by-design, wonder lives in other subjects).

### Calculus (5 items)
| idx | T | question | answer |
|-----|---|----------|--------|
| 2339 | T5 | "A function f is increasing on an interval if:" | "Whenever a < b in it, then f(a) < f(b)" |
| 2343 | T5 | "What are the asymptotes of y = 1/x?" | "The x-axis and the y-axis" |
| 2360 | T5 | "Why is the number e called the 'natural' base for exponentials?" | "The derivative of e^x is e^x" |
| 2361 | T5 | "Limits formalize what intuitive notion?" | "Approaching a value without necessarily reaching" |
| 2362 | T5 | "If a function has a local maximum at x = c and is smooth there, what is f'(c)?" | "Zero — the tangent there is horizontal" |

Asymptotes, limits, derivatives, "smooth/increasing function" formal-defns — all beyond 10th-grade per `TIER_CAPS.md`.

### Near-duplicate Pythagorean theorem (2 items)
Three near-identical "a² + b² = ?" → "c²" at T5. Kept the most natural phrasing (idx 2217: "Pythagoras' theorem says, for a right triangle with legs a, b and hypotenuse c?"), dropped the other two:

| idx | T | question |
|-----|---|----------|
| 159  | T5 | "Pythagoras's theorem: a² + b² = ?" |
| 517  | T5 | "The Pythagorean theorem: a² + b² = ?" |

## 2. Tier shifts — 40 questions retiered

### T1 → T2 (5 items) — simple word problems, order-of-ops, squaring
Math T1 is 5th-grade arithmetic. Word problems and order-of-ops belong at T2 per the bank's existing pattern.

- 1230 "Resolve both parens first: (9 − 4) × (3 + 2)" — order of operations
- 1371 "Pencils cost 25¢ each. 8 pencils?" — word problem
- 1374 "Sue is 5 years older than Tim. Sum of ages 23. Tim's age?" — age word problem
- 1397 "Evaluate: (7 − 3)²" — squaring
- 1407 "Evaluate: (5 + 3)²" — squaring

Also T1 → T2 vocab (3 items):
- 1176 "If a÷b = c with r left, c is the:" (Quotient)
- 1177 "If a÷b = c with r left, a is the:" (Dividend)
- 1178 "If a÷b = c with r left, b is the:" (Divisor)

### T1 → T3 (3 items) — operation properties / multiplicative inverse
These are middle-school algebra concepts (commutative property, multiplicative inverse), not 5th-grade arithmetic.

- 1186 "Property that says a + b = b + a:" (Commutative)
- 1191 "The multiplicative inverse of 4 is:" (1/4)
- 1192 "Is subtraction commutative?" (No)

### T1 → T4 (21 items) — 3D volume, perfect numbers, similarity, coordinates, equations
Coordinate-plane quadrants, 1-var equations, similarity/congruence, perfect numbers, box volume — all 8th-grade.

- 481 "Point (3, 5) — which quadrant?"
- 490 "If x − 4 = 10, x = ?"
- 1269 "Use the alternating-digits rule — which is a multiple of 11?" (divisibility-rule advanced)
- 1282 "Rectangular box 4 × 5 × 6. Volume?" — 3D volume
- 1874-1888 "Box ... Volume?" — 15 items, all 3D volume (T4 per pattern in rest of bank)
- 1891 "Which is a perfect number?"
- 1892 "First perfect number:"
- 1903 "Two shapes the same size AND shape are: Congruent"
- 1904 "Two shapes the same shape but possibly different sizes are: Similar"
- 1934 "Which is a perfect number?" (dup-style)

### T1 → T5 (5 items) — combinatorics, geometric series
Combinatorial counting (anagrams, choose-k, nCn, factorials) is T5 per spec.

- 2006 "How many ways to choose 3 books from 8? (order doesn't matter)" → 56
- 2013 "How many ways to seat 5 people in a row?" → 120
- 2368 "Sum of finite geometric: 1 + 2 + 4 + 8 + 16 = ?" — geometric series T5
- 2387 "nCn = ?" — combinatorial notation
- 2390 "How many distinct anagrams of 'BOOK'?" → 12

## 3. Grammar — 2 fixes

| idx | from | to |
|-----|------|----|
| 380 | "How many sides does a octagon have?" | "How many sides does an octagon have?" |
| 1139 | "What defines an scalene triangle?" | "What defines a scalene triangle?" |

## 4. Metadata cleanup — 78 questions

Three classes of formatting artifacts removed:

### Leading-zero formatting (45 items)
Choices like `'04'`, `'06'`, `'09'`, `'013'`, `'017'`, `'060%'`, `'07.0'`, `'03.8%'`, `'Tim = 09'`, `'012 min'` → cleaned to `'4'`, `'6'`, `'9'`, `'13'`, `'17'`, `'60%'`, `'7.0'`, `'3.8%'`, `'Tim = 9'`, `'12 min'`. Critically the regex preserves valid decimals (`0.5`, `1.05`, `−0.05`, `0.30`) and thousands separators (`1,000`).

### `'='` prefix in answer/choice (13 items)
Choices like `'= 09'`, `'= 1/2'`, `'= +14'`, `'= half × the'`, `'==  4'` → stripped to `'9'`, `'1/2'`, `'+14'`, `'half × the'`, `'4'`. Double-`==` artifact normalized to single `=`.

### Trailing-dot choice formatting (9 items)
Choices like `'10.'`, `'20.'`, `'27.'`, `'15.'` → stripped to `'10'`, `'20'`, `'27'`, `'15'`. Only applies to pure integer-followed-by-dot; decimals (`'1.0'`, `'$1.50'`) unaffected.

Total of 78 questions had at least one of these artifacts cleaned.

## 5. Topic coverage map (final bank)

| topic                    | T1 | T2  | T3  | T4 | T5  | sum |
|--------------------------|----|-----|-----|----|-----|-----|
| arithmetic               | 401| 56  | 4   | 0  | 11  | 472 |
| other                    | 28 | 95  | 176 | 29 | 18  | 346 |
| percentages              | 2  | 144 | 15  | 7  | 1   | 169 |
| number_theory            | 0  | 73  | 59  | 4  | 0   | 136 |
| fractions                | 10 | 104 | 6   | 11 | 1   | 132 |
| exponents                | 0  | 49  | 36  | 21 | 6   | 112 |
| quadratics               | 0  | 0   | 0   | 0  | 97  | 97  |
| algebra_solve            | 0  | 0   | 36  | 54 | 0   | 90  |
| angles_lines             | 2  | 54  | 14  | 5  | 3   | 78  |
| sequences_series         | 0  | 0   | 23  | 0  | 55  | 78  |
| area                     | 0  | 56  | 15  | 3  | 0   | 74  |
| ratio_proportion         | 0  | 0   | 65  | 6  | 0   | 71  |
| decimals                 | 5  | 46  | 10  | 7  | 1   | 69  |
| statistics               | 5  | 0   | 56  | 0  | 7   | 68  |
| probability              | 0  | 0   | 60  | 0  | 0   | 60  |
| rounding_estimation      | 0  | 39  | 2   | 0  | 0   | 41  |
| perimeter_circumference  | 0  | 22  | 14  | 1  | 0   | 37  |
| coordinate_geometry      | 0  | 0   | 0   | 35 | 0   | 35  |
| combinatorics            | 0  | 0   | 4   | 0  | 27  | 31  |
| measurement              | 6  | 4   | 16  | 5  | 0   | 31  |
| sqrt_cube_root           | 0  | 0   | 0   | 25 | 2   | 27  |
| polygons_shapes          | 4  | 20  | 1   | 1  | 0   | 26  |
| trig                     | 0  | 0   | 0   | 0  | 24  | 24  |
| logarithm                | 0  | 1   | 0   | 0  | 22  | 23  |
| volume                   | 1  | 0   | 1   | 19 | 1   | 22  |
| pythagorean              | 0  | 13  | 0   | 4  | 4   | 21  |
| functions                | 0  | 0   | 0   | 17 | 4   | 21  |
| algebra_expand           | 0  | 0   | 0   | 20 | 0   | 20  |
| platonic_solids          | 0  | 0   | 0   | 13 | 1   | 14  |
| complex_numbers          | 0  | 0   | 0   | 0  | 7   | 7   |
| absolute_value           | 0  | 0   | 6   | 0  | 0   | 6   |
| properties               | 0  | 2   | 4   | 0  | 0   | 6   |
| word_problems            | 5  | 1   | 0   | 0  | 0   | 6   |
| scientific_notation      | 0  | 0   | 0   | 3  | 0   | 3   |
| place_value              | 2  | 0   | 0   | 0  | 0   | 2   |

(`other` = generic clusters not landing in any single topic — mostly multi-topic word problems, integer ops, mixed arithmetic.)

### Tier-2-to-4 coverage check
Per `TIER_CAPS.md`: every major topic with ≥3 questions should have ≥2 at every T2-T4 OR be a topic that's tier-bound by spec.

Topics with thin or single-tier coverage:
- `quadratics` — T5 only (spec: quadratics ARE T5 by definition; T4 has `algebra_expand`/`algebra_solve` instead) ✓
- `combinatorics` — T3=4 + T5=27, T4=0 (spec: combinatorics IS T5 per regrader; T3 has 4 "subsets of N" + "P(events)") ✓
- `coordinate_geometry` — T4=35 only (spec: slope/midpoint are 8th-grade) ✓
- `trig`, `logarithm` — T5 only (per spec) ✓
- `complex_numbers` — T5 only (per spec) ✓
- `place_value` — T1=2 only (sparse but appropriate; small total) — acceptable
- `properties` — T2=2 + T3=4, T4=0 (sparse but plausible; commutative-style only goes so far) — acceptable

No gaps that demand new content per the prompt's "NO TIER FILLS REQUIRED" rule.

## 6. Validation

```
$ py -m tools.quizgen validate --subject math
Validated 2455 math questions: 2455 KEEP, 0 REPAIR, 0 DISCARD

$ pytest -q
598 passed in 54.36s
```

## Scripts (gitignored, scratch/)

- `tools/quizgen/scratch/math_audit_plan.py` — dry-run of all changes
- `tools/quizgen/scratch/math_audit_apply.py` — actual apply (used)
- `tools/quizgen/scratch/math_review_diff.py` — diff vs deterministic regrader
- `tools/quizgen/scratch/math_topic_coverage.py` — topic-cluster report
- `tools/quizgen/scratch/math_audit_report.py` — final-state summary
