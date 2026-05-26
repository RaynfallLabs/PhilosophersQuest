# science bank assembly log

- Pool: 1435 questions across 15 source files
- After intra-bank dedup: 1299
- After gate validation: 1286 pass (0 soft-warn), 13 fail
- Final bank size: **1286**

## Sources

- `_gen_science_t1_p123.json` — 140 questions
- `_gen_science_t1_p45.json` — 110 questions
- `_gen_science_t2_p123.json` — 140 questions
- `_gen_science_t2_p45.json` — 110 questions
- `_gen_science_t3_p123.json` — 155 questions
- `_gen_science_t3_p45.json` — 120 questions
- `_gen_science_t4_p123.json` — 140 questions
- `_gen_science_t4_p4.json` — 50 questions
- `_gen_science_t4_p5.json` — 70 questions
- `_gen_science_t5_p1.json` — 50 questions
- `_gen_science_t5_p123.json` — 135 questions
- `_gen_science_t5_p2.json` — 35 questions
- `_gen_science_t5_p3.json` — 50 questions
- `_gen_science_t5_p4.json` — 50 questions
- `_gen_science_t5_p5.json` — 80 questions

## Tier distribution

- T1: 250
- T2: 248
- T3: 274
- T4: 250
- T5: 264

## Gate failures (dropped)

- `length_budget`: 9
- `duplicate`: 4

## Dedup drops (136)

Questions dropped because their normalized stem matched an
earlier-accepted question. Tier-complete files take priority.

