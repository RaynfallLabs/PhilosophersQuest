---
version: 1
date: 2026-05-12
subject: cooking
in_game_action: food preparation (escalator_chain mode)
style_verdict: WONDER-DRIVEN with practical anchoring
---

# Subject: Cooking

Cooking sits between math (SNAPPY-ROTE, combat) and philosophy (WONDER-DRIVEN, identification). Its in-game action — *preparing food* — runs as `escalator_chain`: questions get harder each round, and chain depth determines food quality. Players have ~42 seconds at WIS 10, ~70 seconds at WIS 25. That's enough breathing room for scene-led, scaffolded questions — but not paragraphs.

Cooking pulls weight on FIVE pillars (per `docs/quiz/cooking_strategies.md`):

1. **Practical kitchen skills**
2. **Nutrition** (firm + contested handled honestly)
3. **World cuisines**
4. **Food history & wonder**
5. **Family meals + food ceremonies**

## 1. Timing budget

| Stat | Value |
|---|---|
| `SUBJECT_TIMER` | `('cooking', (28, 1.4))` in `src/player.py` |
| Total timer at WIS 10 | **42s** |
| Total timer at WIS 25 (late-game) | **63s** |
| Default-weapon chain cap | n/a (cooking uses different action) |
| Typical chain target | **10-15** |
| Per-Q budget at WIS 10, chain-12 | **3.5s** |
| Readable words at 240 wpm + decision | **~10 words/question at WIS 10** |

## 2. Per-tier char budgets

| Tier | Hard cap | Word count guideline | Voice |
|---|---:|---|---|
| T1 | **≤ 280** | ~30 words | Symbol-led or single-fact recall. "Sharp knife or dull knife — which is safer?" |
| T2 | **≤ 480** | ~70 words | One-line scene + question. "A chef arranges all chopped ingredients before turning on heat. The French term is ___?" |
| T3 | **≤ 680** | ~110 words | Scene + technique-with-consequence. Brief setup permitted. |
| T4 | **≤ 900** | ~150 words | Multi-sentence setup + judgment / chemistry / history-context required. |
| T5 | **≤ 1100** | ~180 words | Wonder-led; deep history; contested-topic balanced framing; science detail. |

Hard cap = target × 1.05 per the standard grace zone.

## 3. Per-tier content profile

| Tier | Practical | Nutrition | Cuisine | History/Wonder | Family/Ceremony |
|---|---|---|---|---|---|
| T1 | Safety basics, basic heat methods | Food group identification | Common dish recognition | Where the potato came from | Birthday cake candles, napkin etiquette |
| T2 | Knife cuts basic, mise en place | Macros + ultra-processed | Mother sauces, signature dishes | Columbian Exchange basics | Sunday dinner, Thanksgiving 1621 |
| T3 | Heat methods advanced, ratios | NOVA classification, fermented food benefits | Regional cuisine + technique | Spice trade, food origin stories | **Western banquets, wedding cake history** |
| T4 | Kitchen chemistry, scaling | Seed oil debate, raw milk debate, traditional foods principles | Famous chef techniques | **Service à la russe 1810**, brigade system, Maillard 1912 | **Medieval banquets, Versailles court dining, Victorian dinner-party codes** |
| T5 | Modernist cuisine | Cholesterol revisionism, Blue Zones research | Obscure regional cuisines | Food in revolutions, philosophy of taste | **Debutante cotillions, royal banquet diplomacy** |

## 4. Voice rules

### Scene-led, not definition-shell

NEVER:
- "What is mise en place?"
- "Define nixtamalization."
- "What does umami mean?"

ALWAYS:
- "A chef arranges all chopped ingredients before turning on the heat. The French term is ___?"
- "Mesoamerican cooks soaked corn in alkaline water (lime or wood ash) — a process that unlocked B3 (niacin) and prevented pellagra. What is this process called?"
- "Kikunae Ikeda isolated a savory compound from kombu in 1908, naming it 'umami.' What kind of taste does it describe?"

The anti-rote gate is **NOT exempted** for cooking. Scene-led phrasing is the discipline.

### Concrete handles beat jargon

- *The fond in the pan after searing.* / *The crisp crust the Maillard reaction created.* / *The slack way the chicken thigh felt before it tightened up cooking through.*
- Bad: "What scientific process produces brown color in seared meat?"
- Good: "A steak hits the hot pan. As it sears, the surface turns deep brown and develops complex savory flavor — amino acids and reducing sugars reacting with heat. What's the chemist's name for this 1912-discovered reaction?"

