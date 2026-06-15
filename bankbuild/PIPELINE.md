# Quiz Bank Rebuild — Complete Runbook

**Trigger:** the user says *"now we're going to do the `<X>` bank"* (geography, theology, science, …).
This document is the **entire process, zero-to-shipped**. Follow it exactly; do not improvise.
The **history** bank (`data/questions/history.json`, 5,356 questions) is the reference build.

One pipeline builds any subject so it ships **without a separate audit phase** — the two strengths of
the old overnight audit (a fresh adversarial re-judge + a deterministic mechanical scan) now run
*inside* the build loop. See §6 for why that works.

---

## 0. Orient first (no agents yet)

- **The unit of design is the TOPIC LADDER, not the question.** A topic gets a mini-bank ladder across
  tiers that turns the subject into a person/story (memory: `feedback-topic-ladders`). One fact per rung.
- **Read the subject's voice + stance** before writing anything: `docs/quiz/subjects/<X>.md`,
  `docs/quiz/<X>_strategies.md`, `docs/quiz/moral_vision.md` (SUPREME — the bank's soul), and the
  subject's voice memory (`feedback_<x>_voice` / the controlling-pattern memory in MEMORY.md).
- **Every subject has ONE controlling VOICE rule** — the soul of its answers:
  Wonder Pattern (history, geography, theology, trivia) · Comma-Saves-Lives (grammar) ·
  Recognition (AI) · Discovery (science) · Bastiat seen/unseen (economics). Math/grammar are the
  snappy-rote exceptions (no Wonder Pattern).
- **Hard constraints:** ALL LLM work via Claude Code Opus subagents — `model:'opus'` on EVERY agent,
  no exceptions (no API spend). Research is web-sourced; **thin beats fabricated**. Grade-10 ceiling.

---

## 1. Prerequisites — does subject X already have these two files?

Check `bankbuild/<X>/_queue.json` and `bankbuild/subjects/<X>.json`. If either is missing, build it
before any pipeline run.

### 1a. Topic queue — `bankbuild/<X>/_queue.json`
An ordered array of topic specs. One entry (history example):
```json
{ "id":"hammurabi-s-code", "name":"Hammurabi's Code", "strand":"Ancient Near East & Egypt",
  "kind":"ladder", "scope":"282 written laws; eye-for-an-eye justice", "tier_span":"T2-T5",
  "depth":"standard", "target_q":10, "source":"Core Knowledge; AP World Unit 1",
  "framing_note":"VISION-CENTRAL: ... (moral_vision §3.4) ... teach it honestly ...", "weight":"high" }
```
Field meaning: `depth` = deep (10-15 rungs, keystone topics) | standard (3-5) | mini (1-3 gems);
`tier_span` = the difficulty band; `target_q` = rung target; `weight` = priority.
- **Topic SELECTION = social-consensus canon:** web-grounded breadth against STANDARD curricula
  (Core Knowledge, AP, museum/encyclopedia canon) — NOT the moral_vision docs. Using the philosophy
  docs as the topic index makes a parochial bank (memory: `feedback-register-consensus`).
- **Topic FRAMING (`framing_note`) = moral_vision:** stance, mandated emphasis/inclusions, voice.
- Priority-**sort** the array: weight high>med>low, then depth deep>standard>mini.
- Building the queue is itself an Opus task (research the canonical topic list for the subject, tag each
  field). History's was assembled from a `register.json` of strands → topic specs.

### 1b. Subject config — `bankbuild/subjects/<X>.json` (copy `subjects/history.json` as the template)
```json
{ "name":"<X>",
  "queue":"C:\\Users\\brand\\Documents\\PhilosophersQuest\\bankbuild\\<X>\\_queue.json",
  "voice_rule":"<the subject's controlling VOICE rule, distilled from its docs + voice memory>",
  "framing":"<one line on how moral_vision applies>",
  "tier_note":"Tiers = conceptual difficulty (T1 simple/concrete .. T5 analytic), grade-10 ceiling; aim ~30%+ at T1-T2." }
```
`voice_rule` is the ONLY subject-specific prompt text — the 14 craft rules + the 3 leak shapes are
generic, baked into the pipeline.

---

## 2. Operational rules (hard-won — break these and you lose work)

- **ONE batch at a time, NEVER concurrent.** Concurrent batches compound server rate-limiting and drop
  topics. Wait for each to finish and integrate before launching the next.
- **Batch size ~15-20 topics.** Checkpoint after EVERY batch, then advance the cursor.
- **`model:'opus'` on every agent.** No API spend.
- **Quota walls** — a batch failing with "session limit" / "hit your … limit" is the ~5-hour usage cap,
  not a controls failure: STOP, resume next window from the manifest. Transient "rate limited" /
  "Overloaded" are absorbed by the pipeline's retry-with-backoff — don't stop for those.
- **Resumable:** `python bankbuild/bank.py status --subject=X` shows the manifest; the next batch starts
  after the last integrated `idx`.

---

## 3. Build the bank (the loop)

For each batch covering queue indices `[N, N+count)`:
1. **Launch** (paste the config from 1b inline as `args.config`):
   `Workflow {scriptPath:"bankbuild/bank_pipeline.wf.js", args:{config:<X config JSON>, start:N, count:20}}`
2. **Integrate** on completion:
   `python bankbuild/bank.py integrate "<task output file>" --subject=X`
3. **Advance** `N += count`; repeat until the queue is exhausted.

Each ladder runs: **research → author (rules + self-audit) → craft judge + revise (Pass A) →
deterministic gate + adversarial judge + de-tell (Pass B)**. It checkpoints as `passed` (clean) into
`bankbuild/<X>/ladders/`, or `needs_review` into `bankbuild/<X>/needs_review/`.

---

## 4. Handle needs_review
Ladders the build couldn't drive to **0 high + 0 medium** land in `needs_review/`. Don't promote them.
Options: re-run specific topics (`args:{config:…, idxs:[12,57,…]}`), hand-review, or drop. A modest
needs_review rate is **healthy** — it means the adversarial judge is catching real tells (it caught a
fabricated fact on the very first history smoke-test). Never loosen the bar to force passes.

---

## 5. Assemble + ship

1. `python bankbuild/bank.py merge --subject=X` → `data/questions/<X>_v2.json` (staging; live bank untouched).
2. `python bankbuild/bank.py gate --subject=X` → mechanical-tell scan of the staged bank
   (`python bankbuild/tellgate.py bank data/questions/<X>_v2.json` for per-question detail). Fix or accept.
3. `python bankbuild/bank.py promote --subject=X` → backs up the live bank to `<X>_pre_v2_backup.json`,
   swaps in v2 (runs the gate first as a pre-promote check).
4. **SHIP — user confirms releases:** commit the new bank, bump the version, rebuild the installer.
   Release per the iterative **x.y.0-per-bank** plan (one minor version per completed bank).

---

## 6. Why this ships clean WITHOUT a separate audit (the prevention layers)

The recurring tells come in two kinds, and each has a defense **inside the build**:

1. **Author + craft judge + revise (Pass A)** — author writes against the 14 craft rules + the 3
   high-severity leak shapes (RESTATEMENT / TOPIC-NAME MATCH / ENUMERATION) + a 5-point self-audit; a
   strict judge flags; revise loop (cap 2).
2. **Deterministic mechanical gate** — `mechGate` in `bank_pipeline.wf.js`, mirrored by `tellgate.py`.
   Free, runs every time. Two checks: key-noun leak on a LABEL answer; answer printed verbatim in the
   stem. **76% precision but only ~2-4% recall** (validated against the 1,200 LLM-audited history rungs),
   because ~93% of tells are SEMANTIC. So its flags don't auto-edit — they're **handed to the adversarial
   judge** to confirm or clear, so good vivid answers are never forced to change.
3. **Adversarial judge (Pass B)** — a fresh, hostile, INDEPENDENT re-judge ("this already passed a judge;
   catch what it missed"), fed the gate flags. This catches the SEMANTIC 93% a regex can't see. Revise
   may DROP an unfixable rung (e.g. a fabricated fact). A ladder passes only at **0 high + 0 medium**.
4. **Pre-promote gate** — `bank.py promote` re-scans the staged bank before swapping it live.

**Why we don't audit a built bank:** an exhaustive LLM re-judge + web-fact-check found high-severity
craft at ~0.4% and bad facts ~0.4% across 1,200 rungs — not worth ~14 quota windows + a fix phase. Pay
the adversary once at build time instead (memory: `project-bank-rebuild-harness`, `feedback-topic-ladders`).

---

## 7. Keeping the gate in sync
`bank_pipeline.wf.js`'s `mechGate` (JS, in-build) and `tellgate.py`'s `gate` (Python, batch/pre-promote)
implement the SAME two checks. Change one → change the other. The Python copy is the reference;
`python bankbuild/tellgate.py validate` measures its precision/recall against any LLM-audited ground truth.

## File map
- `bankbuild/bank_pipeline.wf.js` — the subject-agnostic build Workflow
- `bankbuild/subjects/<X>.json` — per-subject config (voice rule, queue path, framing)
- `bankbuild/<X>/_queue.json` · `…/ladders/` · `…/needs_review/` · `…/manifest.json` — per-subject state
- `bankbuild/bank.py` — integrate / merge / status / gate / promote (`--subject=X`, default history)
- `bankbuild/tellgate.py` — deterministic gate: `scan` · `bank <file>` · `validate`
- `data/questions/<X>.json` (live) · `<X>_v2.json` (staging) · `<X>_pre_v2_backup.json` (backup)
