# Math Framework (v2)

The voice + structure rules for the math bank. This document is the
**framework** (the why + voice); see `MATH_TEMPLATES.md` for the
**templates** (the per-tier approved patterns) and
`tools/quizgen/gates/math.py` for the **gates** (the deterministic
checks).

Math is fundamentally different from the wonder subjects (history,
philosophy, cooking, animal, geography, theology, trivia, economics,
science, AI). It is one of the two snappy-rote exceptions named in
`feedback_no_rote_wonder.md` (the other is grammar). The Wonder Pattern
does not apply. Instead math has its own controlling voice rule — §1
below.

Math is also the engine of **combat** in Philosopher's Quest. Combat is
the most-pinged quiz action in the game — a kid playing for an hour
will answer dozens to hundreds of math questions. The bank's job:

1. **Drill mental-math tricks** at age-appropriate levels so the kid
   internalizes shortcuts they can use everywhere.
2. **Expose foundational equations and their NAMES** so a kid sees the
   Pythagorean theorem (named) dozens of times before they hit it in
   8th grade.

The math timer is 16 seconds — the tightest in the game. Stems must be
SNAPPY. Decoration is the enemy.

---

## §1 The Mental-Move Pattern (THE controlling voice rule)

**The most memorable math question makes the kid execute a specific
mental MOVE — and the CONTEXT tells them what move they just made.**

This is math's analog to grammar's Comma-Saves-Lives Pattern. Where
grammar asks "where does the wrong version produce the punchline?",
math asks "what mental shortcut should the kid have used here, and
have we NAMED that shortcut in the context?"

### Hierarchy of math-memorability

Tier 1 of the hierarchy is the highest-priority voice. The bank's
center of gravity should be tiers 1-2 of this hierarchy at T2+; T1 is
pure rote (tier 3 of the hierarchy) and that's correct for T1.

| Hierarchy tier | Type | Example |
|---|---|---|
| **1. TRICK-EXECUTION QUESTIONS** (highest, T2+) | Stem invites a specific mental shortcut; context NAMES the trick. | `25 × 16 = ?` → 400; context: "Halving-and-doubling trick: 25×16 = 50×8 = 100×4 = 400. Halve one number, double the other, keep multiplying until the math is easy." |
| **2. NAMED-EQUATION QUESTIONS** (T2+) | Stem invokes a foundational equation; answer requires applying it; context names the equation. | "A right triangle has legs 3 and 4. Find the hypotenuse." → 5; context: "Pythagorean theorem: a² + b² = c². 3² + 4² = 9 + 16 = 25; √25 = 5. This is the famous 3-4-5 right triangle." |
| **3. ROTE RECALL** (T1 mainly; valid at all tiers for foundational facts) | Pure recall — times tables, perfect squares, π ≈ 3.14, common F/D/P conversions. | `7 × 8 = ?` → 56 |
| **4. PURE COMPUTATION WITHOUT A NAMED TRICK** (lowest, valid only when nothing else applies) | Brute calculation. Used sparingly; if a question is just "compute 4738 + 2196" with no shortcut to teach, it's not earning its place. | `4738 + 2196 = ?` |

All four are **valid**. None are banned (math IS exempt from the
anti-rote gate per `moral_vision.md`). But the BANK's center of
gravity at T2+ must be tiers 1-2 — that's where the bank stops being a
flashcard and starts teaching mental moves.

### Three-question test (mirrors Wonder Pattern's test)

For each math question, ask:

1. **The Trick Test** (T2+ only) — does the context NAME a trick or
   equation by name? "Halving-and-doubling", "Pythagorean theorem",
   "Make-a-ten", "FOIL", "Difference of squares", "Quadratic formula",
   "Distributive property", "Complement-to-100" are all named moves.
   If the context just states the answer ("200 is the sum"), the
   question is not earning its T2+ slot.
2. **The Speed Test** — can a kid in the target grade compute this
   answer in 16 seconds with the named trick? If the stem is over ~80
   chars or the computation requires paper, the question fails combat.
3. **The Reuse Test** — would the kid use this trick somewhere else in
   life (tipping at restaurants, splitting a check, estimating a sale
   price, finding a missing measurement)? If yes, the trick earns its
   tier.

### Worked examples (the canonical mental-move corpus)

