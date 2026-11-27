# Science refresh: the pick of 200 a tier (whole bank, read-only on the questions)

Each tier of Philosopher's Quest's new science bank was written about 5-15% over its 200, so that this pick keeps the best 200. You choose which questions of ONE tier to leave out. You do not rewrite anything.

**Read:**
- `bankbuild/science_refresh/config.json`: `tiers` (what a tier asks), `strands`, `strand_targets_final`.
- The tier's units in `bankbuild/science_refresh/units.json`.
- For each of those units, `units/<id>/final.json` (the questions) and `units/<id>/judge.json` (the judge's view of the draft: useful, but the final may already have fixed it).

The brief tells you how many questions to leave out in each strand. They come from the targets.

**How to choose, in order:**
1. **Overlaps.** Two questions in the tier, or one here and one in a lower tier, that teach the same fact. Leave out the weaker one. Grep `units/*/final.json` for the lower tiers.
2. **Grade fit.** A question whose fact is clearly above or below the tier's grade.
3. **Weak questions.** A wrong choice that is not plausible to a student of the grade, a clue in the stem, or a clumsy or unclear stem.
4. **Least interesting.** Among questions that are all sound, leave out the ones a student would find the dullest, or the least worth knowing at that grade.

Keep every unit at no fewer than 6 questions: a card has to teach a unit, and a unit of 4 is thin. Spread the cuts over the units rather than hollowing one out, unless rule 1 or 2 calls for it.

**Output.** Write `bankbuild/science_refresh/pick_T<n>.json`:
```json
{"tier": <n>, "drop": {"<10-hex stem hash>": "<unit id>: <one-line reason>"}}
```
- The hash is the first 10 hex characters of the SHA-1 of the stripped stem (UTF-8). Compute it with Python; never guess it.
- Check that the counts per strand match the brief exactly before you finish.
- Do not edit any other file.
