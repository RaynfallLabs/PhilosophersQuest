# Maths grade curve

*Slice 9 of the winning-build plan, 2026-11-13.*

Brandon: "math questions are legitimately tuned to tier to represent a smooth grade progression curve for mental math, and with practice, kids can get faster with higher tiers."

Maths is the timed subject. In combat, a run of right answers multiplies a weapon's damage, and the weapon's material picks the maths tier. Maths is the deliberate rote exception to the wonder rules, so facts and drills are fine here. What matters is that each tier is a real step up in mental maths from the one below.

## The five tiers

| Tier | Grades | Score band | What is in it |
|---|---|---|---|
| 1 | 1-2 | 1.0 to under 3.0 | Facts to 20, missing numbers, counting by 2s, 5s and 10s, tens and doubles within 100 |
| 2 | 3-4 | 3.0 to under 5.0 | Times tables to 12 x 12, division facts, rounding, two-digit sums with regrouping, tens across a hundred |
| 3 | 4-5 | 4.0 to under 6.0 | Multiplying by parts, three-digit sums, the order of operations, fractions of a number, decimals, benchmark percents, squares to 12 x 12 |
| 4 | 6-7 | 6.0 to under 8.0 | Any percent of a number, one- and two-step equations, negatives, squares to 20, cubes, roots, fraction division |
| 5 | 7-8 | 7.0 to under 9.0 | Exponent rules, Pythagorean triples, percent change and markups, roots to 29 x 29, signed arithmetic, two-digit by two-digit |

The bands overlap by a grade where the tiers do (tier 2 and tier 3 share grade 4; tier 4 and tier 5 share grade 7). Tier 3 meets tier 4 at grade 6.

## The score

`tools/balance/math_difficulty.py` reads each question's stem and gives it a **school-grade score**: 1.0 is the start of grade 1, 8.9 the end of grade 8. It is deterministic (no randomness) and shared by the curve tool, the quiz pipeline gate and the tests.

In plain words:

1. **The kind of question sets the starting grade.** That is the grade in which the standards first ask for it as mental work. Common Core comes first. The UK National Curriculum is named where it places a skill earlier than Common Core; the game's topic card teaches it. Examples:
   - single-digit sums: grade 1;
   - times-table facts: grade 3;
   - squares and the ² sign: grade 4 (UK Year 5);
   - benchmark percents: grade 5;
   - roots: grade 6;
   - two-step equations: grade 7;
   - exponent rules and Pythagoras: grade 8.
2. **The numbers move it up inside that kind**:
   - a carry or a borrow (+0.7 a grade each);
   - another column of digits;
   - a harder times-table fact (7 x 8 scores above 2 x 3);
   - a second step;
   - a bigger answer to hold in your head.
3. **A sum with several operations** starts at the grade of its hardest idea and adds a little for every step's arithmetic. The ideas are:
   - order of operations, grade 5;
   - with a power, grade 6;
   - with a negative number, grade 7.
4. **Trivial items** are flagged and never allowed above tier 1. These are times 0 or 1, divided by 1, a number divided by itself, plus 0, a power of 1, and the root of 1.
5. **Two kinds of exponent-rule item fall out of tier 5.**
   - One exponent is 1. "5^1 x 5^2" needs no rule: it is one more multiplication.
   - The answer is past the memorised power ladders. 5^8 = 390,625 and 3^7 = 2,187 are no longer mental work.

A few anchors:

| Question | Score | Tier |
|---|---|---|
| 3 + 4 | 1.3 | 1 |
| 9 + 8 | 2.0 | 1 |
| 15 + 30 | 1.8 | 1 |
| 7 x 8 | 3.6 | 2 |
| 57 + 64 | 3.8 | 2 |
| 47 x 6 | 4.7 | 3 |
| 347 + 86 | 4.4 | 3 |
| 4 + 7 x 4 | 5.3 | 3 |
| 75% of 800 | 5.8 | 3 |
| 15% of 240 | 6.8 | 4 |
| Solve: 4x + 7 = 51 | 7.5 | 4 |
| √49 | 6.3 | 4 |
| √324 | 7.5 | 5 |
| 6 - 4 x 3 | 7.2 | 5 |
| 23 x 24 | 7.1 | 5 |
| Pyth. triple: legs 8, 15 | 8.3 | 5 |

## Every topic's grade band

The data is in `tools/balance/math_grade_curve.json`. A topic may appear only at the tiers listed here.