| Move | Example stem | Context teaches |
|---|---|---|
| Times table rote (T1) | `7 × 8 = ?` | "Times tables — memorize these so combat math is automatic. 7 × 8 = 56." |
| Make-a-ten (T1) | `8 + 5 = ?` | "Make-a-ten trick: 8 + 2 = 10, then 10 + 3 = 13. Bridge through 10 to add fast." |
| Complement-to-100 (T2) | `75 + 25 = ?` | "Complement-to-100: numbers ending in 25 and 75 pair up; 25+75 = 100. Look for these pairs to add fast." |
| Halving-and-doubling (T2) | `25 × 16 = ?` | "Halving-and-doubling: 25×16 = 50×8 = 100×4 = 400. Halve one factor, double the other, repeat until one factor is round." |
| Squares ending in 5 (T2) | `35² = ?` | "Square-ending-in-5 shortcut: take the tens digit times the next integer (3×4 = 12), then append 25. So 35² = 1225." |
| 10%-then-double (T3) | `20% of 45 = ?` | "Tip trick: 10% of 45 is 4.5 (move decimal left), so 20% = 2 × 4.5 = 9." |
| Add-subtract-the-same (T3) | `98 + 47 = ?` | "Round-to-100 trick: add 2 to 98 → 100; subtract 2 from 47 → 45; 100 + 45 = 145." |
| Difference of squares (T3) | `19 × 21 = ?` | "Difference-of-squares trick: 19 × 21 = (20−1)(20+1) = 20² − 1² = 400 − 1 = 399." |
| Distributive (T2/T3) | `15 × 12 = ?` | "Distributive property: 15 × 12 = 15 × 10 + 15 × 2 = 150 + 30 = 180." |
| Pythagorean triple (T4) | "A right triangle has legs 5 and 12. Find the hypotenuse." | "Pythagorean theorem: a² + b² = c². The 5-12-13 triangle is one of four common Pythagorean triples (3-4-5, 5-12-13, 8-15-17, 7-24-25) worth memorizing." |
| Slope formula (T4) | "Find the slope through (1, 3) and (4, 9)." | "Slope formula: m = (y₂−y₁)/(x₂−x₁) = (9−3)/(4−1) = 6/3 = 2. Slope = rise over run." |
| FOIL (T5) | "Expand (x + 3)(x + 5)." | "FOIL: First × First + Outer + Inner + Last × Last. x·x + x·5 + 3·x + 3·5 = x² + 8x + 15." |
| Quadratic formula (T5) | "Solve x² + 5x + 6 = 0 by factoring." | "Trinomial factoring: find two numbers that multiply to 6 and add to 5. That's 2 and 3, so (x+2)(x+3) = 0; x = −2 or x = −3. (The quadratic formula x = (−b ± √(b²−4ac))/2a also works.)" |

### What this REPLACES (do not import from wonder subjects)

- ❌ NAMED THINGS > VIVID ACTIONS > etc. (Wonder Pattern hierarchy)
- ❌ Drama-Available Rule, Dinner Test (in the wonder sense)
- ❌ Behind-the-scenes wonder, retellability
- ❌ Singular-cool-fact-is-answer
- ❌ Story-in-stem (math stems should be MINIMAL, not narrative)

---

## §2 Grade-anchored tier mapping

Tiers map to US grade standards. T5 caps at 9th grade (Algebra 1). The
bank does NOT teach Algebra 2, pre-calc, trig functions, logs, or
calculus.

| Tier | Grade band | What's taught |
|---|---|---|
| T1 | Pre-K → 5th | Pure rote: times tables 1-12, addition/subtraction within 20, doubles, fact families, skip counting, number bonds |
| T2 | 6th grade | Multi-digit ops, mental tricks (complement-100, halving-doubling, distributive, squares-end-in-5, ×9/×11/×5 shortcuts), fraction ops, common F/D/P conversions, percent of a number, PEMDAS, GCF/LCM, divisibility rules, integers intro, coordinate plane, mean/median/mode |
| T3 | 7th grade | Proportions, scale, signed rational ops, sign rules, percent shortcuts (tips, 15%), combining like terms, distributing through parens, two-step equations & inequalities, probability basics, compound probability, simple interest |
| T4 | 8th grade | Slope, slope-intercept, systems (graph/substitute/eliminate), exponent rules, scientific notation, square root simplification, Pythagorean theorem, distance/midpoint, transformations, similarity, volume (cylinder/cone/sphere), function notation |
| T5 | 9th grade (Algebra 1) | Polynomial ops, FOIL, factoring (difference of squares, trinomials, GCF, grouping, perfect squares), quadratic by factor/roots/formula, discriminant, vertex form, rational expressions, arithmetic & geometric sequences, compound interest formula |

