# Math Templates (v2)

Per-tier approved stem patterns, choice-shape conventions, length caps,
and anti-patterns. The framework (`MATH_FRAMEWORK.md`) explains the
WHY; this document gives the WHAT.

**Authoring rule**: every new math question matches an approved
template AND the Mental-Move Pattern (`MATH_FRAMEWORK.md` §1).

---

## §1 Stem-vs-context discipline

Per `MATH_FRAMEWORK.md` §4:

- **Stem**: the math problem itself, MINIMAL. The kid reads stem and
  computes in ≤ 12 seconds.
- **Answer**: the numerical or short symbolic result.
- **Context**: NAMES the trick or equation, EXECUTES the move
  step-by-step, CONNECTS to a real-life use when applicable. Shown
  only on wrong-answer or end-game review.

The trick lives in CONTEXT. The stem just poses the problem.

---

## §2 Length caps (driven by 16s combat timer)

| Tier | Stem char cap | Total record cap | Notes |
|---|---|---|---|
| T1 | 40 | 280 | Numeric expressions only: `7 × 8 = ?` |
| T2 | 90 | 400 | One-sentence setups OK |
| T3 | 140 | 550 | Multi-sentence stems begin (proportions, percent) |
| T4 | 200 | 750 | Word problems with multi-clause setups |
| T5 | 250 | 900 | Polynomial expansions can run long |

Length caps are enforced by `tools/quizgen/deterministic/length_budget.py`
via `SUBJECT_TIER_BUDGETS["math"]`.

---

## §3 Approved stem patterns by tier

### T1 patterns (Pre-K → 5th grade, pure rote)

| Pattern | Example stem | Notes |
|---|---|---|
| Bare-numeric times tables | `7 × 8 = ?` | Drill |
| Bare-numeric addition within 20 | `8 + 5 = ?` | Drill |
| Bare-numeric subtraction within 20 | `13 − 5 = ?` | Drill |
| Doubles | `6 + 6 = ?` | Special-case addition |
| Halves | `Half of 14 = ?` | Maps to ÷2 |
| Skip-count next | `5, 10, 15, ? ` | Pattern recognition |
| Number bonds to 10 | `7 + ? = 10` | Bond pairs |
| Fact-family pair | `If 4 + 3 = 7, then 7 − 3 = ?` | Inverse-op |
| Missing addend | `5 + ? = 12` | Subtraction as missing addend |
| Even/odd recognition | `Is 7 even or odd?` | Number-sense (limited) |

### T2 patterns (6th grade)

| Pattern | Example stem | Notes |
|---|---|---|
| Multi-digit addition/subtraction | `345 + 178 = ?` | Carry/borrow |
| Multi-digit multiplication | `24 × 13 = ?` | Distributive trick in context |
| Long division | `156 ÷ 12 = ?` | |
| Complement-to-100 | `75 + 125 = ?` | Trick in context |
| Halving-and-doubling | `25 × 16 = ?` | Trick in context |
| ×9 shortcut | `9 × 7 = ?` | ×10 minus number trick in context |
| ×11 trick | `11 × 23 = ?` | Insert-digit-sum trick in context |
| ×5 shortcut | `18 × 5 = ?` | Halve-then-×10 trick in context |
| Square ending in 5 | `35² = ?` | Tens-times-next-25-append trick in context |
| Distributive | `15 × 12 = ?` | Distributive trick in context |
| Fraction add/subtract | `1/3 + 1/4 = ?` | Common denominator in context |
| Fraction × | `2/3 × 3/4 = ?` | Multiply tops, multiply bottoms |
| Fraction ÷ | `1/2 ÷ 1/4 = ?` | Invert and multiply in context |
| F/D/P conversion | `1/4 as a percent = ?` | Common-conversion table in context |
| Percent of a number | `10% of 45 = ?` | "of" means × in context |
| 10% shortcut | `10% of 270 = ?` | Decimal-shift trick in context |
| PEMDAS basics | `3 + 4 × 2 = ?` | Order-of-operations rule in context |
| Rectangle area/perimeter | `Rectangle 4 × 7. Area?` | A = lw named in context |
| Rectangular prism volume | `Box 2 × 3 × 4. Volume?` | V = lwh named in context |
| Triangle area | `Triangle base 6, height 4. Area?` | A = ½bh named in context |
| GCF / LCM | `GCF of 12 and 18?` | Prime-factor method in context |
| Divisibility check | `Is 234 divisible by 6?` | Rules in context |
| Mean / median / mode | `Mean of 3, 5, 7, 9?` | Definitions in context |
| Negative-number basics | `−3 + 5 = ?` | Number-line model in context |
| Absolute value | `|−7| = ?` | Distance-from-zero in context |

