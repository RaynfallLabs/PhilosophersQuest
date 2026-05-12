---
version: 1
date: 2026-05-11
subject: math
---

# Math strategy taxonomy

Every math question in Philosopher's Quest should point at a named pedagogical move. Two pillars:

1. **Computation strategies** — the mental moves fluent calculators use to derive facts fast (NCTM "derived facts" / Boaler-Parrish "number talks" / Common Core "fluency").
2. **Vocabulary & concept recognition** — names for shapes, angles, properties, and number categories students don't see daily (Pimm 1987, *Speaking Mathematically*).

Both pillars serve the same goal: practice the moves and words that aren't visible in everyday life. A question is *pedagogical* when its distractors are the answers a learner would get by skipping the strategy or confusing the term.

Every math question gets a `_meta.strategy` field naming which strategy it teaches. Coverage is audit-able.

## Pillar 1 — Computation strategies

### Additive (T1, mostly)

| Strategy ID | The move | Example | Distractor design |
|---|---|---|---|
| `make_ten_addition` | Bridge to 10: `8+5 = 8+2+3 = 10+3` | `8 + 5 = ?` → 13 | 10 (stopped at the make-ten step), 12 (off-by-one), 14 |
| `near_doubles` | Use known double: `7+8 = 7+7+1` | `7 + 8 = ?` → 15 | 14 (used 7+7), 16 (used 8+8), 13 |
| `compensate_addition` | Round one, adjust: `29+47 = 30+47−1` | `29 + 47 = ?` → 76 | 75 (forgot adjustment), 77 (wrong-direction adjust), 86 |
| `split_addition` | Place-value split: `47+38 = (40+30)+(7+8)` | `47 + 38 = ?` → 85 | 75 (forgot to carry), 815 (concatenation error), 84 |
| `subtract_by_add_up` | Count up: `83−47 → 47+3=50, 50+33=83 → 36` | `83 − 47 = ?` → 36 | 44 (subtracted wrong way), 46 (carry error), 35 |
| `compensate_subtraction` | Round to easier: `83−39 = 83−40+1` | `83 − 39 = ?` → 44 | 43 (forgot adjustment), 45, 54 |

### Multiplicative (T1-T2)

| Strategy ID | The move | Example | Distractor design |
|---|---|---|---|
| `times_table_anchor` | Direct recall ×1, ×2, ×5, ×10 facts | `6 × 5 = ?` → 30 | 25 (×5−1), 35 (×5+1), 11 (added) |
| `multiply_by_5` | Halve and ×10: `28×5 = 14×10` | `28 × 5 = ?` → 140 | 70 (halved without ×10), 280 (×10 without halving), 130 |
| `multiply_by_9` | ×10 minus ×1: `9×7 = 70−7` | `9 × 7 = ?` → 63 | 70 (forgot to subtract), 56 (subtracted twice), 64 |
| `multiply_by_11_single` | Repeat digit: `11×6 = 66` | `11 × 7 = ?` → 77 | 71, 88, 18 (sum-instead-of-multiply) |
| `multiply_by_11_double` | Outside-then-add-inside: `11×34 = 3(3+4)4 = 374` | `11 × 34 = ?` → 374 | 344 (no add), 384, 444 |
| `halve_then_double` | Restructure: `14×5 = 7×10` | `14 × 5 = ?` → 70 | 60, 28, 19 |
| `multiply_by_powers_of_10` | Shift decimal | `47 × 100 = ?` → 4700 | 470, 47000, 147 |
| `double_double_double` | ×8 via three doublings | `13 × 8 = ?` → 104 | 96, 26 (one doubling), 80 |

### Number sense (T1-T2)

| Strategy ID | The move | Example |
|---|---|---|
| `doubling_chain` | Powers of 2 from anchor: `8 → 16 → 32 → 64` | `What is double 32?` → 64 |
| `halving_chain` | Powers of ½: `64 → 32 → 16` | `Half of 48 is?` → 24 |
| `round_to_anchor` | Nearest 10/100: `487 → 500` | `Round 487 to nearest hundred.` → 500 |
| `magnitude_comparison` | Order-of-magnitude: `0.3 vs 0.29` | `Which is larger: 0.3 or 0.29?` → 0.3 |
| `negative_compare` | Number-line: `−8 < −3` | `Which is larger: −8 or −3?` → −3 |

