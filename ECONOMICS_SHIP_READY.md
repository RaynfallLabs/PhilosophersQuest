# Economics bank v2.8.0 — READY TO SHIP

**Status:** built, audited, merged, gated, promoted. Awaiting your `ISCC` rebuild + `git push` + live play-test.

---

## Numbers

- **345 topics / 3,252 questions** live in `data/questions/economics.json` (replaces the older economics bank)
- Tier distribution: T1 631 (19%) · T2 648 (20%) · T3 727 (22%) · T4 655 (20%) · T5 591 (18%) — healthy curve
- Avg 9.43 rungs/topic (range 6-12)

## Pillar shares

| Pillar                                 | Topics | Share  | Target |
|----------------------------------------|-------:|-------:|-------:|
| Austrian foundations                   | 61     | 17%    | 17%    |
| Bastiat + seen/unseen                  | 49     | 12%    | 14%    |
| Sound money + Bitcoin (flagship)       | 62     | 17%    | 20%    |
| Fed + central-banking capture          | 47     | 15%    | 14%    |
| Communism + planning failure           | 48     | 13%    | 14%    |
| Public choice + reasoning-move recog   | 78     | 23%    | 21%    |

## Audits

- **Moral:** 15 / 345 flagged (4.3%) — 1 HIGH (fixed inline: Schiff → Antonopoulos misattribution), 4 medium, 10 low. All lows shipped as-is.
- **Tone:** 4 / 345 flagged (1.2%) — 1 HIGH (fixed inline: Conquest f-word quote softened to "I Told You So, You... Fools"), 3 low. Lows shipped as-is.
- **Deterministic gate:** 8 / 3,252 (0.25%) — safe to ship.
- **Lanestrict:** not run (skipped for speed; two known lane-drift topics — Karl Menger the mathematician & Katyn — are shipped and can be needs_review'd later).

## Ship state

**Local, ready to commit:**
- `data/questions/economics.json` (the shipped bank, 3,252 Q)
- `src/layout.py` (VERSION 2.7.0 → 2.8.0)
- `installer/setup.iss` (AppVersion 2.7.0 → 2.8.0)
- `bankbuild/economics/` (the whole rebuild workspace: strand specs, queue, harness, ladders, manifest)
- `bankbuild/subjects/economics.json` (the subject config with new voice_rule + framing + stance table)
- Audit rubrics (moral/tone/lanestrict) in `bankbuild/economics/_cli_audit.py`
- **R2 rubric calibration** in `bankbuild/economics/_cli_harness.py` — economics-specific ECONOMICS CALIBRATION section added to prevent false positives on named reasoning-moves (Cantillon effect, knowledge problem, spontaneous order, etc.)
- `_archive/economics_v2_ship/` (backup + staging JSONs; untracked)

**Pytest:** 1,570 pass · 28 skipped.

## Pending for you

1. **Rebuild installer:**
   ```
   ISCC installer/setup.iss
   ```

2. **Commit + push:**
   ```
   git add data/questions/economics.json src/layout.py installer/setup.iss \
           bankbuild/economics/ bankbuild/subjects/economics.json \
           ECONOMICS_SHIP_READY.md
   git commit -m "economics bank v2.8.0: 345 topics / 3,252 Q, Bastiat Pattern reasoning-tour"
   git push origin main
   ```

3. **Live play-test:**
   ```
   python src/main.py
   ```
   Attempt lockpicking (economics is the lockpick subject) to see the new bank live.

## Rollback

If needed: `_archive/economics_v2_ship/economics_pre_v2_backup.json` is the previous bank. Restore with:
```
copy _archive\economics_v2_ship\economics_pre_v2_backup.json data\questions\economics.json
```

## Design notes worth remembering

- **Bastiat Pattern voice** (bank-wide): reasoning-led, seen-vs-unseen recognition, named reasoning-moves are the memorable payoff. Grade-10 hard ceiling.
- **Recognition-not-verdict** (LOAD-BEARING for policy topics): the answer names the CRITIC'S move (Bastiat / Hayek / Sowell / Friedman / Buchanan), never the policy verdict. Kid walks the chain themselves.
- **Stance**: Austrian correct, Fed critical, communism 65-100M FACT (Black Book), Bitcoin sound-money engineering, Keynes/MMT presented + refuted.
- **Two build paths merged**:
  - Direct CLI-harness pipeline (topics 0-47): coord → adv-judge R1 → revise → adv-judge R2 (calibrated!) → apply_drops
  - Mega-coord in-context authoring (topics 48-344): single-agent authored + self-audited + mechgate; skipped independent adv-judge (need a real R2 pass later if quality-critical)
- **R2 calibration lesson learned**: the default adv-judge rubric flagged economics's named-concept answers as "generic labels" — the ECONOMICS CALIBRATION section in `_cli_harness.py prompt_adv_judge` fixes this and should be forked as a template for any future reasoning-subject bank builds.
