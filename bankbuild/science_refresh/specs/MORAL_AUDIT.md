# Science refresh: the moral audit (stance and method units, read-only on the questions)

You are an independent reviewer of the stance in Philosopher's Quest's new science bank (T1 = 5th grade ... T5 = 9th).

Read first:
- `docs/quiz/moral_vision.md` §3.10 (stance versus neutral: the no-verdict rule is NOT uniform) and §5 (show, don't preach);
- `bankbuild/subjects/science.json` "framing" (the bank's lean);
- `bankbuild/science_refresh/units.json`: each unit's `framing_note`, the 9th-grade version of the framing, which governs the tone.

For each unit you are given, read `units/<id>/final.json` (stem, answer, choices, context) and `units/<id>/card.json` (`context_blurb`).

**Score each question and each card in BOTH directions.**

1. **Imposed verdict.** The bank's own voice states a contested claim or a judgement as fact, where it should attribute it to a named person or body, with the year. Watch especially:
   - how much of the warming is human-caused, and the harm ahead;
   - the lockdowns' worth;
   - the origin of the virus;
   - vaccine safety beyond the documented record.
   (medium; high if the key itself is the unattributed verdict)
2. **Neutral where the bank leans.** The framing celebrates the method and honours dissent. It covers the institution honestly and tells the dark chapters as the standing warning. Vaccines are scrutinized, not celebrated.
   - Flag a question or card that turns these into false balance: it presents the documented record as merely "one view", hides the dark chapter, or sides with the institution against the documented record.
   - Flag a settled fact given false balance the other way (evolution, the greenhouse physics, the warming itself, germ theory, the vaccine mechanism, smallpox eradicated).
   (medium)
3. **Strawman or cartoon.** Either side is shown without its real reasons: the officials in an emergency, the mainstream assessment, the doubters of the day. Flag a villain painted with no reason, or a hagiography. (medium)
4. **Preaching or smug voice.** A sermon, an "and that is why we must...", alarm in the bank's own words, mockery of either side, or a banned word: "anti-vaxxer", "denier", "conspiracy theorist" as the bank's label, or "misinformation" as the bank's own verdict. (medium; high for a banned word)
5. **Answer not defensible on the record.** The key is right only if one takes a side on a live dispute, or a wrong choice is merely the other school rather than wrong on the record. Also flag a figure or a quote that looks unsourced or misquoted. (high)
6. **Lane drift.** The real payload is politics, a court case or a party, not the science, the evidence or the method. (low or medium)
7. **Pathogen detail.** Any genome, engineering or technique detail. (high)

Do not flag settled science stated flatly, documented facts stated with their source, or attributed claims. When unsure, do not flag.

**Output.** Write `bankbuild/science_refresh/units/<id>/moral.json` for every unit you were given:
```json
{"unit": "<id>", "verdict": "clean" | "flag",
 "flags": [{"where": "<10-hex stem hash, or 'card'>", "rule": 1-7,
            "severity": "low|medium|high", "what": "<the words>",
            "fix": "<new wording, exact>"}]}
```
- A stem's hash is the first 10 hex characters of the SHA-1 of the stripped stem (UTF-8).
- `verdict` is "flag" if any flag is medium or high.
- Give an exact replacement phrase for each flag, so the lead can apply it.
- Do not edit any other file.
