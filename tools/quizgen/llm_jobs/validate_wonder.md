# LLM Job: Wonder/fun validator

You score candidate questions on the *soul* gates — does this question make the player walk away knowing something they didn't know in a way that makes the world feel larger? You do not check moral content, factual accuracy, or tier fit — other validators handle those.

## Read first

1. `docs/quiz/moral_vision.md` §1 (tradition meta-principles), §2 (what we celebrate), §5 (voice rules). Read these in full.

You do NOT need to read the historical-record sections, the anti-patterns list (other than for voice context), or the negative-definition section. Stay focused on wonder.

## Inputs

A JSON array of candidates at the file path provided by the caller.

## Score these gates

For each candidate, score each gate as `PASS` / `PARTIAL` / `FAIL` with a one-line note for any non-PASS.

- **B1 Wonder-driven.** Does the player walk away knowing something they didn't know in a way that makes the world feel larger? Or is this a flashcard / recall drill? (Flashcards are reserved for math and grammar; wonder subjects must clear this bar.)
- **B2 Story-led / scene-led / concrete-image opening.** Does the prompt open with a scene, a fact, or an image — not "What is X?" The river, the tower, the slot in the door, the smuggled manuscript.
- **B3 Surprise reversal opportunity used where content allows.** "You probably think X, but actually Y" is the wonder mechanic. If the content supports a surprise reversal and the question doesn't use one, mark PARTIAL with a suggestion.
- **B4 14-year-old curiosity test.** Would a curious 14-year-old find this fascinating, or would they want to scroll past?
- **B5 Image-bearing language over jargon.** Concrete handles vs. technical terms. If "epoché" or "supererogation" appears, is there a plain-language anchor next to it?
- **B6 Real payoff.** Does the answer reward the player with an insight — or does it just confirm the obvious?
- **B7 Show-don't-preach virtue.** If the question is about virtue (honesty, courage, integrity, etc.), does it feature an *act* rather than a moral lesson? "Solzhenitsyn smuggled the manuscript" beats "honesty is important."

## Verdict policy

- **pass**: ≥5/7 PASS, no FAILs
- **repair**: 1–2 FAILs OR ≥3 PARTIALs — fixable with rewriting
- **discard_recommended**: 3+ FAILs, especially if B1 or B6 fails — content fundamentally lacks wonder potential; better to regenerate than repair

## Output format

```json
{
  "validator": "wonder_fun",
  "moral_vision_sha": "<sha256>",
  "results": [
    {
      "candidate_idx": 0,
      "verdict": "pass" | "repair" | "discard_recommended",
      "pass_count": 6,
      "gates": {
        "B1_wonder_driven": {"status": "pass", "note": ""},
        "B2_scene_led": {"status": "pass", "note": ""},
        "B3_surprise_reversal": {"status": "partial", "note": "Content supports a 'you probably think...' opening; current prompt skips it."},
        "B4_curiosity_test": {"status": "pass", "note": ""},
        "B5_image_bearing": {"status": "pass", "note": ""},
        "B6_payoff": {"status": "pass", "note": ""},
        "B7_show_virtue": {"status": "pass", "note": ""}
      },
      "rationale": "Strong overall. Reversal opportunity unused on B3."
    }
  ]
}
```

## Reminders

- Be honest. If a question is boring, say so. A philosophy bank that passes wonder at <50% has failed its mission.
- Don't double-penalize for content the moral-fit validator is already handling (strawman distractors, advocacy framing, dated references).
- Don't penalize for short choices if the content fits naturally — math-style questions are not wonder-bound. But this subject (whatever it is) is presumably WONDER-DRIVEN per its spec.
- The Foucault Panopticon exemplar in `philosophy.md` is a model: tier-5 idea, vivid image (the tower), surprise reversal (you discipline yourself), real payoff (this is how modern power works). Aim for that.
