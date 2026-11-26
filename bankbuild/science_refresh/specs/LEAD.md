# Science refresh: the lead's runbook for the full build

Brandon said yes on 2026-11-25, then "keep going with the build, run until
complete; ask any questions you need of me but don't pause work". This page
is for the lead (the session that schedules the agents). Re-read plan section
10 after any usage wall, restart or context summary, then this page.

## The loop
At most **3 agents at once**, all Opus (`model: "opus"`), all in the
background, none spawning others. When an agent finishes:
1. `py -m bankbuild.science_refresh.status --done <label>`.
2. Run the lead's script for the step it finished (below).
3. `py -m bankbuild.science_refresh.status`, then fill the free slots. Take
   the first rule that applies:
   1. **reader**: 2 card batches written and gated (up to 6 units), or the
      last ones at the tail.
   2. **card**: 3 units finalized (fewer at the tail).
   3. **recheck**: 3 units revised with changes (fewer at the tail).
   4. **revise**: 3 units judged and fact-checked (fewer at the tail).
   5. **judge**: 3 units authored (fewer at the tail).
   6. **factcheck**: 1 unit authored.
   7. **research**: the next unit in build order.
   "The tail" means no unit waits at an earlier step to join the batch.
4. Record each launch: `py -m bankbuild.science_refresh.status --launch <step> <ids> [--batch N]`.
5. Commit the finished units' files now and then (never `_cards/` or `_inflight.json`).

## The lead's scripts between steps
- After **research**: `py -m bankbuild.science_refresh.gates <id>`. A FAIL left
  over is fine: the reviser must fix gate FAILs.
- A unit whose judge and fact-check are `ok` on every question, with no
  gate FAIL, skips the reviser. The lead writes `final.json` with the draft's
  questions unchanged and empty `revised`, `added` and `dropped`, then runs
  `finalize`. `signs-of-a-chemical-change` was the first, on 2026-11-26.
- After **revise**: `py -m bankbuild.science_refresh.gates --kind final <ids>`.
  If a unit changed nothing (empty `revised` and `added`), it skips the re-check.
- After **recheck** (or for a unit with nothing changed):
  `py -m bankbuild.science_refresh.finalize <ids>`.
- Before **card**: `N=$(py -m bankbuild.science_refresh.status --next-batch)`, then
  `py -m bankbuild.science_refresh.cards packet N <ids>`. For each unit, add
  `"carded": {"batch": N}` to `state.json` after the writer finishes and
  `py -m bankbuild.cards.gate science N` passes.
- Before **reader**: `py -m bankbuild.cards.judge packet science N` for each batch.
- After **reader**: `py -m bankbuild.cards.judge score science N`, then
  `py -m bankbuild.science_refresh.cards save N`. If a card is not covered,
  send the reader's misses to its card writer (SendMessage), re-gate, then run
  `py -m bankbuild.cards.judge packet science N --only <topic>` and a fresh
  reader for that topic.

## Briefs (fill in the ids; the repo root is the worktree)
Every brief ends with: "Hard rules: do NOT spawn sub-agents or workflows.
Never delete or overwrite a path you did not create. Never override
LOCALAPPDATA, APPDATA, USERPROFILE or HOME. Do not run pytest. Do not touch
git." Python is `C:/Users/brand/AppData/Local/Python/pythoncore-3.14-64/python.exe`
with `PYTHON_MANAGER_AUTOMATIC_INSTALL=false` (and `PYTHONIOENCODING=utf-8`).
- **research**: `specs/RESEARCH_AUTHOR.md`, the unit's entry in units.json and
  its map lines, plus one finished unit of the same tier as the bar to meet
  (T1 the-sun-and-its-planets, T2 cells-the-building-blocks-of-life,
  T3 mendels-peas-and-inherited-traits, T4 inside-the-atom,
  T5 how-germs-were-proven).
  Every research brief also names the neighbours already written, so no
  question asks a fact another unit asks. From T2 on, it also names the
  lower-tier units on the same ground: a question must go a grade deeper
  and never re-ask a lower tier's fact.
  `lead_notes.md` keeps the cross-unit notes to pass on.
- **judge**: `specs/JUDGE.md` and the unit ids. Ask the judge to check for
  overlaps against every unit with a `final.json`, and to rule on lanes.
- **factcheck**: `specs/FACTCHECK.md` and the unit id.
- **revise**: `specs/REVISE.md` and the unit ids.
- **recheck**: `specs/RECHECK.md` and the unit ids.
- **card**: `specs/CARD.md` (on top of `bankbuild/cards/AUTHOR_SPEC.md`) and
  the batch number.
- **reader**: `bankbuild/cards/JUDGE_SPEC.md` and the batch numbers; the reader
  writes `_cards/science/bNNN_judge.json` for each.

## Stance units
They run last, COVID last of all (status.py's build order). Their framing
notes are in units.json. Brandon, 2026-11-25, on the COVID unit: "Yes, as
described" (the units.json scope, with no change).