### T3 patterns (7th grade)

| Pattern | Example stem | Notes |
|---|---|---|
| Proportion solve | `If 3/x = 6/8, find x.` | Cross-multiply in context |
| Scale-factor | `Map: 1 cm = 50 km. Distance for 4 cm?` | Setup OK |
| Signed-rational ops | `−2/3 + 5/6 = ?` | Sign rules + common denom in context |
| Tip math (20%) | `20% tip on $35?` | 10%-then-double in context |
| Tip math (15%) | `15% tip on $40?` | 10%-plus-half in context |
| Percent change | `From 50 to 65, percent increase?` | Formula in context |
| Add-subtract-the-same | `98 + 47 = ?` | Round-to-100 trick in context |
| Diff-of-squares mental | `19 × 21 = ?` | Difference-of-squares trick in context |
| Near-50 squaring | `47² = ?` | (50−3)² expansion in context |
| Combining like terms | `Simplify 3x + 5 − x + 2` | |
| Distributing through parens | `Expand 3(x + 4)` | Distributive property in context |
| Two-step equation | `Solve 3x + 5 = 20` | Inverse-ops in context |
| Two-step inequality | `Solve 2x − 3 > 7` | Flip-sign rule in context |
| Circle area | `Circle radius 3. Area in terms of π?` | A = πr² named in context |
| Circle circumference | `Circle radius 5. Circumference?` | C = 2πr named |
| Parallelogram area | `Parallelogram base 8, height 3. Area?` | A = bh named |
| Trapezoid area | `Trapezoid bases 4 and 6, height 5. Area?` | A = ½(b₁+b₂)h named |
| Cylinder volume | `Cylinder r=2, h=5. Volume?` | V = πr²h named |
| Temp conversion | `100°C in F?` | F = (9/5)C + 32 named |
| Distance / rate / time | `60 mph for 3 hours. Distance?` | d = rt named |
| Simple interest | `$1000 at 5% for 2 years.` | I = Prt named |
| Probability basics | `Roll a die. P(rolling 4)?` | Favorable/total in context |
| Compound probability | `Roll 2 dice. P(both 6)?` | Independent × together in context |

### T4 patterns (8th grade)