### What is NOT taught (above 9th grade)

The math bank explicitly does NOT include:

- ❌ Logarithms, natural log, change-of-base
- ❌ Trigonometric functions, SOH CAH TOA, unit circle, identities
- ❌ Calculus (limits, derivatives, integrals)
- ❌ Z-scores, normal distribution, statistical inference
- ❌ Imaginary/complex numbers (briefly mentioned via quadratic
  discriminant only)
- ❌ Conic sections (parabola is OK at T5 as quadratic graph; ellipse,
  hyperbola, circle equations OUT)
- ❌ Matrices, vectors
- ❌ Set theory beyond informal union/intersection at T3
- ❌ Gauss sum n(n+1)/2 (too sophisticated for 9th)
- ❌ Euler constants e, φ; only π is named (T3 onward)

---

## §3 The 16-second combat constraint

Math is the combat quiz. Combat is chain-mode: build a combo until a
wrong answer. The 16-second per-question timer at WIS 10 is the
**hardest cap in the game** (per `project_subject_timer.md`).

This drives:

- **Stem length cap by tier** (see `MATH_TEMPLATES.md` §2):
  - T1: ≤ 40 chars (numerical only: `7 × 8 = ?`)
  - T2: ≤ 90 chars
  - T3: ≤ 140 chars (may include 1 short setup sentence)
  - T4: ≤ 200 chars
  - T5: ≤ 250 chars
- **Answer length**: numerical or short symbolic; almost never a
  sentence
- **No narrative scenery in stems** — no "Maria buys 3 apples"
  word-problem theater unless the word-problem IS the trick (T3-T5
  setups are OK but kept tight)
- **No distracting context inside the stem** — the trick-name lives in
  CONTEXT, not stem

If the kid can't read-and-compute in ≤ 12 seconds (leaving 4 for
answer selection), the question fails the bank.

---

## §4 Where the trick lives: CONTEXT is the teacher

Per `feedback_lift_discovered_rules.md` §14 (story-in-stem): live
learning happens at stem + answer ONLY. Context is shown only on
wrong-answer or end-game review.

For MATH this means: **the stem invites the trick, but the trick is
NAMED in context for review.** A kid who answers correctly doesn't
need the explanation — they did the move. A kid who answered wrong
sees context that:

1. NAMES the trick / equation by its proper name ("Halving-and-doubling",
   "FOIL", "Pythagorean theorem", "Quadratic formula")
2. EXECUTES the move step-by-step
3. CONNECTS to where the trick is used in life (tipping, splitting a
   bill, estimating a sale)

### Anti-pattern: context that just states the answer

❌ "The answer is 56."
❌ "200 is the sum."
❌ "5² = 25."

These context fields are FLASH-CARD ANSWERS, not teaching. The
context-coverage gate hard-rejects T2+ questions whose context is just
a restatement of the answer.

### Pattern: context that names + teaches the move

✅ "Times-tables rote. 7 × 8 = 56. Memorize the table — automatic
multiplication is the foundation of mental math."

✅ "Complement-to-100 trick: numbers ending in 25 and 75 sum to 100.
75 + 125 = 75 + 25 + 100 = 100 + 100 = 200. Watch for these pairs."

✅ "Pythagorean theorem: a² + b² = c². With a = 3 and b = 4, c² = 9 +
16 = 25, so c = 5. The 3-4-5 right triangle is the most famous
Pythagorean triple."

---

## §5 Foundational equations corpus

The bank must NAME these equations repeatedly. A 7th grader who has
played the game should have seen "Pythagorean theorem" in context 30+
times before they meet it in 8th grade class.

### T2-named equations

| Equation | Stem example | Tier first appears |
|---|---|---|
| A = l × w | "Rectangle 4 × 7. Area?" | T2 |
| P = 2(l + w) | "Rectangle 3 × 5. Perimeter?" | T2 |
| V = l × w × h | "Box 2 × 3 × 4. Volume?" | T2 |
| A = ½ × b × h | "Triangle base 6, height 4. Area?" | T2 |

