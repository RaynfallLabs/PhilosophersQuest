# Economics v2.8.0 — post-ship R2 audit results

Run 2026-09-05 after the shipped v2.8.0 build. Purpose: catch what the mega-coord in-context self-audit missed on topics 48-344 (297 topics that shipped without a fresh independent adversarial audit).

## Aggregate

- **297 audited** (idx 48-344)
- **0 HIGH flags** — no factual errors, no dead-name answers, no restatement leaks, no unsourced facts caught
- **5 medium flags** — worth fixing inline
- **~140 low flags** — dominated by two systematic mega-coord author habits (below); NOT worth applying-drops on, as the fix would harm the ladders more than leaving the flag

## Medium flags — worth fixing before v2.8.1

| idx | topic | flaw | fix suggestion |
|----:|:------|:-----|:---------------|
| 49  | Sowell (T3 stage-two) | Rung 7's answer is telegraphed by "stage-one" phrase in stem | Reword T3 rung 7 stem to describe stage-two abstractly without echoing stage-one anchor |
| 58  | 2008 GFC / TARP | Rung 7 pairs TARP+SVB using only the ladder's own topics as distractor material | Replace 3 distractors with parallel bank-rescue pairs from other eras (Continental 1984, Bear Stearns 2008, First Republic 2023) |
| 59  | Smoot-Hawley 1930 | Same-fact repeat: rungs 4 and 6 both key "Smoot-Hawley Tariff Act" | Re-key rung 6 to a different Smoot-Hawley detail (world trade collapse %, retaliation pattern, or Willis Hawley/Reed Smoot Congressional roles) |
| 171 | Solzhenitsyn / Gulag | Rung 9 keys Conquest's f-word quote (documented but inappropriate for kids) | Same fix I already applied to `the-soviet-gulag-solzhenitsyns-accounting.json`: soften "Fucking Fools" -> "... Fools" with an editorial-softening note in context |
| 343 | (idx 343 topic) | Rung 2 answer is 3.5x longest distractor + logical-telegraph leak | Trim the answer's clarifying clause; make distractors match its structure |
| 344 | (idx 344 topic) | Rung 4 answer is 3.1x longest distractor; two joke-adjacent distractors | Trim answer; replace joke distractors with plausibly-wrong parallel wrongs |

## Low flags — DO NOT apply_drops

- ~117 low flags in the 48-146 range are TOPIC-NAME MATCH on T1 anchor rungs (mega-coord authored the T1 answer as the topic-title term). Running apply_drops would remove ~100 T1 anchors, leaving those topics without a foundational rung — WORSE outcome than leaving the flag.
- ~21 low flags in the 246-344 range are length-parity issues where mega-coord added pedagogical clauses to answers, making them longer than distractors. Same principle — trimming inline improves; dropping loses the rung.
- The remaining scattered lows are minor and are all shipped-safe.

## Recommendation

- Roll the 5-6 medium fixes into the next patch (v2.8.0.1) or into v2.8.1 alongside the Linux AppImage first-shipping.
- If a full quality-hardening pass is desired later, a targeted "REVISE (not drop) the low-flag T1s" agent pass could raise ~100 T1 rungs from OK to good. Not needed for ship.

## Data

Full verdicts JSON per topic at `bankbuild/economics/_cli_state/NNNN_verdicts_adv.json` (overwritten by this R2 pass; the earlier author-clean verdicts are gone). Not aggregated to a single file since it's a followup and not part of the ship pipeline.
