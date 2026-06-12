# Bank Rebuild Plan — a repeatable, research-grounded, register-driven harness

## The root cause this fixes
Questions come out bland *over and over* because every pass is a **one-off**: hand-craft or a
throwaway swarm, judged in isolation, no memory, no coverage target, no research. Same failures
recur because nothing in the loop *prevents* them. This plan replaces that with a **pipeline** —
each failure mode we've found is killed by a specific, repeatable stage, and the whole thing runs
identically for every subject. It is built repeatable from line one: real code in a package, file
state between stages, calibration gates before scale.

## The unit is the TOPIC LADDER (not the question)
Per `memory/feedback_topic_ladders.md`: a keystone subject (Joan of Arc, Lincoln, Saratoga…) is a
**mini-bank** spanning T1→T5, one fact per rung, slotted by *conceptual difficulty* not obscurity,
balanced ~equal rungs per tier, stakes-in-stem, self-contained (shuffled deck), downward-only
scaffold. `JOAN_LADDER_PROTOTYPE.md` is the blessed template.

---

## The pipeline (7 stages)

Legend: **[LLM]** = Opus subagent swarm · **[DET]** = deterministic Python (testable, version-
controlled) · **[YOU]** = human gate. Every stage reads the prior stage's file and writes its own,
so any stage is independently re-runnable and inspectable.

### Stage 0 — REGISTER: the canon of what SHOULD exist  **[LLM-draft → YOU-bless]**
*The robustness step — coverage is measured against a target, not left to chance. **Two sources,
two jobs: social consensus picks the TOPICS (breadth); your moral vision governs the FRAMING and
guarantees the must-haves.** The framework/vision docs are a philosophy, not a curriculum index —
using them as the topic list would make a parochial bank.*

- **0a — Coverage from the social-consensus canon (WHAT exists).** Web-grounded against the broadly-
  agreed body a well-educated kid should be exposed to in the discipline: standard curricula (Core
  Knowledge, AP / national outlines), cultural-literacy canons, major encyclopedia topic maps. Sets
  BREADTH; deliberately NOT limited to what our docs enumerate. (French Revolution, Roman Empire,
  Industrial Revolution, WWII, the Constitution… in because the world agrees a kid should know them.)
- **0b — Moral-vision overlay (HOW each topic is taught + non-negotiable inclusions).** Apply
  `moral_vision.md` + `HISTORY_FRAMEWORK.md` to each consensus topic: attach a **framing / voice /
  stance note** (the Terror counted honestly; the Industrial Revolution's real human progress
  celebrated), plus **mandated inclusions and weights** the neutral base under-emphasizes (communist
  death toll, the American founding, the Western tradition as achievement). Selection stays broad;
  the vision sets the angle and guarantees the non-negotiables — it adds and weights, it never hides
  history.
- **0b is a FLOOR, not just an overlay:** the vision doesn't only annotate consensus topics — it
  **injects** topics the consensus omitted and **expands/upweights** ones it minimized, whenever
  `moral_vision.md`/`HISTORY_FRAMEWORK.md` say a topic matters (flagged `vision_mandated` so you see
  them). It can add and upweight; it cannot subtract canon.
- **0c — Granularity (ladder-sized).** Broad topics are too coarse for wonder — the reality lives in
  the specifics. Decompose them: "WWII" → D-Day, Midway, the Blitz, Enigma, the Holocaust,
  Hiroshima… Each entry is tagged `kind`: **LADDER** (fact-dense keystone → full T1–T5 ladder, e.g.
  Joan, Lincoln, D-Day) or **STANDALONE** (a one-off gem → 1–3 wonders, e.g. the Rosetta Stone).
- Each register entry: topic · `kind` (ladder/standalone) · weight · target tier-span · **framing
  note (moral-vision)** · `vision_mandated` flag · source (which curriculum/canon put it on the
  list) · 1-line rationale.
- **YOU bless/edit the register.** Highest-leverage human gate — small; defines comprehensiveness
  AND the per-topic stance for the whole subject in one pass.