### T3-named equations

| Equation | Stem example |
|---|---|
| A = πr² (circle area) | "Circle radius 3. Area in terms of π?" |
| C = 2πr (circle circumference) | "Circle radius 5. Circumference in terms of π?" |
| V = πr²h (cylinder) | "Cylinder radius 2, height 5. Volume in terms of π?" |
| A = bh (parallelogram) | "Parallelogram base 8, height 3. Area?" |
| A = ½(b₁+b₂)h (trapezoid) | "Trapezoid bases 4 and 6, height 5. Area?" |
| F = (9/5)C + 32 (temperature) | "Convert 100°C to Fahrenheit." |
| d = rt (distance) | "60 mph for 3 hours. Distance?" |
| I = Prt (simple interest) | "$1000 at 5% for 2 years. Simple interest?" |

### T4-named equations

| Equation | Stem example |
|---|---|
| a² + b² = c² (Pythagorean theorem) | "Right triangle legs 5 and 12. Hypotenuse?" |
| y = mx + b (slope-intercept form) | "Slope 2, y-intercept 3. Equation of line?" |
| m = (y₂−y₁)/(x₂−x₁) (slope formula) | "Slope through (1,3) and (4,9)?" |
| d = √((x₂−x₁)² + (y₂−y₁)²) (distance formula) | "Distance from (0,0) to (3,4)?" |
| V = (4/3)πr³ (sphere volume) | "Sphere radius 3. Volume in terms of π?" |
| V = ⅓πr²h (cone volume) | "Cone radius 2, height 6. Volume in terms of π?" |
| Exponent rules: x^a · x^b = x^(a+b), etc. | "Simplify x³ · x⁵" |

### T5-named equations

| Equation | Stem example |
|---|---|
| x = (−b ± √(b²−4ac))/2a (quadratic formula) | "Solve x² + 5x + 6 = 0 by formula" |
| b² − 4ac (discriminant) | "Discriminant of x² + 3x + 5?" |
| a² − b² = (a+b)(a−b) (difference of squares) | "Factor x² − 25" |
| (a+b)² = a² + 2ab + b² (perfect square trinomial) | "Expand (x+4)²" |
| FOIL: (a+b)(c+d) = ac + ad + bc + bd | "Expand (x+3)(x+5)" |
| aₙ = a₁ + (n−1)d (arithmetic sequence) | "10th term of 3, 7, 11, 15, ...?" |
| aₙ = a₁ · r^(n−1) (geometric sequence) | "5th term of 2, 6, 18, 54, ...?" |
| A = P(1 + r/n)^(nt) (compound interest) | "$1000 at 6% compounded yearly for 3 years?" |

---

## §6 Mental-math tricks corpus

