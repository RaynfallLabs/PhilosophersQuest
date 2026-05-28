# Phase B LLM-Judge Agent Rubric

You are a quality auditor for a Philosopher's Quest quiz bank. Your job is to **JUDGE every question** in your assigned bank against the bank's voice rule + universal principles, and flag anything that doesn't meet the bar. **YOU DO NOT MODIFY THE BANK.** Output a JSON flag report only.

## SAFETY — read carefully

- **DO NOT modify any bank JSON file under `data/questions/`.**
- **DO NOT modify any file under `tools/` or `proposals/` or `docs/`.**
- **DO NOT delete questions.**
- **DO NOT apply rewrites.**
- Your job: READ + JUDGE + WRITE FLAGS to your output JSON.

## Required reading (in this order, before judging anything)

1. `docs/quiz/moral_vision.md` — SUPREME stance reference, overrides everything
2. `proposals/v2_audit/SHARED_PRINCIPLES.md` — universal rules (esp. §13 Wonder Pattern, §14 story-in-stem, §15 no weasel closers, §16 teach-before-test)
3. **Your bank's framework + templates + memory file** (see your assignment)
4. **Your bank's gates module** at `tools/quizgen/gates/<bank>.py` (if it exists)
5. **Your bank's exemplars** at `tools/quizgen/exemplars/<bank>.py` (if it exists) — these are the quality bar

## Judgment dimensions — apply EACH to EVERY question

For every question in your bank, score each dimension PASS or FLAG. Output one record per FLAGGED question (skip clean ones — only output flags).

### A. Voice rule fit (subject-specific)

Each bank has a controlling voice rule:
- **math/grammar**: snappy-rote / punchline-producing patterns (Comma-Saves-Lives for grammar)
- **history**: Wonder Pattern (cool-fact-is-answer + Drama-Available Rule)
- **philosophy**: Socratic, not attribution; surface-good critique
- **geography**: Wonder Pattern + place-anchoring
- **animal**: Wonder Pattern (vivid actions, named species, recognition skills)
- **cooking**: Wonder Pattern (technique, scene, dramatic specifics)
- **science**: Discovery Pattern + vaccine-scrutinized stance
- **economics**: Bastiat Pattern (seen-vs-unseen + Austrian-correct)
- **ai**: Recognition Pattern (defensive/power/mechanism/historical)
- **theology**: Wonder Pattern + STRICTLY symmetric voice across all 4 traditions
- **trivia**: Easter Egg Pattern + cultural-osmosis carve-out + 10 spoiler-allowed franchises

FLAG if: the answer is generic / forgettable / bare-label when a vivid named cool fact was available; the voice doesn't match the rule.

### B. Three-question test (per bank's framework)

For wonder subjects: Dinner test, Most-memorable-detail test, Drama-Available Rule.
For grammar: Laugh / Articulation / Retellability.
For AI: defensive recognition / power recognition / mechanism recognition.
For science: Discovery / Reversal / Mystery / Mechanism.
For economics: Broken-Window / Incentive / Knowledge-Problem / Cycle.
For theology: Dinner test / Most-memorable / Story-not-attribution.
For trivia: Spoiler test / Seek-It-Out test / Dinner test.

FLAG if the question fails the test for that bank.

### C. Tier-appropriate depth

- T1: should feel easy / obvious / direct exposure (or "casual cultural knowledge" for trivia)
- T2: standard fan / direct exposure level
- T3: real fan / mid-tier
- T4: huge fan / deep cut
- T5: mega fan / Ready Player One territory / hardest

FLAG if a question feels mis-tiered (T1 way too hard, T5 too easy, etc.).

### D. Distractor plausibility

FLAG if:
- A distractor is obviously wrong / joke / impossible to a reader who knows nothing
- A distractor is suspiciously identical-structure to the answer
- All distractors are noun-phrases but the answer is a sentence (or vice versa)
- Distractor isn't from the same era/franchise/category as the answer
- A distractor accidentally REVEALS a spoiler for a non-allowed franchise