### Wonder, not advocacy

Even when the bank takes a position on contested nutrition, **present**, don't preach.

Bad: "Why are seed oils inflammatory?"
Good: "Many traditional-food advocates argue that high omega-6 polyunsaturated oils (soybean, corn, canola), especially when heated or reused, contribute to inflammation. Mainstream cardiology disagrees, citing PUFA's effect on LDL. Which of the following best summarizes the debate?"

Bad: "Modern processed foods are bad for you."
Good: "The NOVA classification, developed by Brazilian researchers in 2009, sorts foods by industrial processing level. Group 4 — 'ultra-processed' — correlates in observational studies with obesity, diabetes, and depression. Which of the following best describes a NOVA-4 food?"

## 5. Distractor design (per pillar)

- **Practical**: Distractors = adjacent-but-wrong techniques (sauté vs. sweat — both pan-fried but different intent). "Julienne" wrong against "brunoise" — both fine cuts but different shapes. Wrong-meat-temperature distractors (chicken 145 instead of 165).

- **Nutrition**: Distractors = competing schools (low-fat 1990s; low-carb 2010s; balanced traditional). Wrong macronutrient functions. Wrong vitamin sources.

- **Cuisine**: Distractors = adjacent-but-wrong dishes/cuisines. Cantonese dish offered as Sichuan. Bolognese paired with spaghetti (wrong — Bolognese is traditionally with tagliatelle).

- **History**: Distractors = plausibly-confused dates, places, attributions. Wrong chef credit. Wrong country origin (potato Andes-not-Ireland; tomato Mexico-not-Italy).

- **Family/Ceremony**: Distractors = adjacent-but-wrong traditions. Afternoon tea vs. high tea conflation. Easter ham vs. Easter lamb across denominations. Wedding cake tier symbolism mistakes.

## 6. Cooking-specific anti-patterns

- **No "all of the above" / "none of the above"** — lazy
- **No trick questions** based on regional naming disputes that have multiple valid answers (e.g., "Is it a hoagie or a sub?")
- **No advocacy framing** even on firm-evidence topics — let evidence speak through the question structure
- **No food shaming** — present nutrition information, don't moralize ("If you eat X you are unhealthy")
- **No contemporary celebrity chef worship** without substance (a question about Gordon Ramsay should reference something he actually did/said, not just his fame)
- **No anachronisms** — don't have a question imply Italians had tomatoes before 1500, or that fork-and-knife eating was universal before the 18th century

## 7. Contested topics — required framing

When a question hits a contested topic from the strategies doc, it MUST present both sides:

- "X school argues Y because Z" — and — "Mainstream Y position holds A because B"
- The CORRECT ANSWER is the one that best summarizes the *debate*, not the one that endorses a side
- Distractors are caricatures of either side OR irrelevant trivia

## 8. Quality gates (NOT relaxed)

| Gate | Threshold | Exempted for cooking? |
|---|---|---|
| schema | required | No |
| length_parity | **1.50 ratio + 22% mean dev** (calibrated for cooking) | No |
| length_budget | per-tier cap above | No |
| anti_rote | regex match → fail | **No** (forces scene-led) |
| duplicate | 0.85 similarity | No (standard threshold) |
| `validate_cooking_facts` (NEW LLM) | fact-check pass | applies |
| `validate_balance` (NEW LLM) | both-sides on contested topics | applies |

The 1.50 ratio (vs. philosophy's 1.30) accommodates the natural length variation of single-word answers — cuisine names, knife cuts, technique names. Still catches leak-by-length cases ("Yes" vs "Yes if temperature is greater than 165"). See `tools/quizgen/deterministic/length_parity.py` `SUBJECT_RATIO_OVERRIDES`.

## 9. What success looks like for the cooking rebuild

A cooking bank where:
- A T1 question teaches a kid how to safely hold a knife.
- A T2 question reveals that *companion* etymologically means "one who eats bread with you."
- A T3 question makes the player respect nixtamalization or a Sunday gravy tradition.
- A T4 question shows the chemistry behind the brown crust on a steak — or the Versailles theater of public royal dining.
- A T5 question makes the player want to read Brillat-Savarin or visit a coffee ceremony in Ethiopia.
- Family meals + ceremonies are honored alongside science + technique.
- Contested nutrition debates are presented honestly, not flattened.
