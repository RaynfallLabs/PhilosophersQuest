# LLM Job: Viral check (final sanity pass)

This is the last gate before commit. You read a random sample of approved questions and ask: *would the author be embarrassed by intellectual flimsiness, partisan flame-bait, strawmen of opposing views, condescension, or punching down?*

## Read first

1. `docs/quiz/moral_vision.md` §7 (the viral test) and §9 (what this bank is not).

## What this test catches

- Questions that read as advocacy when re-quoted out of context
- Questions that condescend to a religious, cultural, or political tradition
- Questions whose distractors look like mockery
- Questions whose answer is technically defensible but glib about real suffering
- Questions that punch down

## What this test is NOT

- It is **not** "would the social-media mob be mad?" Substantive ideological positions on contested questions are welcome if they are intellectually serious.
- It is **not** "is this balanced?" The bank explicitly rejects false equivalence between sustained scholarship and slogans.
- It is **not** wonder/fun scoring (other validator handles that) or fact-checking (separate validator).

## What you do

For each candidate in the sample (typically 20–50 per subject):

1. Read the question + answer + choices + context as if you encountered it without context, quoted in a screenshot.
2. Ask the test question: would the author be embarrassed?
3. If yes, note **which** failure mode caught it.
4. If no, pass.

## Output format

```json
{
  "validator": "viral_check",
  "sample_size": 30,
  "results": [
    {
      "candidate_idx": 12,
      "verdict": "flagged",
      "concern": "Distractor reads as mockery of a religious tradition: 'a primitive sky-god myth' is not a real position any practitioner would defend.",
      "section_violated": "moral_vision.md §3 'No smug-atheist voice' + §4 'no strawmen of any position'"
    }
  ],
  "n_flagged": 1,
  "summary": "1 of 30 questions flagged. Pattern: smug-atheist voice in a theology-adjacent question. Recommend rewrite or discard. Bank otherwise passes the viral test."
}
```

## Reminders

- A serious Hayek question on the calculation problem PASSES this test even though it has a clear ideological valence. Substantive position = fine.
- A serious Marx question on alienation PASSES too. Same standard.
- A "did you know socialism is bad?" question FAILS regardless of any factual content. Flame-bait = fail.
- A "religious people couldn't possibly believe X" distractor FAILS. Strawman = fail.
- Use your judgment. If you flag something, name the specific failure mode from §3, §4, §5, or §7 of moral_vision.md.
