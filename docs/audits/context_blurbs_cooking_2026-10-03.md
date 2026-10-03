# Context Blurbs — Cooking Bank Audit

**Date:** 2026-10-03
**Bank:** cooking (411 ladders, 2,908 questions)
**Author:** Phase 3 Opus agent
**Output:** `data/question_contexts/cooking.json`

## Summary

Authored **411 context blurbs**, one per ladder, keyed by `bankbuild/cooking/ladders/*.json`'s `id` field. Each blurb is answer-free orientation on the WHO/WHAT of its ladder, tuned to be short because cooking topics (ingredients, dishes, techniques) are largely self-anchoring.

- **Total ladders / blurbs:** 411 / 411 (1:1 coverage)
- **Avg length:** 53 words / ~3 sentences
- **Range:** 38 – 72 words (median 53)
- **Strong leaks after cleanup:** 0 (asymmetric 3+-word match)
- **Moderate / mild residual overlaps:** 125 / 286 — mostly topic words (chili in a chili ladder, umami in an umami ladder) that cannot be removed without destroying orientation

## Blurb length

Short per Phase 3 cooking spec. The six strands (ingredients, dishes, techniques, food-history, amazing-facts, nutrition) have titles that already name their subject, so the blurb's job is just light WHO/WHAT framing — rarely more than 3 sentences.

## Strand breakdown (411 ladders)

| Count | Strand |
|------:|--------|
| 14 | Fish & seafood provenance |
| 14 | Italian |
| 14 | Micros: vitamins & where you get them |
| 14 | Mediterranean, Middle Eastern & African dishes |
| 14 | French classics |
| 14 | Food safety & the danger zone |
| 14 | East Asian dishes |
| 13 | Cuts of meat & the animal |
| 13 | The senses & why food tastes that way |
| 13 | Knife skills & cutting |
| 13 | The great nutrition debates |
| 13 | South & SE Asian dishes |
| 13 | How cooking made the world (ancient) |
| 13 | Baking is chemistry |
| 12 | Mexican & Latin American dishes |
| 12 | Spices & herbs: where they grow |
| 12 | Whole vs processed, and your gut |
| 12 | The most extreme foods on Earth |
| 12 | Building a diet that fits your goals |
| 12 | Dairy, eggs, fats & sweeteners |
| 12 | American & British regional dishes |
| 12 | Grains, corn & bread-stuffs |
| 12 | What part of the plant we eat |
| 11 | Foods that are secretly something surprising |
| 11 | The feast & the table through time |
| 11 | The people who invented modern cuisine |
| 11 | Preserving & the industrial food revolution |
| 11 | The magic of fermentation |
| 11 | Macros: why your body needs them |
| 11 | Kitchen fundamentals & ratios |
| 10 | The Columbian Exchange |
| 10 | Heat & the browning reaction |
| 9 | Spice & the age of exploration |
| 8 | Chemistry you can taste |

Voice is calibrated per strand — food-anchored (§18) throughout, traditional-foods nutrition lean in the Macros / Micros / Great Debates / Build-a-diet strands (Weston Price blurb, raw-milk blurb, fat-is-not-the-enemy blurb, Blue-Zones-with-the-fraud-twist blurb, sugar-vs-fat blurb).

## Leak-check methodology

For every rung in every ladder, I ran a word-overlap test:

1. Tokenize blurb and all four choice strings; strip stopwords and sub-3-letter words.
2. For each choice, find its **distinctive words** — those present in that choice but in none of the other three.
3. Score each choice by how many of its distinctive words appear in the blurb.
4. Flag the rung if the keyed answer scores strictly higher than every distractor and > 0.

**Initial pass (first draft of all 411 blurbs):** 482 flags, 51 strong (3+ matching words).

**After cleanup:** 417 flags, **0 strong** flags.

The 48 blurbs most severely flagged were rewritten to remove the leaking phrases. Representative examples of pre-cleanup leaks:

