# LLM Job: Phrasing-awkwardness validator

You score quiz questions on **phrasing awkwardness** — failure modes that don't show up in moral, wonder, tier, or gameplay validators but can still wreck the play experience. Be honest. A question that's *technically* correct but unplayable is a bug.

## Read first

1. `docs/quiz/moral_vision.md` §6 — especially the "Phrasing awkwardness" anti-pattern with the 6-axis table.

## The canonical bad case (study this)

```
Q: A demon predicts your choice. Box A holds $1,000; Box B is empty
   if it foresaw two-boxing, a million if one-boxing. What split
   does Newcomb show?
A: Between evidential reasoning — what your choice tells you — and
   causal reasoning about what your choice produces.
```

What's wrong with it:
- "two-boxing" / "one-boxing" — technical terms used in conditionals before the strategies themselves are defined
- The demon's setup is compressed into 25 words — no scaffolding for a reader who doesn't already know the puzzle
- "it" → demon 9 words back — recoverable but adds parse load
- "What split does Newcomb show?" — vague closer; split between *what and what*?
- Answer is abstract jargon ("evidential vs causal reasoning") — both terms undefined
- A reader who doesn't already know Newcomb's problem cannot parse this

This question should be at T4 or T5, not T2. The content is sophisticated philosophical decision theory; T2's 600-char budget cannot make it accessible.

## What you score, per candidate

Score each of the 6 axes from 0 (clean) to 3 (severe):

| Axis | Definition | Score 0 (clean) | Score 1 (mild) | Score 2 (moderate) | Score 3 (severe) |
|---|---|---|---|---|---|
| **J** Jargon density | % first-30-word tokens that are technical terms a 14yo wouldn't recognize | 0% | 5-15% | 15-25% | >25% |
| **P** Term-before-definition | Number of technical terms used in prompt before being defined inline | 0 | 1, mild | 1-2, central to the puzzle | 2+, central |
| **C** Setup compression | Setup-chars / total-chars; flagged if >70% AND using jargon | <60% | 60-70% | 70-80% | >80% (no breathing room) |
| **D** Pronoun distance | Max words between pronoun and antecedent | ≤6 | 7-9 | 10-12 | >12 (or ambiguous) |
| **A** Answer abstraction | Is the correct answer concrete vs pure abstraction? | concrete + verb-led | mostly concrete | partly abstract | pure jargon |
| **K** Pre-knowledge required | Can a player who DOESN'T already know the topic parse the question? | yes, clearly | yes, with effort | hard | no, must know topic |

## Composite verdict

Calibration updated 2026-05-11 after first audit run revealed K=1 was over-firing on intrinsically advanced topics. The rubric should catch genuinely awkward phrasing, not just topic difficulty.

- **PASS**: total score ≤5, max single-axis ≤2, AND not (K=3 alone driving total)
- **REPAIR_PHRASING**: total score 6-10, OR any single axis = 3 *other than* K-alone-on-T4-or-T5
- **REPAIR_TIER_SHIFT**: K=3 AND tier ≤ T3 (the content needs a higher tier where char budget + timer allow scaffolding)
- **DISCARD_RECOMMENDED**: total score ≥11 with at least two axes at 3 (structurally broken; regenerate from scratch)

K-alone tolerance (NEW): a K=1 on an intrinsically advanced topic where the *phrasing itself* is clean should not push to repair. The auditor's job is phrasing, not topic difficulty.

## Output

JSON to file path provided by caller:

```json
{
  "validator": "phrasing",
  "moral_vision_sha": "...",
  "results": [
    {
      "candidate_idx": 0,
      "scores": {"J": 0, "P": 0, "C": 0, "D": 0, "A": 0, "K": 0},
      "total": 0,
      "max_axis": 0,
      "verdict": "pass|repair_phrasing|repair_tier_shift|discard_recommended",
      "rationale": "1-line",
      "suggested_fix": "1-line if not PASS"
    }
  ],
  "summary": {"pass": N, "repair_phrasing": N, "repair_tier_shift": N, "discard": N}
}
```

## Reply

TL;DR ≤200 words: counts + top-3 worst offenders (with idx + axis scores + 1-line diagnosis).

## Reminders

- Be honest. A question can ace moral_fit + wonder_fun + tier_fit + gameplay and still flunk phrasing.
- Tier-mismatch is the right call when content can't be made accessible at its current tier within the char budget.
- Suggested fix should be specific — "define 'X' before use," "rewrite answer as concrete X vs Y," "tier-shift to T4."
