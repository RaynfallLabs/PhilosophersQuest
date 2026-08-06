# Quiz Bank Rebuild — Complete Runbook

**Trigger:** the user says *"now we're going to do the `<X>` bank"* (geography, theology, science, …).
This document is the **entire process, zero-to-shipped**. Follow it exactly; do not improvise.
The **history** bank (`data/questions/history.json`, 5,356 questions) is the reference build.

One pipeline builds any subject so it ships **without a separate audit phase** — the two strengths of
the old overnight audit (a fresh adversarial re-judge + a deterministic mechanical scan) now run
*inside* the build loop. See §6 for why that works.

---

## 0. Orient first (no agents yet)

- **Check the subject roster + per-subject notes in §13 FIRST** — it tells you the subject's KIND (knowledge / reasoning / snappy-rote), controlling voice, which de-tell rubric to fork, ladder-shape fit, stance load, and (if you're choosing) which bank to build next.
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
   **Then run the §11 post-promote hygiene:** register the subject with the legacy gates
   (`length_parity.ANSWER_OUTLIER_SUBJECTS` + full `pytest`), sweep `<X>_v2`/`<X>_pre_v2_backup`
   artifacts out of `data/questions/`, and run the post-ship semantic-dedup pass.

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

## 8. Additions from the philosophy build (2026-06-17) — the de-tell sweep + the moral-vision audit

Philosophy (`data/questions/philosophy.json`, 2,867 Q) is now a **second reference build**, alongside history. Two tools were added and are the standard now.

**The de-tell sweep — the per-batch convergence tool (`bankbuild/detell_pipeline.wf.js`).** After each build batch: integrate, then de-tell the `needs_review` ladders instead of re-running them from scratch (§4). It reads each `needs_review/<id>.json`, runs a surgical reviser (fix ONLY flagged rungs; parity sacred; reword answers to kill echoes; NO new facts) + a fresh adversarial judge + the mechanical gate, and **deterministically drops any rung still flagged after 2 rounds** so every ladder converges to 0-high/0-medium (shedding ~0–2 rungs). Apply with `python bankbuild/<X>/_apply_detell.py "<task output>"` (promotes cleared ladders into `ladders/`, deletes them from `needs_review/`). Typical rhythm: build passes ~30–50% first try; the de-tell sweep + drop converges the rest to 100%. Its judge applies a **reasoning-appropriate** standard — a careful kid reasoning to the answer from live options is the skill, NOT a telegraph — which matters when the answer is a *move*, not a fact.