### Fraction / decimal / percent (T2-T3)

| Strategy ID | The move | Example |
|---|---|---|
| `fraction_common_denom` | Find LCD: `½ + ⅓ → 3/6 + 2/6` | `½ + ⅓ = ?` → 5/6 |
| `fraction_simplify` | Divide num+denom: `4/8 → 1/2` | `Simplify 8/12.` → 2/3 |
| `decimal_align` | Line up decimal point: `0.7 + 0.25` | `0.7 + 0.25 = ?` → 0.95 |
| `percent_10_anchor` | 10% = move decimal: `350 → 35` | `10% of 350 = ?` → 35 |
| `percent_easy_anchors` | 50% halve, 25% quarter, 75% three-quarters | `25% of 80 = ?` → 20 |
| `percent_flip` | `a% of b = b% of a`: `8% of 50 = 50% of 8 = 4` | `8% of 50 = ?` → 4 |
| `ratio_scaling` | Multiply both sides: `3:4 = 6:8 = 9:12` | `If 3:4, then 9:?` → 12 |

### Algebra (T3-T4)

| Strategy ID | The move | Example |
|---|---|---|
| `isolate_x_one_step` | Subtract / divide: `x+5=12 → x=7` | `x + 5 = 12` → 7 |
| `isolate_x_two_step` | Unwrap in reverse order | `2x + 5 = 13` → 4 |
| `balance_both_sides` | Move terms across `=` | `3(x−2) = 2x+5` → 11 |
| `distribute` | `a(b+c) = ab+ac` | `Expand 3(x+4).` → 3x+12 |
| `factor_difference_squares` | `a² − b² = (a+b)(a−b)` | `x²−9 = ?` → (x+3)(x−3) |
| `factor_quadratic_simple` | Sum/product trick: `x²−5x+6` | `Solve x²−5x+6=0` → 2, 3 |
| `quadratic_formula` | `(−b±√(b²−4ac))/2a` | T4-T5 |

### Number theory (T2-T4)

| Strategy ID | The move | Example |
|---|---|---|
| `divisibility_2` | Ends in even digit | `Is 374 divisible by 2?` → Yes |
| `divisibility_3` | Digit sum divisible by 3 | `Is 471 divisible by 3?` → Yes |
| `divisibility_5` | Ends in 0 or 5 | |
| `divisibility_9` | Digit sum divisible by 9 | |
| `prime_check_small` | Trial division to √n | `Is 17 prime?` → Yes |
| `gcd_by_factor_pairs` | List factors, take largest common | `gcd(12, 18) = ?` → 6 |
| `lcm_by_multiples` | List multiples, take smallest common | `lcm(6, 8) = ?` → 24 |
| `factorize_to_primes` | Tree decomposition: `60 → 2²·3·5` | `Prime factorize 60.` |

### Exponents / roots (T2-T4)

| Strategy ID | The move | Example |
|---|---|---|
| `square_perfect_recall` | Memorized 1²-12² | `12² = ?` → 144 |
| `cube_small_recall` | Memorized 1³-5³ | `4³ = ?` → 64 |
| `exponent_product_rule` | `aᵐ · aⁿ = aᵐ⁺ⁿ` | `2³·2⁴ = ?` → 2⁷ |
| `exponent_quotient_rule` | `aᵐ/aⁿ = aᵐ⁻ⁿ` | |
| `exponent_power_rule` | `(aᵐ)ⁿ = aᵐⁿ` | |
| `negative_exponent` | `a⁻ⁿ = 1/aⁿ` | T4 |
| `root_perfect_square` | √16, √25, √36 ... | `√81 = ?` → 9 |

### Geometry / measurement (T1-T4)

