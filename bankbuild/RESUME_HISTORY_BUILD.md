# Autonomous resume — Philosopher's Quest HISTORY bank rebuild

You are resuming an automated, fully-checkpointed history-bank rebuild. Be autonomous — do NOT ask
questions. Working directory: `C:\Users\brand\Documents\PhilosophersQuest`.

## State (durable; survives any reset)
- `bankbuild/history/_runstate.json` — `{next_start, batch_size (8), needs_rerun_idxs, total_topics: 777, in_flight}`
- `bankbuild/history/manifest.json` — per-topic status (passed / needs_review / error)
- Harness: `bankbuild/history_pipeline.wf.js` (the Workflow) + `bankbuild/bank.py`

## STEP 1 — are we DONE?
Run `python bankbuild/bank.py status`. If every one of the 777 topics is `passed`, the build is COMPLETE:
1. `python bankbuild/bank.py merge` then `python bankbuild/bank.py promote`
2. Refresh `HISTORY_REBUILD_REPORT.md` with the final numbers.
3. DELETE this recurring schedule (it has finished) — list the scheduled routines and remove `history-bank-resume`.
4. Report completion. STOP.

## STEP 2 — concurrency lock (never double-drive)
Read `_runstate.json` `in_flight`. If it is non-empty AND its `ts` is within the last **45 minutes**,
another driver is already running — exit quietly without launching anything. Otherwise continue.

## STEP 3 — the loop (ONE batch at a time — NEVER two concurrent; concurrency throttles the server)
1. Choose the batch:
   - If `needs_rerun_idxs` is non-empty → `args = {idxs: needs_rerun_idxs}`
   - Else → `args = {start: next_start, count: 8}`
2. Stamp the lock: set `_runstate.in_flight = [{ "range": <desc>, "ts": <epoch seconds from `date +%s`> }]`.
3. Launch: `Workflow {scriptPath: "bankbuild/history_pipeline.wf.js", args: <above>}`.
4. On the completion notification:
   - `python bankbuild/bank.py integrate "<task output file path from the notification>"`
   - `python bankbuild/bank.py merge` ; `python bankbuild/bank.py promote`
   - Recompute `needs_rerun_idxs` = manifest idxs with status != passed AND idx < next_start. If this
     was a forward batch, `next_start += 8`. Set `in_flight = []`.
5. Go back to STEP 1.

## STOP CONDITION for one scheduled run
If a batch's failures contain **"session limit"** / **"hit your ... limit"** (the quota wall), STOP this
run: clear `in_flight`, leave state for the next scheduled run to pick up. (The retry-with-backoff in the
pipeline already absorbs transient "rate limited" / "Overloaded" — do NOT stop for those.)

## Rules
- `batch_size = 8`, single batch at a time. Promote every batch (live `history.json` grows).
- Do **NOT** git-commit `data/questions/history.json` — it is held for the x.y.0 release.
- The new bank lives only in the working tree + `bankbuild/history/ladders/` checkpoints (both safe).
