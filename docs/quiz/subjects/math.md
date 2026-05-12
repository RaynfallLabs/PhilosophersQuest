---
version: 1
date: 2026-05-11
subject: math
in_game_action: combat (chain mode)
style_verdict: SNAPPY-ROTE
---

# Subject: Math

Math is fundamentally different from the wonder subjects. It is **SNAPPY-ROTE** by design — bound to combat, where the chain mechanic is supposed to feel like pressure. Where philosophy questions teach the player on the way to asking, math questions test what the player already knows, fast. The timer was deliberately left tight (math = pressure point of the game). Char budgets are correspondingly tight.

That said: math is not *only* arithmetic drills. Higher tiers carry brief wonder-moments — famous theorems, π and e, glimpses of calculus — *if* they can be parsed in the timer. Wonder in math comes in flashes, not paragraphs.

## 1. Timing budget

| Stat | Value |
|---|---|
| `SUBJECT_TIMER` | `('math', (8, 0.8))` in `src/player.py` |
| Total timer at WIS 10 | **16s** |
| Total timer at WIS 25 (late-game) | **28s** |
| Default-weapon chain cap | **7** |
| Legendary-weapon chain cap | **10** |
| Per-Q budget at WIS 10, chain-10 | **1.6s** |
| Per-Q budget at WIS 25, chain-10 | **2.8s** |
| Readable words at 240 wpm | **~6 words at WIS 10 chain-10; ~11 words at WIS 25 chain-10** |

**Implication:** math content must be *recognition-fast*. Reading the question must take a fraction of a second; arithmetic computation takes the rest. Choices are typically numbers, short expressions, or short phrases.

Math timer was **NOT** bumped during the 2026-05-11 learning-focused rebalance. Wonder subjects got more time and longer scaffolded prompts; math stayed pressure-first because combat is supposed to feel that way.

## 2. Per-tier WIS expectations + char budgets

| Tier | Expected WIS | Total timer | Per-Q @ chain-10 | **Max record chars** | Density flag |
|---|---|---|---|---|---|
| 1 | 10–12 | 16–18s | 1.6–1.8s | **≤ 100** | 15 words |
| 2 | 12–15 | 18–20s | 1.8–2.0s | **≤ 150** | 22 words |
| 3 | 15–20 | 20–24s | 2.0–2.4s | **≤ 200** | 30 words |
| 4 | 20–25 | 24–28s | 2.4–2.8s | **≤ 280** | 45 words |
| 5 | 25+ | 28s+ | 2.8s+ | **≤ 360** | 60 words |

Hard cap = target × 1.05 per the standard +5% grace.

## 3. Per-tier content profile

| Tier | Conceptual demand | Voice | Typical question shape |
|---|---|---|---|
| 1 | Single-step arithmetic recall — times tables, basic add/subtract, single-digit operations | Symbol-led: "7 × 8 = ?" | `[op] [number] [op] [number] = ?` with numeric choices |
| 2 | Two-step or slightly richer recall — fractions, percentages of round numbers, simple geometry recall | Symbol-led with brief gloss allowed | `½ + ⅓ = ?` / "15% of 80?" / "Area of 5×4 rectangle?" |
| 3 | Multi-step or unfamiliar shape — algebra basics, exponent rules, sequence recognition, geometry formulas | Brief setup permitted | "Solve for x: 2x + 5 = 13" / "What's the 6th Fibonacci number?" |
| 4 | Word problems, advanced algebra, geometry with proof-style reasoning, probability | Scene-led for word problems | "A train leaves at 60 mph; another at 90 mph from opposite direction 300 miles away. When meet?" |
| 5 | Calculus glimpses, advanced number theory, famous theorems, abstract algebra basics | Wonder-led where content allows | "Euler's identity ties 5 fundamental constants. Why is e^(iπ) + 1 = 0 stunning?" |

## 4. North-star exemplars

Three per tier. Generators few-shot from these.

### Tier 1 — pure recall, symbol-led

```
Q: 7 × 8 = ?
A: 56
Choices: 56 / 54 / 63 / 48
```

```
Q: 15 + 27 = ?
A: 42
Choices: 42 / 41 / 43 / 32
```

```
Q: Which is larger: 2/3 or 3/4?
A: 3/4
Choices: 3/4 / 2/3 / They are equal / Cannot tell
```

### Tier 2 — two-step or slightly richer

```
Q: ½ + ⅓ = ?
A: 5/6
Choices: 5/6 / 2/5 / 1/6 / 1/5
```

```
Q: 15% of 80 = ?
A: 12
Choices: 12 / 15 / 11 / 16
```

```
Q: A square has side 6. What is its area?
A: 36
Choices: 36 / 24 / 12 / 30
```

### Tier 3 — multi-step or new shape

```
Q: Solve for x: 2x + 5 = 13
A: x = 4
Choices: 4 / 3 / 5 / 9
```

```
Q: What's the next number? 1, 1, 2, 3, 5, 8, ...
A: 13
Choices: 13 / 11 / 12 / 14
```

```
Q: A circle has radius 5. What is its area? (Use π ≈ 3.14)
A: 78.5
Choices: 78.5 / 31.4 / 25 / 157
```

### Tier 4 — word problems + advanced algebra

```
Q: A train leaves Station A at 60 mph heading east. Another leaves Station B (300 miles east) at 90 mph heading west. After how many hours do they meet?
A: 2
Choices: 2 / 2.5 / 3 / 1.5
```

