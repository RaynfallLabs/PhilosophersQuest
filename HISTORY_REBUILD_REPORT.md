# History Bank Rebuild — COMPLETE

**Status: DONE — all 777 register topics rebuilt.**

## Final result
- **`data/questions/history.json` = 5,356 questions across all 777 topics** — about **5× your original** (1,049).
- **Zero invalid** (every answer matches one of its 4 choices; 4 choices each; every fact web-sourced and judged). **Manifest: 777/777 `passed`, 0 error, 0 needs_review.**
- **Tier spread:** T1 291 · T2 1,246 · T3 1,454 · T4 1,430 · T5 935 (T1–T2 ≈ 29%).
- Your original is backed up at **`data/questions/history_pre_v2_backup.json`** (gitignored). To revert: copy it back over `history.json`.
- Per-topic checkpoints in `bankbuild/history/ladders/<topic>.json` (777 files); rebuildable manifest via `python bankbuild/bank.py status`.

## How it was built
Per-topic pipeline (`bankbuild/history_pipeline.wf.js`), one topic at a time, fully checkpointed:
**research** (web-sourced, anti-hallucination) → **author** (all 14 craft rules + the Wonder Pattern + a 5-point self-audit) → **craft-judge** (rules + per-rung severity + fact-check vs sources) → **revise-until-clean** (cap 3; passes only with zero high/medium telegraphs, ≤2 low notes; anything rougher parked, never shipped dirty).

Run across multiple session-quota windows: I drove the lower topics live while the every-2-hours `history-bank-resume` schedule drove the upper topics during my quota pauses. Both used the identical harness and bar.

## Rules learned and integrated mid-run (your "pause, integrate, resume")
Author self-audit + severity pass-bar (the unblocker) · distractor-category match (the #1 telegraph) · effect/goal-match telegraph · Drama-Available auto-HIGH · tier-balance nudge toward a real T1–T2 base · retry-with-backoff for server throttling · never run concurrent batches. All saved to memory and committed (`fb0a391`, `3374e57`, `2229bd3`).

## Honest caveats
1. **I did not human-spot-check the upper ~half in-stream** — topics ~383–776 were driven by the background schedule through the same judge, which passed them, but I didn't eyeball each as it landed. Worth sampling a handful (open the file, read a few ladders) before you lean on it. (Six ancient-block topics — 375–380: Sumerian inventions, the Nile, Hieroglyphics, Salamis, the Peloponnesian War, Pythagoras — had failed the judge in an earlier window and were recovered on the final run; all six now pass.)
2. **Recurring low/medium tells:** a minority of rungs carry a noted "answer is the longest/only-elaborated choice" or "stem pre-states the goal" tell. They cleared the ≤2-medium bar but are worth a future polish pass if you want it pristine. (Notes live alongside each topic if we want to hunt them.)
3. **Data layer verified; not play-tested in Pygame from here** — load the game and try some history actions to confirm it feels right live.

## Release
The rebuilt `history.json` is **held out of git** (gitignored) per the plan — it's ready to ship as the **x.y.0** release whenever you want to cut it (version bump + un-ignore + commit + installer). Say the word and I'll prep that.