| Topic | Tier | Grades | Standard | In plain words |
|---|---|---|---|---|
| Addition Facts | 1 | 1-2 | 1.OA.C.6, 2.OA.B.2 | Add two one-digit numbers from memory (sums to 20), add 0 or 10, know the doubles. |
| Subtraction Facts | 1 | 1-2 | 1.OA.C.6, 2.OA.B.2 | Subtract within 20 from memory, including across ten. |
| Missing Numbers | 1 | 1-2 | 1.OA.D.8 | Find the unknown number in an addition or subtraction fact. |
| Skip Counting | 1 | 1-2 | 2.NBT.A.2 | Count on by 2s, 5s and 10s. |
| Skip Counting | 2 | 3 | 3.OA.D.9 | Count on by 3s, 4s, 6s, 7s and 8s: the times tables as patterns. |
| Adding and Subtracting Tens | 1 | 1-2 | 1.NBT.C.4-6, 2.NBT.B.7 | Add or take away a multiple of 10 from a two-digit number. |
| Adding and Subtracting Tens | 2 | 3 | 3.NBT.A.2 | Add or take away tens across a hundred with three-digit numbers. |
| Doubling and Halving | 1 | 2 | 2.NBT.B.5, 2.OA.C.3 | Double or halve a two-digit number with no regrouping. |
| Doubling and Halving | 2 | 3 | 3.NBT.A.2, 3.OA.C.7 | Double or halve with regrouping, and three-digit numbers. |
| Times Tables | 2 | 3-4 | 3.OA.C.7, 3.NBT.A.3 (UK Year 4: tables to 12 x 12) | Every product of two one-digit numbers from memory, the 11s and 12s, and a digit times a multiple of 10. |
| Division Facts | 2 | 3-4 | 3.OA.C.7, 4.NBT.B.6 | Divide using the times tables, and a multiple of 10 by a digit. |
| Rounding | 2 | 3-4 | 3.NBT.A.1, 4.NBT.A.3 | Round to the nearest 10 or 100. |
| Two-Digit Addition and Subtraction | 2 | 3-4 | 2.NBT.B.5, 3.NBT.A.2 | Add and subtract two-digit numbers in your head, with regrouping. |
| Two-Digit Addition and Subtraction | 3 | 4-5 | 3.NBT.A.2, 4.NBT.B.4 | Add or subtract a two-digit number to or from a three-digit one, regrouping twice. |
| Multiplying by Parts | 2 | 3-4 | 3.NBT.A.3, 4.NBT.B.5 | A multiple of 10 times a digit; the easiest two-digit by one-digit products. |
| Multiplying by Parts | 3 | 4-5 | 4.NBT.B.5 | A two-digit number times a one-digit number by place value, or times a multiple of 10. |
| Multiplying by Parts | 4 | 6-7 | 5.NBT.B.5 (in your head) | Two teen numbers multiplied in your head. |
| Multiplying by Parts | 5 | 7-8 | 5.NBT.B.5 (in your head) | Two-digit by two-digit in your head, with carries. |
| Order of Operations | 3 | 5 | 5.OA.A.1 | Multiply before you add or subtract. |
| Order of Operations | 4 | 6 | 6.EE.A.2c | The order of operations with powers or two-digit products. |
| Order of Operations | 5 | 7 | 7.NS.A.3 | The order of operations when the answer or a number is negative. |
| Fractions, Decimals and Percents | 3 | 4-5 | 4.NF.C.6, 5.NBT.B.7 (UK Year 5: percent equivalents) | Halves, quarters, fifths and tenths as decimals and percents; adding and multiplying simple decimals. |
| Fractions, Decimals and Percents | 4 | 6-7 | 6.RP.A.3c, 7.NS.A.2d | Eighths and thirds as decimals and percents. |
| Fractions, Decimals and Percents | 5 | 7 | 7.NS.A.2d | Repeating decimals (sixths, ninths, twelfths) to three places. |
| Percent of a Number | 3 | 5 | 6.RP.A.3c (UK Year 6: percentages of amounts) | 10%, 20%, 25%, 50% and 75% of a round number. |
| Percent of a Number | 4 | 6-7 | 6.RP.A.3c | Any whole percent of a number by splitting it (30% is 3 x 10%, 15% is 10% + 5%). |
| Percent of a Number | 5 | 7 | 7.RP.A.3 | Increases and decreases (markups and sales), percents over 100% and fractional percents. |
| Finding the Percent | 4 | 6 | 6.RP.A.3c | What percent one number is of another. |
| Finding the Percent | 5 | 7 | 7.RP.A.3 | Percent increase and decrease; parts over 100%. |
| Simplifying Fractions | 3 | 4-5 | 4.NF.A.1, 6.RP.A.1 (UK Year 6: ratio) | Simplify a ratio by dividing both parts by their greatest common factor. |
| Fraction of a Quantity | 3 | 4-5 | 4.NF.B.4, 5.NF.B.4 | A fraction of a whole number: divide by the bottom, multiply by the top. |
| Fraction of a Quantity | 4 | 6 | 5.NF.B.4, 6.NS.A.1 | A fraction of a fraction of a number, and larger two-step shares. |
| Fraction Arithmetic | 3 | 5 | 5.NF.A.1, 5.NF.B.4 | Add, subtract and multiply fractions with unlike denominators. |
| Fraction Arithmetic | 4 | 6 | 6.NS.A.1 | Divide a fraction by a fraction. |
| Fraction Arithmetic | 5 | 7 | 7.NS.A.1-2 | Fraction arithmetic with negative numbers. |
| Squares, Cubes and Powers | 3 | 4-5 | 5.NBT.A.2, 6.EE.A.1 (UK Year 5: square and cube numbers) | Squares to 12 x 12, small cubes, powers of 10 and of 2. |
| Squares, Cubes and Powers | 4 | 6-7 | 6.EE.A.1, 6.EE.A.2c | Squares to 20, cubes to 10, higher powers, sums and differences of squares. |
| Squares, Cubes and Powers | 5 | 7-8 | 6.EE.A.1 in your head; A-SSE.A.2 for b^2 - a^2 | Squares from 21 to 29, the cubes of 11 to 13, and differences of squares by (b - a)(b + a). |
| Square and Cube Roots | 4 | 6-7 | 8.EE.A.2 (UK Year 7: powers and roots) | Square roots of perfect squares to 15 x 15 (and 20 x 20, 30 x 30); cube roots to 4. |
| Square and Cube Roots | 5 | 8 | 8.EE.A.2 | Square roots up to 29 x 29; cube roots up to 9. |
| Negative Numbers | 4 | 6-7 | 6.NS.C.5-7, 7.NS.A.1-2 | Add and subtract across zero; multiply with signs. |
| Negative Numbers | 5 | 7 | 7.NS.A.2 | Divide with signs; larger signed products. |
| Divisibility Rules | 3 | 4-5 | 4.OA.B.4 | Which of four numbers divides a two-digit number. |
| Divisibility Rules | 4 | 6 | 6.NS.B.4 | Divisibility tests for 3, 4, 6, 7, 8, 9, 11 and 12 on three-digit numbers. |
| One-Step Equations | 4 | 6 | 6.EE.B.7 | Solve x + p = q, x - p = q, px = q and x/p = q. |
| Two-Step Equations | 4 | 7 | 7.EE.B.4a | Solve px + q = r. |
| Two-Step Equations | 5 | 7-8 | 7.EE.B.4a, 8.EE.C.7 | Solve p(x + q) = r, and two-step equations with a negative answer. |
| Exponent Rules | 5 | 8 | 8.EE.A.1 | Multiply or divide powers of the same base by adding or subtracting the exponents. |
| Pythagorean Triples | 5 | 8 | 8.G.B.7 | Find a side of a right triangle from a known whole-number triple. |
| Sum of 1 to N | 4 | 6 | enrichment (patterns) | Add 1 to n for small n, by pairing or by adding. |
| Sum of 1 to N | 5 | 7-8 | enrichment (Gauss's pairing trick) | The pairing trick n(n + 1)/2 for larger n. |

## The tools

- `py -m tools.balance.math_grade_curve --audit` lists every question outside its tier's band.
- `py -m tools.balance.math_grade_curve` curves `data/questions/math.json` in place. It is deterministic and idempotent: a curved bank comes back unchanged.
  1. **Move.** An out-of-band question goes to the tier whose band fits it, when its topic has a grade band there and that tier has room. No tier grows by more than 8%. A topic that has no band at its own tier moves first, so it is not lost.
  2. **Replace.** Whatever cannot move is replaced in place by a new in-band question of the same topic. Where the topic has no band at that tier, a fill topic is used instead.
  3. **Backfill.** A tier that lost more questions than it gained is topped back up to its old size.
  4. **Check.** Every new question is generated from code, checked by the answer oracle (`check_answer`: the key is right and no other choice is), rated in band, and never repeats a stem anywhere in the bank or spells out a sum from its topic's card.
- `py tools/balance/build_math_bank_v3.py` rebuilds from scratch and runs the same curve. The shipped bank is no longer this script's exact output: bug bashes fixed the JSON by hand, and the script's random draws have shifted since. Re-curving the shipped bank is the tool of record. The script also carries the three hand fixes it was missing.
- `py -m tools.quizgen validate --subject math` now runs the `math_grade_band` gate (`tools/quizgen/deterministic/math_grade_band.py`).
- `tests/test_math_grade_curve.py` checks the bank:
  - every question is inside its band;
  - the tier medians climb;
  - every topic has a band at its tier;
  - tier sizes stay within 10% of the 3.4.0 sizes;
  - no trivial item sits above tier 1, and no stem is in two tiers;
  - every key is right;
  - the tiers meet without a cliff;
  - the shipped bank is its own curve.

## What slice 9 changed

The 3.4.0 bank had 841 questions outside their tier's band (the gate's count), plus 53 stems that sat in two tiers. Tier 5's median was grade 6.5, barely above tier 4's 6.1.

