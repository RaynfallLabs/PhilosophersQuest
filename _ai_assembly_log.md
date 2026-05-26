# AI bank assembly log

- Pool: 1321 questions across 14 source files
- After intra-bank dedup: 1321
- After gate validation: 1225 pass (1 soft-warn), 96 fail
- Final bank size: **1225**

## Sources

- `_gen_ai_t1.json` — 217 questions
- `_gen_ai_t2_p12.json` — 128 questions
- `_gen_ai_t2_p345.json` — 157 questions
- `_gen_ai_t3_p12.json` — 130 questions
- `_gen_ai_t3_p34.json` — 122 questions
- `_gen_ai_t3_p5.json` — 65 questions
- `_gen_ai_t4_p12.json` — 80 questions
- `_gen_ai_t4_p3.json` — 45 questions
- `_gen_ai_t4_p4.json` — 88 questions
- `_gen_ai_t4_p5.json` — 96 questions
- `_gen_ai_t5_p12.json` — 49 questions
- `_gen_ai_t5_p34.json` — 53 questions
- `_gen_ai_t5_p5.json` — 31 questions
- `_gen_ai_t5_p5_supp.json` — 60 questions

## Tier distribution

- T1: 214
- T2: 227
- T3: 315
- T4: 292
- T5: 177

## Gate failures (dropped)

- `choice_shape_parity`: 45
- `answer_collision`: 34
- `duplicate`: 22
- `length_budget`: 21
- `context_no_meta_references`: 1

