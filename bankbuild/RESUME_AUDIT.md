# Autonomous resume — full-bank AUDIT grind (history)

You are resuming an automated, checkpointed full-bank audit of the Philosopher's Quest history bank.
Be autonomous — do NOT ask questions. Working dir: `C:\Users\brand\Documents\PhilosophersQuest`.

## State
- `bankbuild/history/_audit_all.json` — all 5,356 rungs (each has a stable `rid`), indexed 0..5355.
- `bankbuild/history/_audit_results.json` — accumulated craft + fact verdicts, keyed by rid.
- `bankbuild/history/_audit_runstate.json` — `{next_start, window (300), total: 5356, in_flight}`.
- Harness: `bankbuild/history_audit_full.wf.js` (the Workflow) + `bankbuild/audit.py`.

## STEP 1 — done?
`python bankbuild/audit.py status`. If craft audited is ~100% (>= 5356) AND `audit.py gaps` reports
0 missing fact (no remaining ranges), the AUDIT is COMPLETE: **STOP and do nothing further** — leave a
note that the audit is done and the FIX phase is for a human session (judgment + iteration). Don't fix.

## STEP 2 — concurrency lock
Read `_audit_runstate.json` `in_flight`. If non-empty AND its `ts` is within the last 45 minutes,
another driver is active — exit quietly.

## STEP 3 — forward sweep, then reconcile gaps

### Phase A — forward sweep (while next_start < 5356)
1. Stamp `in_flight = [{start: next_start, count: 300, ts: <date +%s>}]`.
2. Launch: `Workflow {scriptPath:"bankbuild/history_audit_full.wf.js", args:{start: next_start, count: 300}}`.
3. On completion: `python bankbuild/audit.py integrate "<task output file>"`, then `audit.py status`.
   - The craft phase runs first and fully; the fact phase is heavier and may wall mid-window.
   - **Advance only by craft coverage**: if `craft audited >= next_start + 300`, set
     `next_start = min(next_start + 300, 5356)` (the window's craft is complete; any fact gap is
     swept in Phase B). If craft is NOT fully covered (a rare mid-craft wall), leave `next_start`.
   - Clear `in_flight`.
4. **Quota wall**: if the task's failures contain "session limit"/"hit your ... limit", STOP this run
   (apply the advance decision above first, so a craft-complete window still moves the cursor).
   The next scheduled run continues. Transient "rate limited"/"Overloaded" are absorbed by retry —
   don't stop for those. Loop to STEP 1.

### Phase B — reconcile gaps (once next_start has reached 5356)
1. `python bankbuild/audit.py gaps` → JSON list of `{start, count}` ranges missing craft OR fact.
2. For the FIRST range, stamp `in_flight` and launch the same Workflow with that `{start, count}`
   (integrate is idempotent — already-covered rungs in the range are just refreshed). Integrate,
   clear `in_flight`. Stop on a quota wall as in A4; else loop to STEP 1.
3. When `gaps` reports 0 missing fact, the sweep is COMPLETE → STEP 1 stops it.

Keep window=300 in Phase A. This is audit-only; it changes no bank content.