| Trick name | Where it lives | Example |
|---|---|---|
| Times tables (rote) | T1 | 7 × 8 = 56 |
| Doubles | T1 | 6 + 6 = 12 |
| Halves | T1 | Half of 14 = 7 |
| Make-a-ten / bridging-ten | T1 | 8 + 5 = 8 + 2 + 3 = 13 |
| Counting on | T1 | 9 + 4: start at 9, count up 4 → 10, 11, 12, 13 |
| Skip counting | T1 | 5, 10, 15, 20, 25 |
| Fact families | T1 | 4 + 3 = 7, so 7 − 3 = 4 |
| Number bonds to 10 | T1 | Pairs summing to 10: 1+9, 2+8, 3+7, 4+6, 5+5 |
| Complement-to-10 / 100 | T2 | 25 + 75 = 100; 35 + 65 = 100 |
| Add-by-tens-then-ones | T2 | 37 + 25 = 37 + 20 + 5 = 62 |
| Distributive | T2 | 15 × 12 = 15 × 10 + 15 × 2 = 180 |
| Halving-and-doubling | T2 | 25 × 16 = 50 × 8 = 100 × 4 = 400 |
| ×10/100/1000 shifts | T2 | 47 × 100 = 4700 |
| ×5 = halve and ×10 | T2 | 18 × 5 = 90 = (18/2) × 10 |
| ×9 = ×10 minus the number | T2 | 9 × 7 = 70 − 7 = 63 |
| ×11 two-digit (split + insert) | T2 | 11 × 23: insert 2+3=5 between 2 and 3 → 253 |
| Square-ending-in-5 | T2 | 35² = (3×4)25 = 1225 |
| Rounding to estimate | T2 | 49 + 31 ≈ 50 + 30 = 80 |
| Common F/D/P conversions | T2/T3 | 1/4 = 0.25 = 25%; 1/8 = 0.125 = 12.5% |
| 10% trick (decimal shift) | T2/T3 | 10% of 45 = 4.5 |
| 20% = 10% then double | T3 | 20% of 45 = 9 |
| 15% = 10% + half-of-10% | T3 | 15% of 45 = 4.5 + 2.25 = 6.75 |
| Sign rules | T3 | (−)(−) = + |
| Add-subtract-the-same | T3 | 98 + 47 = 100 + 45 = 145 |
| Difference-of-squares mental | T3 | 19 × 21 = 20² − 1 = 399 |
| Near-50 squaring | T3 | 47² = (50−3)² = 2500 − 300 + 9 = 2209 |
| Cross-multiplication | T3 | a/b = c/d ⟹ ad = bc |
| Divisibility rules | T3 | ÷3: digit sum divisible by 3 |
| Combining like terms | T3 | 3x + 5x = 8x |
| Two-step equation | T3 | 3x + 5 = 20 ⟹ x = 5 |
| Solve linear equation | T4 | 4x − 7 = 13 ⟹ x = 5 |
| Recognize perfect squares 1²-20² | T4 | 169 = 13² |
| Pythagorean triples | T4 | 3-4-5, 5-12-13, 8-15-17, 7-24-25 |
| Slope from two points | T4 | m = (y₂−y₁)/(x₂−x₁) |
| Slope-intercept conversion | T4 | y = 2x + 3 has slope 2, intercept 3 |
| Square-root simplification | T4 | √48 = √(16·3) = 4√3 |
| Substitute into formula | T4 | A = πr² with r = 3 ⟹ 9π |
| FOIL | T5 | (x+2)(x+3) = x² + 5x + 6 |
| Difference-of-squares factor | T5 | x² − 9 = (x+3)(x−3) |
| Trinomial factor (find-two-nums) | T5 | x² + 7x + 12 = (x+3)(x+4) |
| Perfect-square recognition | T5 | x² + 6x + 9 = (x+3)² |
| Solve quadratic by factoring | T5 | x² − 5x + 6 = 0 ⟹ x = 2 or 3 |
| Quadratic formula | T5 | x² + 4x + 1 = 0 |
| Arithmetic-sequence nth term | T5 | aₙ = a₁ + (n−1)d |
| Geometric-sequence nth term | T5 | aₙ = a₁ · r^(n−1) |
| Compound interest | T5 | A = P(1 + r/n)^(nt) |

---

## §7 What math SKIPS from the gate pipeline

Math is exempt from many gates that apply to wonder subjects:

- **anti_rote** — math IS rote; that's the point (per `moral_vision.md`)
- **answer_collision** — many math answers are common numbers (e.g.,
  the answer "5" appears many times); collision-by-value is fine
- **wonder_bias_check**, **drama_available**, **dinner_test** — N/A
- **no_verdict_on_contested** — math doesn't have contested topics
- **place_anchor_check**, **scenario_anchored_correct** — N/A
- **scenery / decoration / parens_skim_tell** — math doesn't decorate
- **story_in_stem** — math stems are MINIMAL by design (the trick
  lives in context, not stem; see §4)
- **§15 weasel closers** — math stems are numeric expressions, not
  questions about meaning

Math ADDS its own gates (see `tools/quizgen/gates/math.py`):

- **gate_no_placeholder_strings** (HARD) — bans literal "NA0", "NA1"
  generation artifacts in choices
- **gate_trick_context_required** (HARD T2+) — context must name a
  trick or equation, not just restate the answer
- **gate_named_equation_when_applicable** (SOFT) — when a question
  uses a foundational equation, the equation should be NAMED in
  context
- **gate_stem_length_combat** (HARD) — per-tier stem length cap (the
  16s timer)
- **gate_magnitude_leak** (HARD) — the correct numerical answer must
  not be uniquely large or uniquely small versus distractors (the
  "biggest is always right" anti-pattern)