| Strategy ID | The move | Example |
|---|---|---|
| `rectangle_area` | `l × w` | `5×4 rectangle area?` → 20 |
| `rectangle_perimeter` | `2(l+w)` | `5×4 rectangle perimeter?` → 18 |
| `triangle_area` | `½ × b × h` | |
| `circle_area` | `πr²` | `Circle r=5, area?` → 25π ≈ 78.5 |
| `circle_circumference` | `πd = 2πr` | |
| `pythagorean_3_4_5` | Famous triples: 3-4-5, 5-12-13, 8-15-17 | `Right tri legs 5,12. Hyp?` → 13 |
| `volume_box` | `l×w×h` | |
| `angle_sum_triangle` | Always 180° | |

## Pillar 2 — Vocabulary / concept recognition

These cells answer "What is this thing called?" — exposure builds fluency.

### Shapes (2D)

| Strategy ID | Names taught |
|---|---|
| `polygon_by_side_count` | triangle (3), quadrilateral (4), pentagon (5), hexagon (6), heptagon (7), octagon (8), nonagon (9), decagon (10), dodecagon (12) |
| `triangle_by_sides` | equilateral, isosceles, scalene |
| `triangle_by_angles` | acute, right, obtuse |
| `quadrilateral_types` | square, rectangle, rhombus, parallelogram, trapezoid, kite |
| `regular_vs_irregular` | regular polygon = all sides + all angles equal |

### Shapes (3D)

| Strategy ID | Names taught |
|---|---|
| `solids_basic` | cube, sphere, cylinder, cone, pyramid, prism |
| `regular_polyhedra` | tetrahedron (4), cube (6), octahedron (8), dodecahedron (12), icosahedron (20) — Platonic solids |
| `solid_components` | vertex, edge, face |

### Angles

| Strategy ID | Names taught |
|---|---|
| `angle_types` | acute (<90), right (90), obtuse (90-180), straight (180), reflex (>180) |
| `angle_pair_relationships` | complementary (sum 90), supplementary (sum 180), vertical (across intersection) |
| `parallel_line_angles` | alternate-interior, corresponding, co-interior — T3+ |

### Number categories

| Strategy ID | Names taught |
|---|---|
| `even_odd` | even, odd, parity |
| `prime_composite` | prime, composite, "1 is neither" |
| `figurate_numbers` | square (1,4,9,16...), triangular (1,3,6,10...), perfect (6,28,496...) |
| `integer_rational_real` | natural, whole, integer, rational, irrational, real |
| `irrational_famous` | π, e, √2, φ (golden ratio) — T4-T5 |
| `complex_imaginary` | i = √−1, complex number a+bi — T4-T5 |

### Operations vocabulary

| Strategy ID | Names taught |
|---|---|
| `operation_names_basic` | sum, difference, product, quotient, remainder |
| `division_parts` | dividend, divisor, quotient |
| `factor_multiple` | factor, multiple, common factor, common multiple, GCD/LCM |
| `fraction_parts` | numerator, denominator, mixed number, improper fraction, reciprocal |

### Properties

| Strategy ID | Names taught |
|---|---|
| `property_commutative` | `a+b = b+a` works for + and × |
| `property_associative` | `(a+b)+c = a+(b+c)` |
| `property_distributive` | `a(b+c) = ab+ac` |
| `property_identity` | 0 for +, 1 for × |
| `property_inverse` | additive inverse (−), multiplicative inverse (reciprocal) |

### Geometry vocabulary

| Strategy ID | Names taught |
|---|---|
| `perimeter_area_volume_words` | perimeter (2D edge), area (2D inside), volume (3D inside), surface area |
| `circle_vocabulary` | radius, diameter, circumference, chord, arc, sector, tangent |
| `line_relationships` | parallel, perpendicular, intersecting, skew |
| `congruent_similar` | congruent (same shape AND size), similar (same shape, scaled) |

### Statistics vocabulary

| Strategy ID | Names taught |
|---|---|
| `central_tendency` | mean, median, mode, range |
| `spread_words` | range, variance, standard deviation (T4+), outlier |
| `prob_basic_words` | probability, odds, sample space, event |

### Quantity names (sneaky-useful trivia)

