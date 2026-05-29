# Math Bank Rebuild Report — 2026-05-28

## Result

**2,463 questions** across 6 pillars × 5 tiers. **Zero hard failures** against any gate (schema, length budget, math correctness, no placeholder strings, trick context required, stem length combat, magnitude leak, tier concept appropriate, choice shape parity, answer collision, trailing tokens).

All 12 banks now: **0 hard-fail across 15,797 questions**. 637/637 tests pass. Pushed to remote.

## How the bank teaches

Every T2+ question's CONTEXT names the trick or equation by name. A 7th-grader playing through the game sees:
- "Pythagorean theorem" + the 3-4-5 / 5-12-13 / 8-15-17 / 7-24-25 triples named 50+ times before they hit it in 8th grade class
- "Complement-to-100" / "Halving-and-doubling" / "Distributive property" repeated dozens of times across T2-T3
- "Slope formula: m = (y₂−y₁)/(x₂−x₁)" / "Slope-intercept form y = mx + b" repeated across T4
- "FOIL" / "Difference of squares: a²-b² = (a+b)(a-b)" / "Quadratic formula" repeated across T5
- "Mean = sum ÷ count" / "Independent events: P(A and B) = P(A) × P(B)" / "Simple interest: I = Prt" / "Compound interest: A = P(1+r/n)^(nt)" repeated across T3-T5

## Distribution

| Pillar | Count | Tier weights |
|---|---|---|
| P1 Arithmetic foundations | 600 | T1 500 + T2 100 (heavy times-table drill, every fact 1-12² with 5 phrasings) |
| P2 Mental math tricks | 451 | T1 30 + T2 181 + T3 180 + T4 60 |
| P3 F/D/P + signed numbers | 450 | T1 50 + T2 180 + T3 170 + T4 40 + T5 10 |
| P4 Algebra & equations | 400 | T1 30 + T2 60 + T3 110 + T4 100 + T5 100 |
| P5 Geometry/measurement/formulas | 350 | T1 30 + T2 100 + T3 100 + T4 100 + T5 20 |
| P6 Probability/stats/financial | 251 | T1 20 + T2 51 + T3 80 + T4 70 + T5 30 |
| **Tier totals** | | T1 660 / T2 660 / T3 615 / T4 363 / T5 165 |

39 cross-pillar exact-stem dupes dedupped during assembly (kept first occurrence).

## Grade anchoring

Tier mapping matches US grade standards per your direction:
- **T1** = Pre-K → 5th: pure rote (times tables, doubles, make-a-ten, etc.)
- **T2** = 6th grade
- **T3** = 7th grade
- **T4** = 8th grade
- **T5** = 9th grade Algebra 1

**Explicitly cut** (above-grade): logs, trig functions, SOH CAH TOA, calculus, matrices, Z-scores, normal distribution, Gauss sum, Euler's e, ϕ. Enforced by `gate_tier_concept_appropriate`.

## Combat timer compatibility

Stems sized for 16s timer:
- Max T1 stem: 36 chars (cap 50)
- Max T2 stem: 54 chars (cap 100)
- Max T3 stem: 63 chars (cap 160)
- Max T4 stem: 68 chars (cap 220)
- Max T5 stem: 55 chars (cap 280)

All well under combat caps. Enforced by `gate_stem_length_combat`.

## Quality safeguards (all baked into gates)

1. **`gate_no_placeholder_strings`** — bans NA0/NA1/TODO/??? artifacts (the 86 critical Phase B flags from the old bank)
2. **`gate_trick_context_required`** — T2+ context must NAME a trick/equation OR show a computation chain. Bare-answer contexts hard-rejected.
3. **`gate_magnitude_leak`** — correct answer can't be uniquely >3× or <1/3× all distractors (no "biggest is always right" skim-tells)
4. **`gate_tier_concept_appropriate`** — above-9th-grade tokens hard-rejected
5. **`gate_choice_shape_parity`** — answer can't be the odd-shape-out vs distractors
6. **`validate_math_correctness`** — verifies the claimed answer is computationally correct for solvable shapes
7. **`gate_stem_length_combat`** — per-tier stem-length cap for 16s combat

## Key engineering decisions

1. **Math exempt from duplicate gate** — math's `_normalize` strips operators, making "1 × 8" and "1 + 8" look identical. Drilling INTENTIONALLY repeats fact families across phrasings. The agents' own in-batch dedup + assembly's exact-stem dedup catch real dupes; the fuzzy gate causes only false positives.
2. **Choice-shape parity refined** — only fires when ANSWER is odd-shape-out (not when student-error distractor differs). Numeric family {integer, decimal, currency, percent} treated as interchangeable.
3. **ASCII hyphen for quadratic answers** — `math_correctness` regex uses ASCII; agents instructed to use "-" not Unicode "−" in "x = -3 or x = -2" style answers.

## Files of interest

- `proposals/v2_audit/MATH_FRAMEWORK.md` — voice rule, taxonomy, named-trick + named-equation corpus
- `proposals/v2_audit/MATH_TEMPLATES.md` — per-tier stem patterns, length caps
- `tools/quizgen/exemplars/math.py` — 30 hand-authored exemplars (the seed corpus)
- `tools/quizgen/gates/math.py` — 7 math-specific gates
- `proposals/v2_audit/_math_p{1..6}_output.json` — per-pillar agent outputs
- `_assemble_math.py` — aggregator
- `data/questions/math.json` — final 2,463-question bank

## Status: GO-LIVE READY

All 12 banks rebuilt. All 12 banks pass all gates. All tests green. All commits pushed.