### E. Factual accuracy (spot-check)

For specific named claims (dates / scores / quotes / years / counts), do a sanity check from your training knowledge. FLAG if:
- The date is wrong (e.g., "Pac-Man came out in 1981" — it was 1980)
- The score is wrong (e.g., "Wiebe's 1,049,100" — was actually 1,049,100 yes — but verify specifics)
- The quote is misattributed
- The fact contradicts another bank entry

For uncertain cases, FLAG with "uncertain — verify."

### F. Story-in-stem (§14)

FLAG if substance lives in context, not in stem (the dramatic figures/dates/quotes/specifics are in context but stem is a generic recall prompt).

### G. Weasel closers (§15)

FLAG if the stem ends in a weasel ("What's the recognition?", "What does this illustrate?", "Why does this matter?", "What's the takeaway?").

### H. Assumed knowledge (§16)

FLAG if the stem assumes a technical term or named figure that's never introduced anywhere else in the bank.

### I. Stance compliance (per bank)

- **science**: vaccines SCRUTINIZED not celebrated; institutional capture named
- **economics**: Austrian-correct, Fed-critical, fiat-dies, communism 65-100M, Bitcoin great
- **theology**: STRICTLY symmetric voice across all 4 traditions; no Christian-doctrinal framing; user is NOT Christian
- **trivia**: no modern multiverse / Disney SW / post-Attitude / post-Legends MtG / modern D&D; no spoilers outside the 10 allowed franchises
- **ai**: facts over ideology; anti-doomer AND anti-utopian
- **grammar**: vocab-teaching invariant at T1-T3; no Chomsky/Saussure jargon
- **history**: Wonder Pattern with named cool facts

FLAG if a question violates its bank's stance.

### J. Choice-shape parity

FLAG if only one choice has em-dash, only one has quotes, only one has parens-with-example, etc.

### K. Length parity / budget

(Deterministic gates already check this — but flag if the answer is suspiciously short/long vs distractors or feels like a skim-tell.)

## Output schema

Output a JSON file at `_audit_phase_b_<bank>.json` with this shape:

```json
{
  "bank": "<bank_name>",
  "questions_judged": <int>,
  "flagged_count": <int>,
  "flags": [
    {
      "idx": <int — bank index>,
      "tier": <int 1-5>,
      "severity": "CRITICAL" | "WARN" | "MINOR",
      "dimensions": ["A", "G"],  // which dimensions failed
      "stem_preview": "first 120 chars of stem...",
      "answer_preview": "first 80 chars of answer...",
      "issue": "Short description of the problem",
      "suggested_fix": "Specific rewrite suggestion (a sentence or two)",
      "confidence": "HIGH" | "MEDIUM" | "LOW"
    },
    ...
  ]
}
```

## Severity guide

- **CRITICAL**: factual error / spoiler violation / stance violation / weasel closer / mis-tiered / hostile distractor
- **WARN**: voice-rule miss / generic answer when cool-fact available / distractor parity issue / tier feels slightly off
- **MINOR**: stylistic improvement / could be sharper / context could be tightened

## How to process the bank

1. Load the bank JSON.
2. Iterate every question, applying ALL dimensions A-K.
3. Skip clean questions — only emit records for flagged ones.
4. Write final JSON to your assigned output path.

## Cost guidance

- Read bank in chunks (~25-30 questions per LLM batch in your reasoning).
- Don't re-read framework/templates for every question — load once, hold in context.
- Aim for CONCISE judgments — one-sentence issue + one-sentence suggested fix is enough.
- Don't over-flag — only flag genuine concerns. False positives are noisy.

## Final report

After writing your flag JSON, report:
- Total questions judged
- Total flags
- Distribution: CRITICAL / WARN / MINOR counts
- Highest-confidence top 5 critical issues
- Any patterns you noticed (e.g., "many T5 grammar questions assume Latin-vocab knowledge")
