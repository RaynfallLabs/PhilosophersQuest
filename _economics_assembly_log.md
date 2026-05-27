# economics bank assembly log

- Pool: 1200 questions across 10 source files
- After intra-bank dedup: 1200
- After gate validation: 1196 pass (0 soft-warn), 4 fail
- Final bank size: **1196**

## Sources

- `_gen_economics_t1_p12.json` — 120 questions
- `_gen_economics_t1_p345.json` — 120 questions
- `_gen_economics_t2_p12.json` — 120 questions
- `_gen_economics_t2_p345.json` — 120 questions
- `_gen_economics_t3_p12.json` — 120 questions
- `_gen_economics_t3_p345.json` — 120 questions
- `_gen_economics_t4_p12.json` — 120 questions
- `_gen_economics_t4_p345.json` — 120 questions
- `_gen_economics_t5_p12.json` — 120 questions
- `_gen_economics_t5_p345.json` — 120 questions

## Tier distribution

- T1: 240
- T2: 238
- T3: 239
- T4: 240
- T5: 239

## Gate failures (dropped)

- `duplicate`: 4
- `answer_collision`: 2

