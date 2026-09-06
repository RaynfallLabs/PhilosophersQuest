# v2.9.0 — Grammar bank v2 + economics polish (READY TO SHIP)

**Status:** built, audited, merged, gated, promoted. Ready for `git tag v2.9.0 && git push origin v2.9.0` which triggers the CI to build both artifacts and publish to GitHub Releases.

## Grammar bank v2 — the headline

- **157 topics / 1,041 questions** live in `data/questions/grammar.json`
- Tier distribution: T1 218 (21%) · T2 234 (22%) · T3 225 (22%) · T4 177 (17%) · T5 187 (18%) — healthy T1/T2-heavy curve appropriate for snappy-rote
- Avg 6.63 rungs/topic (range 5-9); intentionally shorter than reasoning banks

## Pillar shares (target vs actual)

| Pillar                                 | Topics | Share  | Target |
|----------------------------------------|-------:|-------:|-------:|
| Punctuation                            | 41     | 22%    | 25%    |
| Homophones + confusables               | 32     | 20%    | 20%    |
| Agreement                              | 22     | 15%    | 15%    |
| Sentence structure                     | 22     | 16%    | 15%    |
| Usage + register                       | 23     | 14%    | 15%    |
| Wordplay + etymology + advanced        | 17     | 10%    | 10%    |

## Voice

**Comma-Saves-Lives Pattern** — the wrong version is the punchline. Answer hierarchy:
1. PUNCHLINE-VIA-MISUSE ("Let's eat, Grandma!" vs "Let's eat Grandma!") — highest
2. REGISTER / CLARITY CONTRAST
3. INFLECTIONAL / PARADIGM (lay/lie, who/whom)
4. CATEGORY NAMING (bottom, sparse above T3)

**Canonical corpus shipped as required exemplars:** vocative Grandma, Oxford strippers/JFK/Stalin, garden-path horse-raced-past-the-barn-fell (Bever 1970), buffalo construction, panda "Eats Shoots and Leaves" (Truss 2003), JFK chiasmus, time-flies pun.

**Zombie superstitions debunked with stance:** never-split-infinitives, Churchill preposition-ending, sentence-initial And/But, singular-they-is-wrong (all four VISION_MANDATED with citations — Chaucer/Shakespeare/Austen/Chicago 5.48/AP 2017/MW 2019).

## Audits

- **Moral:** 5 / 157 low (0 medium, 0 high) — recurring "'his' excludes half the class" framing on singular-they teaching topics; shipped as-is
- **Tone:** 1 / 157 low (semicolons-as-super-commas date list) — shipped as-is
- **Deterministic gate:** 0 / 1,041 (0%) — CLEANEST BANK YET (theology 4/2739, economics 8/3252)
- **Lanestrict:** skipped for speed (grammar vs vocab vs writing-composition; no known drift)

## Economics polish (also in v2.9.0)

Re-shipped 3,252 economics questions with 6 medium-severity fixes from the R2 audit pass:
1. idx 49 (Sowell stage-two) — reworded stem to remove "stage on..." telegraph
2. idx 58 (TARP+SVB pairs) — replaced ladder-internal distractor pairs with parallel bailout-pair sequences from Continental/Penn Central/Franklin National eras
3. idx 59 (Smoot-Hawley same-fact repeat) — re-keyed rung 6 to world-trade-collapse figure (~66% drop 1929-34)
4. idx 171 (Gulag Conquest f-word remnant in context) — softened "You... Fools" with editorial note
5. idx 343 (Hoff parity) — trimmed lone-long answer, matched distractor structure
6. idx 344 (Liberty Fund joke distractors) — replaced "Chinese translations" / "comic-book version" with plausibly-wrong scholarly alternatives

## Ship state

**Local, ready to commit:**
- `data/questions/grammar.json` (1,041 Q live, replacing the older grammar bank)
- `data/questions/economics.json` (3,252 Q re-promoted with 6 fixes)
- `src/layout.py` (VERSION 2.8.0 → 2.9.0)
- `installer/setup.iss` (AppVersion 2.8.0 → 2.9.0)
- `bankbuild/grammar/` (the whole rebuild workspace)
- `bankbuild/subjects/grammar.json` (config)
- Fixed ladder files in `bankbuild/economics/ladders/` (5 revised) + synced `_cli_state/`
- `tests/test_group_a_residuals.py` (grammar-quoted-phrase exception for uppercase-start rule)
- `_archive/grammar_v2_ship/` + `_archive/economics_v2_ship/` (backups; untracked)
- `ECONOMICS_R2_AUDIT_RESULTS.md` + `GRAMMAR_SHIP_READY.md` (handoff docs)

**Pytest:** 1,570 pass · 28 skipped.

## Pending for you

**Option A — trigger the CI (recommended, tests the workflow):**
```
git tag v2.9.0
git push origin v2.9.0
```
CI builds Windows Setup.exe + Linux AppImage in parallel, publishes as GitHub Release.

**Option B — manual local build (if CI hits a bug):**
```
ISCC installer/setup.iss   # builds Windows installer
git push origin main       # push commit (already made)
```

**Live play-test:**
```
python src/main.py
```
Read a scroll (grammar action) to see the new bank; lockpick a chest (economics) to confirm the 6 fixes.

## Rollback

- Grammar: `_archive/grammar_v2_ship/grammar_pre_v2_backup.json` (the previous grammar bank)
- Economics: `_archive/economics_v2_ship/economics_pre_v290_backup.json` (the v2.8.0 economics bank pre-fixes)