| Pattern | Example stem | Notes |
|---|---|---|
| Solve linear | `Solve 4x − 7 = 13` | |
| Slope from points | `Slope through (1, 3) and (4, 9)?` | m = (y₂−y₁)/(x₂−x₁) named in context |
| Slope-intercept | `Slope 2, y-intercept 3. Equation?` | y = mx + b named in context |
| System by substitution | `y = 2x + 1, y = x + 3. Find (x, y).` | |
| System by elimination | `2x + y = 7, x − y = 2. Find x.` | |
| Exponent rules | `Simplify x³ · x⁵` | x^a · x^b = x^(a+b) named in context |
| Scientific notation | `Write 4,500,000 in scientific notation` | |
| Square root simplify | `Simplify √48` | √(perfect × not-perfect) named in context |
| Pythagorean | `Right triangle legs 5 and 12. Hypotenuse?` | a² + b² = c² named in context |
| Pythagorean triple recognition | `Triangle 8-15-?  (right triangle)` | Triples 3-4-5, 5-12-13, 8-15-17, 7-24-25 in context |
| Distance formula | `Distance from (0,0) to (3,4)?` | Distance formula named in context |
| Midpoint formula | `Midpoint of (1,2) and (5,8)?` | Midpoint formula named in context |
| Triangle angle sum | `Triangle has angles 50° and 70°. Third angle?` | Sum-180 in context |
| Cylinder/cone/sphere volume | `Sphere radius 3. Volume in terms of π?` | V = (4/3)πr³ named in context |
| Similarity | `Triangle sides 3-4-5, similar triangle has shortest side 9. Other sides?` | Scale-factor in context |
| Transformation | `Reflect (3, 4) over y-axis. New point?` | |
| Function notation | `f(x) = 2x + 3. Find f(5).` | f notation in context |
| Perfect squares 1-15² | `√169 = ?` | Recognition |

### T5 patterns (9th grade, Algebra 1 cap)

| Pattern | Example stem | Notes |
|---|---|---|
| Polynomial add/subtract | `(2x² + 3x − 1) + (x² − 4x + 5)` | |
| Polynomial multiply | `(x + 2)(x² − 3x + 1)` | Distribute each term |
| FOIL | `Expand (x + 3)(x + 5)` | FOIL named in context |
| Difference-of-squares factor | `Factor x² − 25` | Difference-of-squares formula named |
| Trinomial factor | `Factor x² + 7x + 12` | Find-two-nums method in context |
| Perfect-square trinomial | `Factor x² + 6x + 9` | (a+b)² pattern named |
| Factor by grouping | `Factor x³ + 2x² + 3x + 6` | |
| Solve quadratic by factor | `Solve x² − 5x + 6 = 0` | |
| Solve quadratic by sqrt | `Solve x² = 49` | |
| Quadratic formula | `Solve x² + 4x + 1 = 0` | Quadratic formula named in context |
| Discriminant | `Discriminant of x² + 3x + 5? (# real solutions?)` | b² − 4ac named |
| Vertex form | `Vertex of y = (x − 2)² + 3?` | Vertex form named |
| Arithmetic sequence nth term | `10th term of 3, 7, 11, 15, ...?` | aₙ = a₁ + (n−1)d named |
| Geometric sequence nth term | `5th term of 2, 6, 18, 54, ...?` | aₙ = a₁ · r^(n−1) named |
| Compound interest | `$1000 at 6% compounded yearly for 3 years?` | A = P(1+r/n)^(nt) named in context |
| Rational expression simplify | `Simplify (x² − 4)/(x + 2)` | Factor & cancel |
| Function eval | `f(x) = x² + 3x. Find f(−2).` | |
| Function domain | `Domain of f(x) = √(x − 4)?` | |

---

## §4 Choice-shape conventions

### Numerical answers (T1-T4 dominant)

- All 4 choices are numbers (integers, decimals, fractions, π-form)
- Distractors reflect COMMON STUDENT ERRORS for the trick being
  taught (see `MATH_FRAMEWORK.md` §8)
- Distractors are SAME ORDER OF MAGNITUDE as the answer (no
  magnitude-leak)
- Acceptable form-variation: `2.5`, `2 1/2`, `5/2` are equivalent;
  pick one form for both answer and distractors per question
- π in answers: `9π`, `3π/2` — keep symbolic form consistent across
  choices

### Symbolic answers (T5 algebra)

- All 4 choices are polynomial/algebraic expressions
- Distractors reflect FOIL errors, sign errors, off-by-one in
  factoring, swapped-factor errors
- Length-parity matters: factor `(x+3)(x+4)` should not be the
  shortest choice if distractors are 3× longer

### Multi-step answer text (rare T4-T5)