**The moral-vision audit — the pre-ship stance gate (`bankbuild/<X>/_moral_audit.wf.js`).** An independent Opus panel scores each stance-relevant ladder against `moral_vision.md` §1–§9, flagging BOTH directions: imposed-verdict / strawman / smug-voice / advocacy-frame **and** *neutral-where-the-bank-takes-a-side* (see moral_vision **§3.10** — the no-verdict rule is NOT uniform). Read-only. Run it over the subject's stance topics before `promote`; correct what it flags. **This is now a required ship step for any value-laden subject** — the generic build judge enforces only the generic no-verdict rule, so the subject's STANCE must be checked here (and, better, baked into the config `framing`, as philosophy's now is).

**Helper scripts** (`bankbuild/<X>/`): `_assemble_queue.py` (per-strand files → `_queue.json` + `register.json`), `_next_batch.py N` (next N unbuilt idxs, skips done/needs_review), `_apply_detell.py`, `_gen_review_doc.py` (human-readable review doc to project root).

**Wall / rate-limit handling.** A wall at the **research** stage → empty `thin-research` ladders (n=0): do NOT integrate that output; just re-run the build on those idxs. A wall at the **author/judge** stage → ladders integrate as `needs_review` WITH a full ladder: just DE-TELL them (don't rebuild). Transient `Rate limited` / `Server is temporarily limiting` ≠ the usage wall (the pipeline's retries absorb it; rebuild only the n=0 ones). `bank.py merge` now skips `_`-prefixed files (a build subagent can drop a stray draft into `ladders/`).

**ALWAYS RESUME a walled build batch to completion before integrating** (efficiency rule, cooking build 2026-07-15). When a batch walls mid-run, do NOT integrate the walled partial — relaunch the SAME run with `Workflow({scriptPath, resumeFromRunId, args})` once the window resets. Completed agents replay from cache for free; only the walled agents re-run. Integrating a partial instead lands topics as `needs_review` with an **unfinished adversarial pass**, which the de-tell sweep must then redo — a double adversarial pass that inflates the whole de-tell phase (half of cooking's needs_review pile was wall-caused, not quality-caused). Resume-then-integrate keeps topics passing in-build and shrinks de-tell. **BUT** resume needs the SAME session's cache alive; on a multi-day build the process is torn down between windows and that cache is gone — see **§12.1** for the salvage-based recovery (`_integrate_passed.py` + the early-vs-near-complete modes) that works when resume can't.

**Stance vs neutral (load-bearing).** Before building a value-laden subject, identify its stance topics (where moral_vision §1/§3/§9 commit the bank) vs its genuinely-open ones, and put the LEAN into the subject config `framing` + the topic `framing_note`s so it reaches the author + judge — not only the audit. See moral_vision §3.10 + memory `feedback-stance-vs-neutral`.

## File map
- `bankbuild/bank_pipeline.wf.js` — the subject-agnostic build Workflow
- `bankbuild/subjects/<X>.json` — per-subject config (voice rule, queue path, framing)
- `bankbuild/<X>/_queue.json` · `…/ladders/` · `…/needs_review/` · `…/manifest.json` — per-subject state
- `bankbuild/bank.py` — integrate / merge / status / gate / promote (`--subject=X`, default history)
- `bankbuild/tellgate.py` — deterministic gate: `scan` · `bank <file>` · `validate`
- `bankbuild/detell_pipeline.wf.js` — per-batch de-tell sweep (reviser + adversarial + deterministic-drop); apply with `<X>/_apply_detell.py`
- `bankbuild/queue_dedup.wf.js` + `queue_dedup_apply.py` — **pre-build** gate: cluster same-fact topics and drop the redundant twins from `_queue.json` BEFORE building (subject-generic; run right after `_assemble_queue.py`). See §10.
- `bankbuild/dedup_overlap_scan.py` — **post-ship** candidate finder (subject-generic): local ANSWER-SET overlap over the built `ladders/` → candidate twin pairs (catches built-ladder convergence the scope-based `queue_dedup` misses). Feeds `dedup_verify`. See §12.2.
- `bankbuild/dedup_verify.wf.js` + `dedup_prune_apply.py` — **post-ship** conservative dedup: verify candidate clusters against the FULL built ladders (biased-to-keep), then reversibly prune confirmed dups to `bankbuild/<X>/_pruned/`. See §11.3 + §12.2.
- `bankbuild/<X>/_moral_audit.wf.js` · `_tone_audit.wf.js` — pre-ship stance + parent's-eye audits (read-only, Opus panels; BATCHED — one agent per `args.batch` ladders, default 5)
- `bankbuild/<X>/_assemble_queue.py` · `_next_batch.py` · `_apply_detell.py` · `_gen_review_doc.py` · `_dupscan.py` (question-level dedup) — build helpers
- `bankbuild/<X>/_integrate_passed.py` — **wall-recovery salvage**: from a WALLED build output, integrate ONLY fully-`passed` topics → `ladders/`, leaving the rest for `_next_batch.py` to rebuild. Use when `resumeFromRunId` cache is gone (multi-window builds). See §12.1.
- `data/questions/<X>.json` (live) · `<X>_v2.json` (staging) · `<X>_pre_v2_backup.json` (backup)

## 9. Additions from the animal build (2026-07-08) — the THIRD reference build

Animal (`data/questions/animal.json`, **2,621 Q, v2.3.0**) is now a third reference build alongside history and philosophy. It added several things that are the standard now for **every** future subject rebuild:

1. **Grokipedia FIRST, before Wikipedia.** The research stage (`bank_pipeline.wf.js` researchPrompt STEP 2) now requires: *check Grokipedia (grokipedia.com) first for every fact, prefer it whenever both cover a fact, then corroborate with Wikipedia and other reputable primary sources.* Brandon considers Grokipedia the more reliable source (memory `feedback-grokipedia-first`). Applies to ad-hoc fact-checks too.

2. **A subject's OLD design docs can be WRONG — the CONFIG `voice_rule` is the load-bearing design, not the old `docs/quiz/subjects/<X>.md`.** Animal's `subjects/animal.md` + `animal_strategies.md` described a retired 5-pillar culture/husbandry design that Brandon rejected outright; the shipped design (pure animal-knowledge) lives only in `subjects/animal.json`. Those two docs now carry a SUPERSEDED banner. **Lesson:** don't trust an old subject doc blindly — read it, then *state your understanding back to Brandon for correction before building the queue*; expect the **queue-review gate + the first smoke batch** to surface design problems while they're cheap. Bake the final design into the config `voice_rule`.

3. **Two ladder SHAPES when a subject has cross-cutting themes.** (A) the usual CREATURE/ENTITY ladder — one thing deepened; (B) the **ADAPTATION/THEME ladder** — one theme deepened ACROSS the many entities that share it (animal: eyes, echolocation, live-birth). A fact that spans entities (the fish spherical lens) belongs in a THEME ladder, not forced into one entity. For animal the theme ladders were the ~60% backbone.

4. **The de-tell / judge standard must match the subject KIND.** Philosophy's de-tell *protects* "a careful kid reasoning to the answer" (reasoning subject). A **KNOWLEDGE** subject (animal, and likely geography/science-facts) is the opposite: deducing the answer from the stem IS the tell. Animal has its own `_detell.wf.js` with a knowledge-subject rubric — do NOT reuse philosophy's blindly; fork the rubric per subject kind.

5. **Distractor & anti-restatement discipline** (the recurring first-pass failure — animal's first smoke was 0/5, all restatement / self-eliminating-distractor tells). Bake into the config `voice_rule`: the stem sets up the CHALLENGE/PUZZLE, **never the SOLUTION the answer names**; all four choices stay LIVE (no stem clause self-eliminates one); never DEFINE a term then ask its label; strict choice parity; numbers only when the stem constructs an expectation they shatter. This lifted first-pass quality and de-tell converged every batch to 100%.

6. **Tone / kid-appropriateness audit — a required PRE-SHIP step** (`bankbuild/<X>/_tone_audit.wf.js`, one parent's-eye Opus reviewer per ladder). Flags gameplay-frame leaks (for animal: butcher-table / "you harvest/skin/gut it" / a second-person "cut it open" on a LIVING animal / nursing young on a dead parent), gratuitously graphic/gory WORDING, and cruelty-as-entertainment. CRITICAL GUARD: honest predation, death, scavenging, parasitism, extinction stay — you flag **framing and wording, not subject matter**; fossils / museum specimens / third-person history are fine. Brandon caught the butcher-table frame by eye at review; the audit then swept the rest. This is now a ship gate for any subject with a real-world-action frame or dark content.

7. **Tier-curve diagnostic + the additive DEEPEN pass.** Banks come out **bottom-heavy**: a forced T1/T2 recognition base on ~every ladder + a finite ceiling (most topics genuinely top out at T3–T4) + the no-padding rule ⇒ a hump at T2–T3 and a near-empty T5. Fix it **additively** with `bankbuild/<X>/_deepen.wf.js` (+ `_apply_deepen.py`): per topic it reads the existing ladder, researches NEW advanced facts (Grokipedia-first, not duplicating covered facts), authors 2 fresh **T4/T5** rungs, adversarial-judges + gates + revises, and APPENDS them — never touching existing rungs. Run it on the topics that can carry depth (deep-depth + evolution/paleo + deep-physiology/cognition). Animal's pass added **+283 rungs** and tripled T5 (3.5% → 9.6%).

8. **Workflow-infra gotchas (hard-won):** (a) **a walled/failed JUDGE must return status:failed with NO rungs** — otherwise unjudged rungs fall through as "passed" (fixed this in `_deepen.wf.js`). (b) Big parallel audit/deepen jobs (300+ agents fired at once) trigger **transient server rate-limits** ("Server is temporarily limiting requests · not your usage limit") that knock out roughly half — **chunk to ~38 topics/run**, and re-run the un-verified subset by parsing the output and skipping the agent-failed fallback records. (c) Deepen/audit are token-heavy (~6M tokens / 38-topic chunk) — expect to span 5-hour and weekly usage windows; apply after each chunk so a wall never loses committed progress.

**Ship sequence used (per `bank.py`):** merge → gate → moral-vision audit → **tone audit** → (optional) **deepen pass** for the tier curve → re-merge/gate → `promote` → commit the clean subject-only files to `main` + version bump in `src/layout.py` (x.y.0-per-bank) + installer rebuild. (For animal, Brandon deferred the installer and kept the version bump on his parallel UI branch.)

## 10. Efficiency levers (cooking build, 2026-07-15) — cut usage without degrading output

The cooking build (~170M subagent tokens) is the reference for where the cost goes: **the build pipeline is ~70%**, de-tell ~13%, tone audit ~10%, the rest small. Four changes were made after ship; all are no-quality-risk. (A fifth — **model-tiering** the build, i.e. author on Sonnet with the Opus adversarial pass as the quality backstop — is the biggest lever but relaxes the "opus everywhere" rule and needs a one-strand A/B before rollout; NOT yet adopted.)

1. **Semantic-dedup the queue BEFORE building** (`queue_dedup.wf.js` → `queue_dedup_apply.py`). The token-level dedup only catches similar topic *names*; semantically overlapping ladders (Maillard ×3, chili-to-Asia ×3, tomato-to-Italy ×2) each cost a full research→author→judge→adversarial build and were dropped only at merge. Run dedup right after `_assemble_queue.py`, review the clusters, `--apply`, THEN build. Keeps genuinely-different angles (pepper-trade vs pepper-botany); only drops same-fact twins.
2. **Always resume a walled build batch to completion before integrating** — see §8. Keeps the in-build adversarial pass finished, so wall-caused topics don't fall into the de-tell pile.
3. **Batch the audits** (`_tone_audit.wf.js` / `_moral_audit.wf.js` now take `args.batch`, default 5). One agent reviews N ladders instead of 1, cutting ~60% of the audit phase's per-agent rubric overhead; the schema forces one verdict object per ladder so each still gets a full independent review. Keep tone at FULL coverage (child-safety); it's the batching, not the coverage, that's cheaper.
4. **RULES as a byte-identical prompt prefix** (`bank_pipeline.wf.js`). Every build prompt (author/judge/advJudge/revise) now OPENS with the identical `${RULES}` block, then its task-specific tail — so the session prompt-cache can reuse that ~4KB invariant across all ~3,000 calls (benefit depends on the harness prefix-caching workflow agents; the reorder is harmless regardless). When editing these prompts, keep RULES first and put per-topic text only AFTER it.

## 11. Ship hygiene + gate registration (v2.4.0 ship + cleanup, 2026-07-18)

Three steps that MUST run when a rebuilt bank ships — learned when philosophy shipped with **251 phantom gate failures** and the exe bundled **~47 MB of bank artifacts**.

1. **Register the subject with the legacy `tools/quizgen` gates.** The bankbuild pipeline and the old `tools/quizgen` deterministic gates are SEPARATE validators, and the test suite runs the latter. After `promote`:
   - Add the subject to `tools/quizgen/deterministic/length_parity.py:ANSWER_OUTLIER_SUBJECTS` (every non-`math` subject belongs here; `math` is EXEMPT). A ladder-built bank uses variable-length competing-choice distractors, so the strict "all four choices equal length" fallback rule is WRONG for it — the only real tell to guard is the *answer* being a length outlier. Philosophy was left off → 251 false `length_parity` fails on a clean bank.
   - Run the FULL suite (`pytest tests/ -q`) and reconcile whatever keys off the subject: `test_load_<X>_subject_spec` (a rebuild often relabels the spec `style_verdict` — assert the invariant like `"WONDER" in verdict`, not a brittle literal), and any absolute count thresholds in `test_quizgen_deterministic` (prefer a RATE over a bank-size-dependent absolute).

2. **Sweep bank artifacts OUT of `data/questions/` at ship.** `bank.py promote` leaves `<X>_pre_v2_backup.json` there; builds leave `<X>_v2.json` / `<X>_tellgate.json` / `<X>.json.backup`. The installer bundles `data/questions/` WHOLESALE, so every one of those ships as dead weight in the exe. Move them to `bankbuild/<X>/` or `_archive/` after promote. `tests/test_packaging.py::test_bundled_dirs_contain_only_runtime_files` now FAILS the build if any non-`.json`, or a `_v2`/`_pre_v2_backup`/`_tellgate`/`_backup` artifact JSON, is left inside a whole-dir bundle entry (`data/{items,materials,questions,templates}`, `assets/{fonts,tiles}`) — enforced, not merely advised. `data/questions/` must end as exactly the live banks.

3. **Semantic dedup is REQUIRED — pre-build AND post-ship.** §10 lever #1 dedups the QUEUE before building; a SHIPPED bank ALSO gets the conservative full-ladder pass (the toolkit found real same-fact dups in every bank run: cooking 23, animal 3, philosophy 2). Flow for a shipped bank (all `model:'opus'`; **precondition:** a fresh `bank.py merge --subject=X` reproduces the LIVE count, else `ladders/` is stale and re-merge would regress the bank):
   1. `Workflow{scriptPath:"bankbuild/queue_dedup.wf.js", args:{subject:X}}` → same-fact `clusters`. **For a LARGE bank (~500+ topics) the single-agent clusterer overflows the 64K output cap** (history's 777-topic pass ran ~55 min then died). SHARD instead: one agent per strand (within-strand clustering, each ≤~60 topics) + one cross-strand agent over a compact `{id,name,strand}` index (catches the same figure queued under two strands — history's keystone-strand dups). History found **71 clusters / 78 candidate drops** this way. Note: pass ladder/cluster data to verify agents through a small **python helper script** (`_read_batch.py <start> <count>` printing clusters+full ladders as JSON), NOT baked into the workflow — embedding 14KB or using `String.fromCharCode`/nested-quote read commands trips JS-escaping and the approval-dialog control-char check.
   2. FILTER clusters to ids that actually have a `ladders/<id>.json` — queue topics can lack a built ladder (the **phantom-keep trap**: a cluster whose `keep_id` has no ladder would delete the only built copy). Philosophy hit this with `descartes-dream-argument`.
   3. `Workflow{scriptPath:"bankbuild/dedup_verify.wf.js", args:{subject:X, clusters:[…], batch:6}}` — reads the FULL ladders, biased-to-keep. **This verify pass is LOAD-BEARING** (philosophy 7 raw clusters → 1 real). Returns the confirmed drop set.
   4. `python bankbuild/dedup_prune_apply.py --subject=X "<verify output>" [--dry]` → moves confirmed dup ladders to `bankbuild/<X>/_pruned/` (reversible), drops them from the manifest.
   5. `bank.py merge → gate → promote`, then step 2 (sweep artifacts).

## 12. Additions from the geography build (2026-08-06) — the FOURTH reference build

Geography (`data/questions/geography.json`, **3,216 Q, v2.5.0** — 405 place + earth-system-theme ladders, replaced 1,123) is the fourth reference build. It confirmed the animal/cooking machinery on a big place-KNOWLEDGE subject (PLACE→WONDER voice, two ladder shapes, knowledge-kind de-tell) and added these, now standard:

1. **Multi-window wall-recovery when resume-cache is DEAD (the load-bearing new lesson).** §8's "ALWAYS RESUME a walled batch before integrating" assumes the SAME session's workflow cache survives to the reset. On a real large build it does NOT: the usage cap recurs ~every 5 hours as a *rolling* window (labels like "resets 6pm" but behaves as a moving ~5-hr window), the build spans DAYS, and the Claude Code process is torn down between windows — so `resumeFromRunId` cache is almost always GONE. Geography walled ~15× (rolling) + 2× (weekly) and resume was essentially never available. The robust recovery, subject-forkable, is `bankbuild/<X>/_integrate_passed.py <walled_out>` + **two modes chosen by how far the batch got** (read `agents_done` vs `agents_error` in the task usage):
   - **EARLY wall** (few agents done, most topics never reached `passed`): `_integrate_passed.py` banks ONLY the fully-`passed` topics (status `passed` + valid non-empty rungs — unambiguously complete + clean) into `ladders/`, leaving everything else UN-integrated; `_next_batch.py` then returns the rest to REBUILD fresh. NEVER `bank.py integrate` a walled partial here — it writes `status:'error'`/empty-ladder topics into `needs_review/` where they ORPHAN (manifest says built, `_next_batch` skips them, de-tell can't fix 0 rungs) — the §8 trap made concrete.
   - **NEAR-COMPLETE wall** (only a couple agents walled — e.g. geography batch 17: 112/119 done): run the FULL `bank.py integrate`, but FIRST confirm the printed `needs_review` list has NO 0-rung/EMPTY entries (any that exist would orphan — delete them from manifest+needs_review to rebuild), THEN DE-TELL every `needs_review` id. This salvages ~10 finished-but-flagged topics' research+author+judge instead of rebuilding them. Safe: a walled-during-adversarial topic reports `needs_review` with a full authored ladder, and de-tell runs a fresh adversarial pass anyway.
   Each rolling wall otherwise discards ~2–4M tokens of completed-but-unintegrated work; the salvage recovers the fully-passed slice for free.

2. **Shard queue-dedup at ~400 topics (not ~500); per-SECTION sharding works; find POST-SHIP candidates by ANSWER-OVERLAP, not a re-run.** (Sharpens §11.3.1.) Geography's single-agent `queue_dedup` overflowed the 64K cap at **418** topics (ran ~61 min then died) — treat **~400+** as the shard threshold. `bankbuild/geography/_queue_dedup.wf.js` shards per-SECTION (5 agents, within-section, full scope) + 1 cross-section agent over a compact `{id,name,section}` index — a clean variant of history's per-strand shape. **Post-ship, do NOT re-run the scope-based `queue_dedup`** (it already judged pre-build and cannot see how the built ladders converged): instead run `python bankbuild/dedup_overlap_scan.py --subject=X` (subject-generic; local answer-set overlap over the built `ladders/`, no agents — pairs sharing ≥2 normalized answers), edit the output down to the real same-place/same-topic twins (most hits are legit theme-uses-place cross-links), and feed those to `dedup_verify`. Geography: overlap scan → 4 candidate twins → verify SPARED 3 (each near-twin had 3–4 unique facts) + CONFIRMED 1 (a Yellowstone ladder, 8/11 rungs duplicate). The pre-build scope dedup had judged all 4 as different-angle; only the answer-overlap scan on the BUILT ladders caught the convergence.

3. **Deepen is CONDITIONAL — check the merged tier curve first; theme-ladder-heavy subjects often SKIP it.** (Sharpens §9.7.) Animal came out bottom-heavy (T5 3.5%) and needed the +283-rung deepen pass. Geography came out **T5 14.5% with NO deepen** — its earth-system THEME ladders (one process deepened across many places, naturally analytic at T4/T5) plus the deep city/ancient topics carry native ceiling. Run `bank.py merge` and read the tier dist BEFORE forking `_deepen.wf.js`; skip deepen when T5 ≥ ~13% and T1–T2 ≥ ~30%.

4. **Stance-in-config → 0 audit flags (strong validation of §8's stance-vs-neutral rule).** Geography baked its full stance table into the config `framing` + per-topic `framing_note`s up front (Age-of-Discovery + indigenous civilizations celebrated as full civilizations; colonialism honest both ways; Soviet/Maoist environmental record as fact; sacred sites symmetric; climate descriptive not alarmist). Result: the pre-ship moral audit flagged **0/57** stance topics — the stance reached the author + judge in-build, so nothing needed fixing at audit. The payoff of §8's "put the LEAN into config, not only the audit." (The tone audit still earned its keep: 1 medium + 2 lows across 406 ladders, hand-fixed — child-safety wording is not something config framing prevents.)

5. **`.wf.js` codegen + Windows-console gotchas (hard-won).** (a) When GENERATING a `_build.wf.js` launcher (or any `.wf.js`) via python, write with `open(...,'w',newline='\n')` — CRLF `\r` trips the Workflow approval-dialog's control-char check and the launch is refused. (b) Use FORWARD-SLASH paths in the `workflow()` `scriptPath` — Windows backslashes get eaten as JS string escapes (`\U`, `\b`→backspace) and the delegated path mangles. (c) Any per-subject python helper that PRINTS non-ASCII (ō, é, —) needs `sys.stdout.reconfigure(encoding='utf-8')` up top, or it dies on the Windows cp1252 console mid-report. The `_build.wf.js` launcher pattern (embed the subject config as a JS literal, delegate to `bank_pipeline.wf.js` via `workflow()`) is now standard — it avoids inlining the ~12KB config into every Workflow call.

**Ship sequence (unchanged from §9, all steps ran clean):** merge → gate → moral audit (0 flags) → tone audit (1 medium + 2 lows hand-fixed) → tier-curve check (healthy, deepen SKIPPED) → post-ship dedup (1 pruned) → re-merge/gate → `promote` → full pytest (green; geography was pre-registered in `length_parity.ANSWER_OUTLIER_SUBJECTS`, and `test_load_geography_subject_spec` asserted `"WONDER" in verdict`, so no reconciliation) → artifact sweep → commit + version bump (`src/layout.py` + `installer/setup.iss`, 2.4.0→2.5.0) → installer (PyInstaller freeze validates the bundle carries the new bank; the final ISCC compile needs Inno Setup on the build machine).

## 13. Subject roster & per-subject build notes (which bank next + how each differs)

Ten subjects (each mapped to an in-game action → quiz mode; see CLAUDE.md's table + `src/player.py:SUBJECT_TIMER` for exact mode/timer). **Pipeline-built so far:** history (5,306 Q), philosophy (v2.2.0, 2,864 Q), animal (v2.3.0, 2,600 Q), cooking (v2.4.0, 2,908 Q), geography (v2.5.0, 3,216 Q). **Five REMAIN** — read the named voice memory + `docs/quiz/<X>*.md` (SUPERSEDED-banner aware) and STATE THE DESIGN BACK before building (§9.2):

| Subject | KIND | Controlling voice (memory) | De-tell rubric (§9.4) | Ladder-shape fit | Stance load |
|---|---|---|---|---|---|
| **science** (magic/wands) | knowledge + WONDER | Discovery — reveal *how we know* / the mechanism (`feedback-science-voice`) | KNOWLEDGE (deducing from the stem IS the tell) | **HIGH** — geography's twin: concept/theme ladders deepened across cases + single-discovery/scientist ladders | **HEAVY** — dissent honored, institutional capture nameable, vaccine SCRUTINIZED not celebrated (RFK/Bhattacharya/GBD given the moral weight); bake into config `framing` |
| **theology** (praying) | WONDER, story-led | Wonder→theology, TELL THE STORY (`feedback-theology-voice`) | KNOWLEDGE/story (deduce = tell, but story-led openings) | HIGH — story-led figure/place/myth ladders | **DELICATE** — STRICTLY SYMMETRIC four traditions (Christian ~30 / Arthurian+medieval ~20 / Greek ~25 / Norse ~25); Brandon is NOT Christian → all on one plane, no Christian-favoring language, no author-attribution. Geography's respectful sacred-site handling (Mecca/Jerusalem/Kailash) is the warm template |
| **economics** (lockpicking) | REASONING + stance | Bastiat seen/unseen · the incentive · the knowledge-problem (`feedback-economics-voice`, `feedback-surface-good-critique`) | REASONING (a careful kid reasoning to the answer IS the skill, like philosophy — NOT a telegraph) | MED — a reasoning MOVE per rung, not a fact | **HEAVY** — Austrian-correct, Fed-critical, communism 65–100M, Bitcoin great; teach RECOGNITION of moves, not policy verdicts |
| **grammar** (scrolls/spellbooks) | snappy-rote WITH a voice | Comma-Saves-Lives — punchline via misuse ("Let's eat, Grandma!") (`feedback-grammar-voice`) | different (short punchline items; NOT deep ladders) | LOW–MED — vocab-teaching T1–T3, grade-10; not a topic-ladder subject | light |
| **math** (combat/chain, ~16 s) | snappy-ROTE EXCEPTION | none — Wonder Pattern EXEMPT, anti-rote gate EXEMPT | different (short factual) | **LOW** — not topic-ladders at all | none |

**Which next — the recommendation logic:** favor **biggest flagship × closest-template-reuse while the machinery is fresh**. That points to **science** — it mirrors geography almost exactly (knowledge+wonder, two ladder shapes, Grokipedia-first, knowledge-kind de-tell, deepen-conditional), and its real stance content makes it the clean next test of "bake the stance into config, not only the audit" (§12.4). Then **theology** (do it while geography's symmetric sacred-site handling is warm) or **economics** (pairs with philosophy; reasoning-kind de-tell). **Save math + grammar for LAST** — they are the snappy-rote exceptions the topic-ladder pipeline fits WORST; don't force the wonder/ladder machinery on them, adapt to short punchy items instead.

**Load-bearing per-subject forks (do NOT reuse blindly):** the DE-TELL rubric must match the subject KIND — KNOWLEDGE (`science`/animal/cooking/geography) keys "deduce-from-stem = tell"; REASONING (`economics`/philosophy) keys "reasoning-to-the-answer = the skill." Fork `_detell.wf.js` + the audits per subject, and calibrate the total-record char caps in the config `tier_note` to the subject's `SUBJECT_TIMER` + mode (math 16 s ↔ theology 46 s @ WIS 10 — content must fit the chain/threshold budget).