```
Q: Solve: x² - 5x + 6 = 0
A: x = 2 or x = 3
Choices: x = 2 or x = 3 / x = -2 or x = -3 / x = 1 or x = 6 / x = 5 or x = 6
```

### Tier 5 — calculus glimpses, famous theorems, math wonder

```
Q: Euler's identity says e^(iπ) + 1 = 0. Why is it considered the most beautiful equation in math?
A: It ties five fundamental constants (e, i, π, 1, 0) in one short relation
Choices: 
- It ties five fundamental constants (e, i, π, 1, 0) in one short relation
- It proves that π is irrational
- It is the only equation involving complex numbers
- It defines the natural logarithm
```

```
Q: A function's derivative gives its instantaneous rate of change. What does the derivative of x² equal?
A: 2x
Choices: 2x / x / x²/2 / 2
```

```
Q: Cantor showed that there are different "sizes" of infinity. Which set is LARGER?
A: The real numbers (uncountably infinite)
Choices: 
- The real numbers (uncountably infinite)
- The integers (countably infinite)
- They are the same size (both infinite)
- Neither is larger; infinity has no size
```

## 5. Distractor design (math-specific)

Math distractors are derived from **common wrong-answer patterns**:

- **Off-by-one** (37 vs 38 for 5+33)
- **Wrong-operation** (using + when the question demands ×)
- **Sign error** (returning +X when answer is −X)
- **Wrong base/exponent** (32 vs 25 for 2^5)
- **Forgot to apply unit conversion** (cm/m, percent/decimal)
- **Computed before the conversion** (e.g. compute 15 then forgot it was 15%)
- **Order-of-operations error** (3 + 4 × 2 → 14 instead of 11)
- **Adding numerators AND denominators** for fractions
- **Used wrong formula** (perimeter for area, etc.)

A good math distractor is the result of a **specific mistake a learner might make**, not a random other number. This is the math equivalent of "real rival philosophical positions."

## 6. Math-specific anti-patterns

- **Question requires reading a paragraph for a single arithmetic answer** — fail. Word problems are fine in T4-T5, but should be tight.
- **Answer is "all of the above" or "none of the above"** — banned. These are lazy.
- **Choices that are not parallel in form** — e.g., one numeric, one verbal, one formula — banned unless it's the right kind of question.
- **Ambiguous answers** — math answers must be uniquely correct. If the question allows multiple valid interpretations, the question is broken.
- **Trick questions where the "right" answer depends on a hidden convention** — banned (e.g., 6÷2(1+2) = 9 or 1 viral question is a trick, not a test).
- **Unicode-symbol-as-trap** — distractors that differ only by a Unicode look-alike (× vs * vs ·) are banned.

## 7. Voice for math wonder (T4-T5)

Wonder math is allowed at T4-T5 within tight budgets. The goal is to leave the player wanting to look something up, not to fully explain the concept.

Examples of allowed wonder content:
- π and e — what makes them transcendental
- Famous theorems — Pythagorean, Fermat's last, the Four-Color theorem
- Famous mathematicians — Archimedes' levers, Newton inventing calculus, Euler's productivity, Ramanujan's intuition
- Mathematical paradoxes — Russell's, the Banach-Tarski (T5), the Birthday paradox
- Big numbers and infinity — Graham's number, Cantor's hierarchy
- Cryptography basics — RSA, modular arithmetic

These questions sacrifice a little speed for a little curiosity. Keep them tight; don't write paragraphs.

## 8. Computational correctness gate (built)

Math questions have a uniquely-checkable property: **the answer must be mathematically correct**. The deterministic gate `tools/quizgen/deterministic/math_correctness.py` evaluates the question's arithmetic/algebra/etc. against the claimed answer using sympy.

Shapes handled (deterministic, no LLM):
- Pure arithmetic with ASCII or unicode operators (×, ÷, −, ², ³, √, etc.)
- Fractions (unicode glyphs and ascii notation)
- Percentages ("N% of M")
- "X/Y of M" fraction-of-N shape
- Solve-for-x equations (one solution and multi-root)
- Function evaluation ("If f(x) = ...")
- Comparisons ("Which is larger?")
- Powers (caret and unicode super)
- Square roots (`sqrt(N)` and unicode `√`)

Word problems, conceptual questions, and abstract wonder content fall through with `NA` status (handled by LLM validation).

## 9. Strategy taxonomy

Every math question carries `_meta.strategy` naming the named pedagogical move it teaches:

- **Pillar 1 — Computation strategies** (make-ten, compensate, ×9 = ×10−×1, halve-then-double, etc.)
- **Pillar 2 — Vocabulary & concept recognition** (rhombus, supplementary, dividend/divisor, congruent vs similar, etc.)

See `docs/quiz/math_strategies.md` for the full taxonomy and the distractor-design rule (distractors = answers from skipping the strategy / adjacent-but-wrong concepts).

## 10. Length-parity exemption

Math is exempted from the strict 1.30 length-parity ratio (the philosophy gate). For math, parallel **form** matters (all numeric or all verbal), not parallel **length** — the wrong-operation distractor `68` for the answer `8` is pedagogically valuable even at ratio 8.5.

## 9. What success looks like for the math rebuild

A math bank where:
- A T1 question is recognized and answered in under a second by anyone who knows their tables.
- A T5 question can be a famous theorem that briefly opens a door the player wants to walk through later.
- Distractors teach the player to *not* make a specific common mistake.
- A player chain-attacking with a legendary weapon at WIS 25 can ride a T5 chain to 10 if they really know the material.
- Every answer is mathematically checkable — no ambiguous "right answers."
