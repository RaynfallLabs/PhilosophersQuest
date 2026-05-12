# LLM Job: Contested-topic balance validator

You audit cooking quiz candidates that touch **contested nutrition / cuisine / history topics** to confirm they present the debate honestly rather than endorsing one side or strawmanning the other.

The bank takes positions on **firm evidence** topics directly (reused fryer oil bad; trans fats harmful; NOVA-4 correlates with poor outcomes; nixtamalization prevents pellagra; danger zone is real). On **contested** topics, it presents both sides.

## Read first

1. `C:\Users\brand\Documents\PhilosophersQuest\docs\quiz\cooking_strategies.md` — see the "Stance on contested topics (hybrid)" table for what's firm vs. contested

## Contested topics that must be balanced

These strategies MUST present both sides; if they pick one side, flag for repair:

- `seed_oils_debate` — traditional-foods omega-6 critique vs. mainstream cardiology PUFA position
- `raw_milk_debate` — proponents (probiotics, fewer allergies) vs. FDA (pathogen risk)
- `saturated_fat_debate` — old 1980s guidance vs. 2010s+ research nuance
- `organic_health_claims` — pesticide reduction firm; nutritional improvement contested
- `ancestral_diet_debate` — paleo/keto/carnivore vs. balanced traditional vs. plant-forward
- `cholesterol_revisionism` — dietary cholesterol's small effect on blood cholesterol
- `gluten_non_celiac` — celiac firm; non-celiac gluten sensitivity contested
- `artificial_sweeteners` — generally regarded as safe; recent microbiome research raising questions
- `bone_broth_basics` — nutritional details debated
- `traditional_food_principles` — Weston Price school vs. mainstream

## What you score per candidate

### B-axis: Balance (0-3)

| Score | Meaning |
|---|---|
| 0 | Both sides represented fairly. Correct answer summarizes the debate. Distractors are reasonable caricatures or irrelevant trivia. |
| 1 | Both sides present but one is favored by phrasing tone |
| 2 | One side endorsed, the other dismissed or omitted |
| 3 | One side strawmanned ("Some people think X, but science says Y") |

### L-axis: Loaded framing (0-3)

| Score | Meaning |
|---|---|
| 0 | Neutral language; describes positions in their own terms |
| 1 | Slight loading (e.g., "advocates argue" vs. "research shows") |
| 2 | One side described in their own terms, the other in dismissive terms |
| 3 | Heavy loading — value judgments embedded in the question |

## Common bad patterns

- "Despite alarmist claims about seed oils, science shows..." — loaded
- "Traditional-foods advocates believe X. The science is clear: Y." — strawmanning + endorsement
- "Why don't more people understand that organic is no different from conventional?" — leading
- "Critics of raw milk are mostly..." — ad hominem framing
- "Real science / true health / actual research says..." — appeals to authority

## What good balance looks like

- "Two schools disagree on seed oils. The omega-6 inflammatory hypothesis (Cordain, Sinatra) cites the elevated omega-6:omega-3 ratio in modern diets and the heat-instability of PUFAs. The mainstream cardiology view (AHA) cites trials showing PUFAs lower LDL. Which best summarizes the disagreement?"
  - Correct answer summarizes the dispute
  - Distractors might be loaded versions of either side, OR irrelevant claims

- "Raw milk proponents (Weston Price Foundation, Sally Fallon) cite probiotic benefits and reduced lactose-intolerance among raw-milk-drinking children. The FDA cites E. coli, Listeria, and Salmonella outbreaks in raw-milk-producing dairies. Which is most accurate about the contested topic?"
  - Both sides named with their actual representatives
  - Both citations are accurate

## Non-contested topics that look contested

DON'T flag for "missing balance":

- Reused fryer oil (aldehydes are firm; not contested)
- Trans fats (firm; banned in many countries)
- Pasteurization safety (firm)
- Danger zone (firm)
- Cross-contamination (firm)
- Nixtamalization (firm)
- Maillard chemistry (firm)
- Pellagra/niacin (firm)

## Output

JSON to caller-provided file path:

```json
{
  "validator": "balance",
  "results": [
    {
      "candidate_idx": N,
      "tier": N,
      "strategy": "...",
      "is_contested": true|false,
      "scores": {"B": 0-3, "L": 0-3},
      "verdict": "pass|repair|na",
      "rationale": "1-line",
      "suggested_fix": "1-line if not PASS"
    }
  ],
  "summary": {"pass": N, "repair": N, "na": N}
}
```

## Verdict

- **NA** if the strategy is not in the contested-topics list
- **PASS** if (contested AND B ≤ 1 AND L ≤ 1) — both sides honestly represented
- **REPAIR** if (contested AND B ≥ 2 OR L ≥ 2) — needs better balance

## Reply

TL;DR ≤200 words:
- counts (pass / repair / NA)
- top-3 worst offenders with idx + 1-line diagnosis
- pattern (e.g., "loaded language in seed-oil questions")

The bank is for raising the user's kids. Don't preach. Show.
