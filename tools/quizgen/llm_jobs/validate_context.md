# LLM Job: Context-paragraph validator

The `context` field on each question is what the player sees *after* answering — the wonder-payoff, the explanation, the "huh, I didn't know that" follow-through. You score whether the context is doing its job.

## Inputs

A JSON array of candidates at the file path provided by the caller. You read only the `context` field for each (in relation to its question/answer).

## What you score

- **C1 Adds wonder beyond the question.** Does it teach something *more*, not just paraphrase the answer?
- **C2 Factually accurate.** Same fact-check standard as `validate_facts.md`, applied to the context.
- **C3 Same voice as the question.** Warm but precise; concrete; not preachy; no smug atheist/believer voice; no dated references.
- **C4 Right length.** 1–3 sentences typical. Not a wall of text. Player reads this in 2–3 seconds.
- **C5 Coherent with the answer.** The context should flow from the answer; it should not introduce contradictions or imply the answer is incomplete.

## Output format

```json
{
  "validator": "context_quality",
  "results": [
    {
      "candidate_idx": 0,
      "verdict": "pass" | "repair" | "discard",
      "gates": {
        "C1_adds_wonder": {"status": "pass", "note": ""},
        "C2_accurate": {"status": "pass", "note": ""},
        "C3_voice": {"status": "pass", "note": ""},
        "C4_length": {"status": "pass", "note": ""},
        "C5_coherent": {"status": "pass", "note": ""}
      }
    }
  ]
}
```

## Reminders

- Many existing-bank context paragraphs are decent. Don't be too harsh on length variation.
- C1 is the load-bearing gate. A context that just paraphrases the answer is missing the wonder payoff.
- If C2 fails, treat like a fact-check fail (discard, no repair).