- Out: `bankbuild/history/register.json` (~200–350 topics once consensus breadth is in).
- **Kills:** sparse / *parochial* coverage (a bank limited to what the docs listed); AND values-drift
  (every topic carries its framing note from the start).

### Stage 1 — INVENTORY: what the bank HAS  **[LLM cluster]**
- Assign every existing question to a topic (or `orphan`) via a clustering swarm; reuse the 47
  dup-clusters the pilot already found as seeds.
- Out: `bankbuild/history/inventory.json` (topic → [qids], tiers covered, count).
- **Kills:** invisible duplication (same-fact-across-tiers); orphan/off-canon questions.

### Stage 2 — GAP ANALYSIS: register − inventory  **[DET]**
- Pure set math + thresholds. Each register topic is classified:
  `MISSING` (build from scratch) · `THIN` (1–2 Qs, no ladder → extend) · `BLOATED` (the dup
  clusters → collapse into one ladder) · `OK`. Orphans → `ADD-TO-REGISTER` or `CUT`.
- Out: `bankbuild/history/worklist.json` — the prioritized build queue.
- **Kills:** building blind; wasted effort on already-good topics.

### Stage 3 — RESEARCH: the part that makes it STICK  **[LLM + web, then VERIFY]**
*The anti-blandness engine. This is what I've never had — it's why "name the document" keeps
winning over the fairy tree and the grace-trap answer.*
- Per topic, a research agent (WebSearch/WebFetch to real sources — encyclopedias, primary-source
  archives, trial records) builds a **fact sheet**: each fact + **source** + a conceptual-difficulty
  tag (village-tree = easy; trial-law = hard) + a **legend/confidence flag**.
- **VERIFICATION pass [LLM-judge + DET]:** every sticky fact must trace to a source; unverifiable
  claims are dropped or tagged "handle with tongs" (the executioner-testimony rule); legend is
  labeled as legend. *Nothing fabricated reaches a kid — non-negotiable.*
- **Calibrated 2026-06-09 on Joan: zero hallucinations, strong sourcing, excellent legend discipline →
  READY. Enhancements folded in to close the recall gap:** (1) a **material-culture / object sub-pass**
  (rings, charms, scabbards, the standard — the narrow physical gems a breadth-first sweep misses);
  (2) a **disputed-ATTRIBUTION sub-pass** distinct from miracle-legend (contested letters/quotes — who
  doubts them, on what grounds); (3) **dedup/canonicalize** before output (73 raw → ~30 distinct);
  (4) **run the topic's known-gem list as a recall harness**, with a stated reason for any miss;
  (5) require **≥1 named primary-source URL per fact** + a structural **"documented-shell vs
  unverifiable-core" hedge field** (not prose).
- Out: `bankbuild/history/research/<topic>.json`.
- **Kills:** bland label payoffs; fabricated specifics (failure mode 7); "is there no cooler fact?"

### Stage 4 — LADDER AUTHORING  **[LLM]**
- From the verified fact sheet, author the ladder to the Joan spec: one fact per rung; difficulty-
  slotted; balanced per tier; stakes-in-stem; self-contained; downward-only scaffold; ages/dates as
  scenery, quotes/named-things as payoffs; legend taught as legend.
- Out: `bankbuild/history/ladders/<topic>.json`.

### Stage 5 — JUDGE PANEL (calibrated)  **[LLM panel]**
- The 5 calibrated judges (Integrity, Wonder+§19, Values, **Rand 9/9**, Tier) **+ two new judges:**
  - **LADDER judge** (recast dedup): does the ladder *build*? no repeated fact? balanced tiers?
    downward-only scaffold respected? each rung's answer the coolest fact of *its* question?
  - **FACT judge**: does each keyed answer match the research sheet's sourced facts?
- Out: `bankbuild/history/verdicts/<topic>.json` — keep / rewrite / cut per rung + ladder verdict.
- **Kills:** axis mismatch, telegraphing, contested-verdicts, rote-at-wrong-tier, in-vacuum questions.

