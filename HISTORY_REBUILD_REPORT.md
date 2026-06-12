# History Bank Rebuild — Report

**Status: MILESTONE REACHED — 161 topics live, throttle-capped on the long tail.**

## What's live right now
- **`data/questions/history.json` = 2,055 questions across 161 topics** — roughly **2× your original** (1,049), every question freshly web-sourced and run through the 14-rule craft judge + fact-check.
- Your original is backed up at **`data/questions/history_pre_v2_backup.json`**. To revert: copy it back over `history.json`.
- **Data layer verified:** 0 invalid (every answer matches one of its 4 choices; 4 choices each; sourced).
- **Tier balance:** T1 123 · T2 453 · T3 559 · T4 530 · T5 390 (T1–T2 = 28%).

## What's covered (the highest-priority ~21% of the register)
The queue was priority-ordered (high-weight, deep, vision-mandated first), so the 161 done are the topics that matter most: the ancient world (Mesopotamia, Egypt, Greece — Marathon, Thermopylae, Salamis, Socrates — Rome), the Hebrews and early Islam, the great world civilizations (Aztec, Inca, Mali, Great Zimbabwe), medieval Europe and the Gothic cathedrals, the Renaissance and Reformation, and into the American founding and Civil War (Jefferson, Gettysburg, Pickett's Charge). These are full 12–14 rung wonder ladders.

## Why it stopped here (honest)
1. **Session usage limit** — I hit it overnight (reset 3:30am PT). Recovered after reset.
2. **Heavy intermittent server throttling** — from ~topic 147 on, each forward batch loses ~25% of its research agents to "Server is temporarily limiting requests." They recover on re-run, but it makes the long tail slow and token-expensive.
3. A **bug I introduced** (`blocking`→`toFix`) crashed revise-failures under the throttling — **fixed**.

The remaining ~611 topics (idx 167–776) are the **lower-priority** medium/low-weight tail. Finishing them is entirely doable but is now fighting the throttle for diminishing-priority content.

## Pending (5 topics)
`needs_review`: idx **147, 148, 153, 162, 165** — rate-limit casualties that kept missing throttle windows (not quality failures). They re-run clean in a calmer window.

## How to finish the rest later (trivially resumable)
The harness checkpoints everything; nothing is redone.
- Re-run the 5 stragglers: `Workflow {scriptPath: bankbuild/history_pipeline.wf.js, args:{idxs:[147,148,153,162,165]}}`
- Continue the tail: `Workflow {... args:{start:167, count:20}}` — then `python bankbuild/bank.py integrate <output>; merge; promote`.
- Dashboard: `python bankbuild/bank.py status`. Cursor/state in `bankbuild/history/_runstate.json`.

## Rules learned & integrated overnight (also saved to memory)
Author self-audit + severity pass-bar (the unblocker); distractor-category-match (the #1 telegraph); Drama-Available auto-HIGH; tier-balance nudge; never run concurrent batches (it throttles).

## Caveat
Data layer is verified, but I **cannot play-test Pygame** from here — load the game and try a few history actions (accessory equipping) to confirm it feels right in a live session.