- **gate_tier_concept_appropriate** (HARD) — no concepts above the
  tier's grade band (no logs at T4, no calculus ever, etc.)

---

## §8 Distractor design (per pillar)

Numerical-answer distractors are NOT decorative. They should reflect
the COMMON STUDENT ERROR for the trick being taught. A good distractor
is a wrong answer a kid would actually arrive at.

| Trick | Common errors → distractors |
|---|---|
| Make-a-ten | Forgot to carry (8 + 5 distractor 12 instead of 13) |
| Times tables | Adjacent fact (7 × 8 distractor 54 instead of 56; 7 × 8 → 49 = 7² confusion) |
| Complement-to-100 | Off-by-1 in complement |
| Halving-and-doubling | Halved both / doubled both |
| 10% trick | Moved decimal wrong direction |
| Sign rules | Forgot to flip sign |
| Pythagorean | Forgot to take square root; added instead of squared first |
| FOIL | Missed a cross term; forgot to add like terms |
| Slope | Reversed numerator/denominator |
| Quadratic | Wrong sign on discriminant; off-by-1 |

A magnitude-leak distractor (the correct is 56, distractors are 8, 12,
23) fails the magnitude-leak gate. Distractors should be the SAME
order of magnitude as the answer.

---

## §9 Pillar structure

Six pillars (parallels other rebuilds). Each pillar maps a domain
band; tier-density is uneven by design.

| Pillar | Tier weight | What it teaches |
|---|---|---|
| **P1 — Arithmetic foundations** | T1 heavy, some T2 | Times tables, doubles/halves, make-a-ten, counting on, skip counting, fact families, even/odd, number bonds, two-digit + carry/borrow, single-digit ÷ |
| **P2 — Mental math tricks** | T2-T3 heavy | Complement-to-100, halving-doubling, distributive, ×9/×11/×5 shortcuts, squares-end-in-5, add-subtract-the-same, difference-of-squares mental, near-50 squaring, rounding-to-estimate |
| **P3 — Fractions, decimals, percents, signed** | T2-T3 heavy | Common F/D/P conversions, percent of a number, 10/15/20% tips, decimal ops, sign rules, absolute value, signed rational ops, proportions, cross-multiplication |
| **P4 — Algebra & equations** | T3-T5 heavy | Combining like terms, distributing, two-step equations, inequalities, slope, slope-intercept, systems, exponent rules, polynomial ops, FOIL, factoring, quadratic |
| **P5 — Geometry, measurement, formulas** | T2-T5 spread | Area/perimeter/volume formulas, Pythagorean theorem and triples, distance formula, midpoint, transformations, similarity, special triangles (angle sums), substitute-into-formula |
| **P6 — Probability, stats & financial** | T3-T5 spread | Probability basics, compound probability, independent events, mean/median/mode/range, simple interest, compound interest, arithmetic + geometric sequences |

---

## §10 Target bank size and distribution

| Tier | Target count | Pillar weights (rough) |
|---|---|---|
| T1 | 500 | P1 480, P2 20 |
| T2 | 600 | P1 150, P2 200, P3 150, P5 100 |
| T3 | 550 | P2 100, P3 250, P4 100, P5 50, P6 50 |
| T4 | 450 | P4 200, P5 200, P6 50 |
| T5 | 400 | P4 200, P5 50, P6 150 |
| **Total** | **~2,500** | |

T1 is heavily rote — each times-table fact (3×4, 4×3, etc.) appears
~5 times to drill it.

---

## §11 What math IS NOT

To prevent drift in agent work:

- ❌ NOT a wonder bank — no stories, no cool facts, no canonical scenes
- ❌ NOT a textbook — context teaches the move, not the whole chapter
- ❌ NOT a word-problem bank by default — short numerical stems
  dominate; word problems appear for T3+ when they're the natural way
  to teach a trick (proportions, percent-of, distance-rate-time)
- ❌ NOT above 9th grade — no logs, no trig functions, no calculus
- ❌ NOT a flashcard — T2+ must teach a trick in context, not just
  state the answer
- ❌ NOT decorated — no fancy formatting, no fluff in stems; combat
  timer demands SNAP

The math bank is a mental-math gym disguised as a roguelike combat
engine. Every fight makes the kid faster at the moves they'll use for
life.