### Stage 6 — GATE + INTEGRATE  **[DET]**
- Survivors → existing deterministic gates (`tools/quizgen` length/parity/schema/dup) → merge into
  `data/questions/history.json` with a changelog. The save machinery picks them up automatically
  (proven: seen-set only, decks rebuild from JSON).
- Out: updated bank + `bankbuild/history/CHANGELOG.md`.

---

## The harness (why it's repeatable, not another one-off)
1. **Real package, not scratch:** `tools/bankbuild/` (sibling to `tools/quizgen/`) holds the [DET]
   stages + the Workflow scripts for [LLM] stages + a CLI: `py -m tools.bankbuild <subject> <stage>`.
   Deterministic stages get unit tests. *This is the difference from every prior pass.*
2. **File-state between stages:** `bankbuild/<subject>/*.json`. Any stage re-runs from the prior
   file; nothing is held only in a chat. Inspectable, diffable, resumable.
3. **Parameterized by subject:** identical run for history → animal → cooking → … Only the register
   and framework doc change.
4. **Calibration before scale (each LLM stage):** the research agent is calibrated against the
   **Joan gold sheet you provided** — if it can't independently surface the fairy tree, the grace-
   trap answer, and the sword at Sainte-Catherine, its prompt/sourcing is fixed *before* it runs on
   250 topics. Judges are already calibrated (the Ladder + Fact judges get a calibration set too).
5. **Human gates are small and high-leverage:** bless the register (Stage 0), bless the prototype
   ladder (done), spot-check a sample after Stage 5. You never review 16k questions; the harness does.

## Failure-mode → stage map (the system is designed against the *actual* problems)
| Recurring failure | Killed by |
|---|---|
| Bland / label payoff; "no cooler fact" | Stage 3 Research + Wonder/Rand |
| Fabricated specifics | Stage 3 Verification + Fact judge |
| Sparse / missing coverage | Stage 0 Register + Stage 2 Gap |
| Same fact across tiers / dups | Stage 1 Inventory + Ladder judge |
| Rote minutiae at wrong tier | Stage 4 difficulty-slotting + Tier judge |
| Question in a vacuum (a name, not a person) | Stage 4 ladder authoring from fact sheet |
| Not self-contained / stakes buried | Stage 4 authoring spec (shuffled-deck + §14) |
| Axis mismatch, telegraphing, contested verdict | Stage 5 Integrity / Values judges |

## Honest scale, cost, risk
- **Robust = bigger, but depth is VARIABLE.** Whole-bank target ≈ **5,000 great questions**, not max
  count. Depth per topic: **DEEP** (~10–15 rungs) for canonical keystones (Joan, Founders, Rev War,
  Civil War); **STANDARD** (~3–5) for most topics — compress connective context into the stem,
  spend rungs on the most memorable facts; **STANDALONE** (~1–3) for one-off gems. The register's
  `depth` field + your pruning are the levers that land it near 5,000. Across all subjects this is a
  multi-session program; built weight-prioritized and phased so we review between phases.
- **Order:** prove on **history** end-to-end first (one subject, all 7 stages), then template to the
  rest. Within history: do ~3 keystone ladders first (Joan ✓, + Lincoln, + Washington), you grade
  them, *then* unleash the full register.
- **Biggest risk = research hallucination.** Mitigated by mandatory source-grounding + the Fact
  judge + the legend flag. If a fact can't be sourced, it doesn't ship. We calibrate this risk
  explicitly on Joan before trusting it.
- **Web dependency:** Stage 3 needs WebSearch/WebFetch. If a topic can't be researched online to
  the needed depth, it's flagged for you rather than faked.

## What I need from you to start
1. **Green-light the pipeline shape** (or correct it).
2. **Register source call:** auto-draft the history register **two-source** — consensus canon
   (web-grounded, breadth) + moral-vision overlay (framing note + must-haves) — for you to edit
   (recommended), vs. you hand it to me.
3. **Scope call:** confirm the bank may *grow* substantially for robustness (vs. a fixed cap).
4. Then Stage 0 (draft register) + a Stage 3 research **calibration run on Joan** are the first two
   moves — cheap, and they prove the two riskiest new pieces before any scale.
