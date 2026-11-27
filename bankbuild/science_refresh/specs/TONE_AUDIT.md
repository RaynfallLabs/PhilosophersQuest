# Science refresh: the tone audit (whole bank, read-only on the questions)

You review finished units of Philosopher's Quest's new science bank the way a careful parent would. The game is played by teenagers, and the bank runs from 5th grade (T1) to 9th grade (T5).

Read each unit's `bankbuild/science_refresh/units/<id>/final.json` (the questions: stem, answer, choices, context) and its `card.json` (the teaching card: `context_blurb`).

**What is fine, and expected:**
- Real science stated plainly in the third person:
  - disease, germs and the body's defences;
  - a death in the history of medicine, and the dangers of radiation;
  - animal experiments of the past;
  - nuclear fission;
  - extinction and predators;
  - volcanoes, hurricanes and earthquakes.
- At T4-T5 only, the honest dark chapters of science (the Radium Girls, thalidomide, Tuskegee, eugenics, Lysenko) and the stance units' record. These must be told plainly, with one clause of harm and no gore.
- Mild blood and plain body words are fine for this audience.

**Flag only a genuine problem with the wording or tone:**
1. **Gratuitously graphic wording.** Wording that lingers on injury, gore, agony or remains beyond what the fact needs. Would a parent wince at the WORDING, not at the fact? (medium; high if it is nightmarish for a kid)
2. **Suffering as entertainment.** Harm to people or animals staged as a fun "did you know", a glib or smug voice about real suffering, or a choice set that makes a kid weigh deaths for a point. (medium; high for mass death treated lightly)
3. **Condescension.**
   - A sneer at people of the past for not knowing what we know now ("people used to foolishly think...").
   - A sneer at a culture, a faith or a group.
   - Scare quotes around a belief.
   - A smug voice toward the people on either side of a contested question.
   (medium)
4. **Kid-appropriateness.**
   - Anything sexual.
   - Human reproduction beyond a clinical cell-level fact (this bank leaves it out).
   - Crude content.
   - Gross-out detail for its own sake.
   - Content likely to frighten a child out of proportion to the lesson.
   (medium; high if sexual)
5. **Disturbing out of context.** The deck is shuffled. A stem read cold should not land as menacing toward the reader or creepy. (low or medium)
6. **Stance where it does not belong.**
   - A T1-T3 unit, or a T4-T5 unit not tagged for it, that preaches or takes a side on a contested public question (vaccines, climate policy, COVID, politics).
   - In any unit, an alarmed or sermonising voice in the bank's own words.
   - Banned words: "anti-vaxxer", "denier", "conspiracy theorist" as the bank's label.
   (medium; high for a banned word)

**When unsure, do not flag. Most units are clean.**

**Output.** Write `bankbuild/science_refresh/units/<id>/tone.json` for every unit you were given:
```json
{"unit": "<id>", "verdict": "clean" | "flag",
 "flags": [{"where": "<10-hex stem hash, or 'card'>", "rule": 1-6,
            "severity": "low|medium|high", "what": "<the words>",
            "fix": "<new wording, exact>"}]}
```
- A stem's hash is the first 10 hex characters of the SHA-1 of the stripped stem (UTF-8).
- `verdict` is "flag" if any flag is medium or high.
- Give an exact replacement phrase for each flag, so the lead can apply it.
- Do not edit any other file.