| Strategy ID | Names taught |
|---|---|
| `count_words_old` | dozen (12), score (20), gross (144), baker's dozen (13) |
| `time_periods` | decade (10y), century (100y), millennium (1000y) |
| `metric_prefixes` | kilo (10³), mega (10⁶), giga (10⁹), milli (10⁻³), micro (10⁻⁶) |

## Distractor design — common-error templates

Each strategy has an associated set of "wrong moves" that produce distractors:

**Computation strategy distractors:**
- *Skipped the strategy* — applied a slower naive method and got an off-by-one
- *Half-applied the strategy* — stopped at the bridging step
- *Wrong-direction adjustment* — added when should have subtracted
- *Off-by-one* — counted one too many/few

**Vocabulary distractors:**
- Adjacent-but-wrong concept (e.g., for "rhombus" the distractors are square, parallelogram, trapezoid — all real quadrilaterals)
- One letter / one syllable different (e.g., for "supplementary" use "complementary")
- Almost-right relationship (e.g., for "vertical angles" use "corresponding angles")

## Tier mapping

| Tier | Computation strategies | Vocabulary strategies |
|---|---|---|
| T1 | additive (make-ten, near-doubles), ×1/×2/×5/×10 anchors, doubling/halving, magnitude compare | basic 2D shapes (≤8 sides), even/odd/prime, basic angle types, operation names (sum/difference/product) |
| T2 | compensate, split, ×9, ×11, halve-then-double, fraction common-denom, percent anchors (10/25/50) | quadrilateral types, 3D solids, triangle types, factor/multiple vocab, commutative/associative |
| T3 | isolate-x (1-2 step), divisibility rules, gcd/lcm, exponent rules, rectangle/triangle/circle formulas, percent_flip, ratio_scaling | parallel-line angle pairs, figurate numbers, congruent/similar, central tendency |
| T4 | quadratic factoring (simple), distance-rate-time, work-rate, exponent rules (negative, fractional), Pythagorean triples | irrational famous (π, e, √2), Platonic solids, complex/imaginary intro |
| T5 | quadratic formula, difference of squares, calculus glimpses, advanced word problems | transcendental numbers, formal proof vocabulary |

(`distributive`, `metric_prefixes`, and `quantity_names` moved earlier — they're middle-school content, not advanced.)

## Question generation budget

Per the user request (math = combat = highest-frequency skill), target:

| Tier | Old bank | Current bank | Target (post-strategy) |
|---|---|---|---|
| T1 | 107 | 163 | **600+** (additive + vocab fundamentals) |
| T2 | 104 | 117 | **800+** (most strategies live here) |
| T3 | 145 | 173 | **900+** (algebra basics, divisibility, geometry formulas) |
| T4 | 108 | 156 | **600+** (advanced, word problems) |
| T5 | 74 | 153 | **300+** (calculus glimpses, math wonder) |
| **Total** | **538** | **762** | **~3000-3500** |

Most expansion happens at T1-T3 via the deterministic Python generator (one function per strategy, emits 50-300 questions each). T4-T5 expand modestly via additional LLM agent runs.

## Schema addition

Each math question gets:

```json
{
  "tier": 2,
  "topic_cell": "basic_arithmetic",
  "question": "29 + 47 = ?",
  "answer": "76",
  "choices": ["76", "75", "77", "86"],
  "context": "Round 29 up to 30 to make the addition easy: 30 + 47 = 77. Now subtract the 1 you added: 77 − 1 = 76.",
  "_meta": {
    "strategy": "compensate_addition",
    "strategy_pillar": "computation"
  }
}
```

The game UI ignores `_meta`. Strategy coverage audit just queries the bank for `_meta.strategy`.

## Anti-patterns specific to this taxonomy

- **No "rote drill" without a strategy.** A question like `4 + 7 = ?` with random distractors `11 / 12 / 10 / 13` doesn't teach a move. Either tag it with `make_ten_addition` and use the strategy-derived distractors, or don't ship it.
- **No vocabulary-as-trivia.** "What is the capital of geometry?" — banned. Vocabulary questions must show the concept, not just demand a name. "A 4-sided shape with all sides equal but angles not 90° is called?" — yes. "What is a rhombus?" — no.
- **No "wrong because random."** Every distractor should be the result of a *specific* error someone would make.