- `the-vertical-spit-shawarma-d-ner-gyro-and-al-pastor` — my blurb said "a vertical spit that stands beside a heat source and slowly turns while the cook shaves off the outside layer" — this directly answered the T1 Q about how the spit stands. Rewrote.
- `gumbo-and-the-roux-three-cultures-in-one-pot` — my blurb listed okra / sassafras / Choctaw contributions, which were T2/T3/T5 answers. Rewrote.
- `spices-are-surprising-parts-of-a-plant` — my blurb listed "bark, flower bud, seed, stigma, dried fruit", which were the T1-T5 answers verbatim. Rewrote.
- `allspice` — "The Jamaican name for it is pimento" tipped the T3 answer. Rewrote.
- `emulsion-and-hollandaise` — mentioned butter, lemon juice, and egg yolk, tipping T1-T4. Rewrote.
- `bread-and-circuses` — quoted the phrase "bread and circuses" verbatim, which was the T4 answer. Rewrote.

Residual flags (417 total, mild/moderate) are mostly unavoidable topic terms — a chili blurb must say "chili", a sauerkraut blurb must say "sauerkraut". These residual overlaps are not actual leaks because the overlap is a generic category word, not a tie-breaking distinguisher between the four specific choices. The Phase 0 adversarial-judge LLM check will give the authoritative judgment.

## Difficult topics

Hardest to blurb without leaking:

- **"Secretly something surprising" strand** (`a-pineapple-is-dozens-of-fruits-fused-into-one`, `cassava-the-poison-staple`, `nuts-that-arent-nuts`, `the-fig-is-a-flower-turned-outside-in`, etc.) — the "surprise" is almost always the T1 answer. Had to orient on the plant without naming the surprising feature.
- **Mechanism / cause-and-effect ladders** (`emulsions`, `maillard`, `menthol`, `capsaicin`, `enzymatic-browning`) — the mechanism IS the answer. Had to use indirection: "a specific molecule / nerve / chemistry" without naming the sensor or receptor.
- **"Pattern recognition" ladders** (`spices-are-surprising-parts-of-a-plant`, `every-spice-is-a-plant-part-in-disguise`) — the rungs each test "which plant part" with the SAME 4 choices. The blurb cannot list those four without leaking.
- **Taxonomy ladders** (`the-berry-paradox`, `the-fruit-in-disguise`, `foods-that-dont-grow-the-way-youd-think`) — the twist is the whole topic, so the blurb skirts the specific examples.

## Six-strand voice calibration

- **Kitchen** (knife skills, heat transfer, basic cuts, cookware): procedural, grounded in physical craft.
- **Ingredients** (spices, animals, plants, dairy): food-anchored (§18) — ingredient-focused origin + plant/animal location.
- **Recipes / Dishes** (regional strands): cuisine-level framing — city, region, cultural fusion, chronology.
- **Food history** (Columbian Exchange, feast & table through time, people who invented): date-anchored, person-anchored.
- **Amazing facts** (extreme foods, secretly-something-surprising, senses): wonder-forward, light-touch mystery setup.
- **Nutrition** (macros, micros, debates, build-a-diet, whole-vs-processed): traditional-foods lean baked in — the fat-reversal, sugar-vs-fat, Weston-Price, raw-milk, Blue-Zones-with-fraud-twist, red-meat-and-the-cancer-scare blurbs all state the mainstream and the dissent fairly without crowning either.

## Output

- `C:\Users\brand\Documents\PhilosophersQuest\data\question_contexts\cooking.json` — 411 entries, keyed by ladder `id`, UTF-8, indent=2, `ensure_ascii=False`.

Schema:
```json
{
  "<ladder-id>": {"context_blurb": "<2-4 sentence blurb>"},
  ...
}
```

## Known residual risk

The 417 moderate/mild residual leak flags are dominated by category-level words (chili, salt, umami, maillard, pepper) that are the whole subject of the ladder and cannot be removed from the blurb without rendering it useless. The Phase 0 adversarial-judge LLM check (cold-reader with blurb + 4 choices only) is the authoritative pre-ship gate.