| Tier | Questions before -> after | Median score before -> after | Min / max after | Median digits | Median steps | Carries + borrows (mean) |
|---|---|---|---|---|---|---|
| 1 | 488 -> 527 | 1.63 -> 1.67 | 1.00 / 2.65 | 2 | 1 | 0.28 |
| 2 | 560 -> 604 | 3.10 -> 3.20 | 3.00 / 4.90 | 2 | 1 | 0.36 |
| 3 | 422 -> 455 | 4.80 -> 5.20 | 4.03 / 5.92 | 2 | 1 | 0.40 |
| 4 | 495 -> 534 | 6.10 -> 6.40 | 6.00 / 7.87 | 3 | 2 | 0.07 |
| 5 | 450 -> 450 | 6.50 -> 7.71 | 7.00 / 8.94 | 3 | 2 | 0.38 |

What happened to the questions:

- 1,570 are unchanged.
- 382 moved tier, mostly downward:
  - two-digit sums T3 -> T2;
  - tens and doubles T2 -> T1;
  - fractions of a number, benchmark percents and small powers T4 -> T3;
  - teen products, the order of operations, percents and fraction arithmetic T5 -> T3/T4.
- Some moved up: negatives, roots and teen squares went T3 -> T4.
- 463 were replaced in place by new questions of the same topic:
  - x 0 and x 1 facts and tens within 100 in T2;
  - two-digit sums in T3, replaced by three-digit ones;
  - simple fractions of a number in T4, replaced by two-step shares;
  - in T5, exponent items that were trivial or past the ladders, plus stems duplicated in tier 4.