- Sometimes the answer is "x = 3 or x = −2" — both roots
- Format consistently: "x = 3 or x = −2", not mix of inequality
  notation

---

## §5 Context-field discipline (the teaching layer)

T2+ context MUST:

1. **Name** the trick or equation by name. ("Halving-and-doubling",
   "Pythagorean theorem", "FOIL", "Complement-to-100",
   "Distributive property", "Quadratic formula", "Distance formula".)
2. **Execute** the move step-by-step.
3. **Connect** to a real-life use when applicable.

### Anti-pattern: bare-answer context

❌ "The answer is 200." → fails `gate_trick_context_required`
❌ "200 is correct." → fails
❌ "Sum: 200." → fails
❌ "Multiply: 24." → fails

### Good context for the same question

✅ "Complement-to-100 trick. Numbers ending in 25 and 75 pair up:
25 + 75 = 100. So 75 + 125 = 75 + 25 + 100 = 100 + 100 = 200. Watch
for these pairs when adding."

✅ "Distributive property: 15 × 12 = 15 × (10 + 2) = 15 × 10 + 15 × 2
= 150 + 30 = 180. Break one factor into easy pieces and add."

✅ "Pythagorean theorem: a² + b² = c². With a = 5 and b = 12,
c² = 25 + 144 = 169, so c = 13. The 5-12-13 triangle is one of four
common Pythagorean triples worth memorizing: 3-4-5, 5-12-13, 8-15-17,
7-24-25."

### T1 context (rote layer)

T1 context can be SHORTER. It doesn't need to teach a trick — it
teaches the FACT itself.

✅ T1: "Times table fact: 7 × 8 = 56. Memorize the multiplication
table — automatic recall is the foundation of all mental math."

---

## §6 Anti-patterns (hard-rejected by gates)

### Placeholder-string artifacts (`gate_no_placeholder_strings`)

❌ Distractor reading "NA0" or "NA1" → bulk-gen scaffold leak; always
broken.

### Bare-answer context at T2+ (`gate_trick_context_required`)

❌ Context that just restates the answer. T2+ must teach the move.

### Stem over-length for combat (`gate_stem_length_combat`)

❌ T1 stem > 40 chars. ❌ T2 > 90 chars. ❌ T3 > 140 chars. ❌ T4 > 200
chars. ❌ T5 > 250 chars.

### Magnitude-leak (`gate_magnitude_leak`)

❌ Answer = 56, distractors = 8, 12, 23 (correct is uniquely the
biggest). Distractors must be same order of magnitude.

### Above-grade-band concepts (`gate_tier_concept_appropriate`)

❌ Logarithms at any tier
❌ SOH CAH TOA / trig functions
❌ Calculus (limits, derivatives, integrals)
❌ Statistical inference (Z-scores beyond brief recognition)
❌ Imaginary numbers (i, complex)
❌ Matrices, vectors

### Word-problem theater without a trick

❌ "Maria has 4 apples. She gives 1 to Tom, 1 to Sue, and eats 1.
How many does she have?" — not teaching a trick; just narrative
flashcard. Use the bare `4 − 3 = ?` if you just want subtraction.

### Decoration in stem

❌ "(In simplest form)" parenthetical that only appears on the
correct answer
❌ "(±)" sign hints only on correct
❌ Unit decoration only on the correct (`5 cm` vs `5`, `5`, `5`)

---

## §7 What this REPLACES

Do not import wonder-subject conventions:

- ❌ Story-in-stem (math stems are MINIMAL)
- ❌ Wonder Pattern hierarchy
- ❌ Drama-Available Rule
- ❌ Singular-cool-fact-is-answer
- ❌ Behind-the-scenes wonder
- ❌ Named-character scenery (no "Maria", "Tom" except as briefest
  T3+ word-problem necessity)
- ❌ Decoration parens skim-tells
- ❌ §15 weasel closers (math stems aren't questions about meaning)
