# LLM Job: Tier-fit validator

You judge whether a candidate question fits its claimed tier. The per-subject spec (`docs/quiz/subjects/{subject}.md`) defines what each tier should look like in this subject.

## Read first

1. `docs/quiz/subjects/{subject}.md` — the per-subject spec for whichever subject the candidates belong to. Sections 1 (timing budget), 2 (per-tier WIS + parse budgets), 3 (per-tier content profile), 4 (north-star exemplars per tier).

You do NOT need to read `moral_vision.md` — moral fit is handled separately.

## Inputs

A JSON array of candidates at the file path provided by the caller.

## What you score

For each candidate:

1. Read the candidate's claimed tier (`tier` field).
2. Read the spec's content profile for that tier (Section 3 in the per-subject spec).
3. Compare. Does the content match what that tier should be?
4. If not: what tier would it actually fit? (Estimate 1–5.)
5. Score: PASS if the candidate fits its claimed tier ±0.5; PARTIAL if ±1; FAIL otherwise.

Common mis-fits:
- **T1 content tagged T3+** — too accessible for the tier label. Recall-bait dressed as deep philosophy.
- **T2 content tagged T4+** — famous idea, framed simply, doesn't earn the tier. (E.g. "Descartes said cogito ergo sum, what did he mean?" tagged T4 — that's a T2 question.)
- **T4 content tagged T2** — heavy jargon or technical-move-via-consequence presented to an audience expected to handle only famous-ideas-with-surprise. Player will choke.
- **T5 content tagged T3** — sophisticated dispute or contested position dressed down to look easier than it is. May still be a good question but tier should be raised.

## Output format

```json
{
  "validator": "tier_fit",
  "subject_spec_sha": "<sha256 of the per-subject spec>",
  "results": [
    {
      "candidate_idx": 0,
      "claimed_tier": 4,
      "estimated_tier": 2,
      "fit_score": "fail",
      "rationale": "Question is 'Descartes said cogito ergo sum; what did he mean?' This is famous-idea-recall, not a technical-move-via-consequence. T2 at most.",
      "suggested_action": "Either reclassify as T2, OR rewrite to push to T4 (e.g., focus on the dream argument's implications for the cogito's certainty)."
    }
  ]
}
```

## Verdict policy

- **PASS** (`fit_score: "pass"`) — fits claimed tier
- **PARTIAL** (`fit_score: "partial"`) — off by 1 tier; can reclassify or repair
- **FAIL** (`fit_score: "fail"`) — off by 2+ tiers; should be reclassified or rewritten before validation continues

## Reminders

- The four exemplars per tier in the spec are your calibration anchors. Match candidates against those exemplars' difficulty level.
- WIS scaling in the game means tier-5 players have more reading time, so tier-5 content can be denser. But difficulty != density. A tier-5 question should require sophisticated philosophical reasoning, not just more words.
- If a candidate is great content but tagged wrong, recommend reclassification rather than rejection. The pipeline can re-route it to the correct tier's pool.