- 155 are new tier 5 questions. They top tier 5 back up to 450 with grade 7-8 work: two-digit products, percent change, markups and discounts, signed order of operations, negative fractions, roots to 29 x 29, and differences of squares.

The full counts by tier and topic print from `py -m tools.balance.math_grade_curve --dry-run` (run on the 3.4.0 bank).

## Answer times: a model for the simulator

`practised_seconds(rating)` is 0.9 s to read the stem, find the key among four and press it, plus 0.6 s for each fluent mental operation in the rating's `work`. The model treats each piece of work as one operation:

- a fact recalled;
- a carry;
- a partial product held;
- a percent piece;
- an inverse step.

The constants are set against the arithmetic-fluency literature:

- practised single-digit sums and products take about 1 s to produce;
- a two-digit sum with a carry takes about 3 s;
- a two-digit by one-digit product takes about 3-4 s;
- four choices allow some estimating.

It is a model, not a measurement.

| Tier | Practised median | Practised mean | First time (x1.5, mean) | Today's simulator guess |
|---|---|---|---|---|
| 1 | 1.7 s | 1.7 s | 2.5 s | 1.6-2.0 s |
| 2 | 2.0 s | 2.3 s | 3.4 s | 2.6 s |
| 3 | 2.8 s | 3.0 s | 4.5 s | 4.5 s |
| 4 | 3.6 s | 4.1 s | 6.1 s | 6 s |
| 5 | 3.4 s | 3.9 s | 5.8 s | 7 s |

The simulator's current guesses match the model's first-timer column closely at tiers 3 and 4. So a practice curve that falls by about a third over the first few hundred answers at a tier lands near the practised column.

Tier 5 is about as quick as tier 4 once practised, though it is a grade harder. Its grade-8 work is mostly memorised ladders: roots, triples, powers, and the exponent rule on known powers. Those get fast with practice. Tier 4's percents, shares and equations are worked out fresh each time. Tier 5's slow tail is the two-digit products and the signed order of operations: 90th percentile 6.3 s practised.
