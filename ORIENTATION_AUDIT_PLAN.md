# Context Blurb System + Plan

**Date:** 2026-10-03
**Trigger:** Playtest hit on philosophy T1 question about Anselm's wax tablets with zero orientation on who Anselm is. User: *"we need basic context in every question... I warned you that context needed to be in every rung."* Then: *"Write one 'context' blurb for each ladder... the kid can push a button to bring up Context..."*

---

## The design

Every quiz question belongs to a **topic ladder** (one philosopher's ladder, one war's ladder, one scientist's ladder, etc.). Each ladder gets **ONE context blurb** that carries the WHO/WHAT/WHY orientation a 10th-grader needs to make sense of every rung in the ladder.

A player presses `C` during a quiz to open the Context modal, reads the blurb, closes it, and goes back to the question. The math quiz timer pauses while context is open; all other subjects are already untimed.

The context blurb is **authored once per ladder** and is strictly **answer-free** — it establishes general orientation without stating or implying any keyed fact across T1-T5 of that ladder.

### Why this beats the per-stem rewrite

| | Per-stem rewrite | Context blurb per ladder |
|---|---|---|
| Writing effort | ~16,100 stems (P0 banks) | ~400 blurbs |
| Leak-check surface | Every stem individually | One blurb per ladder (author knows full ladder) |
| Stem architecture | Stem carries orient + hook + question | Stem carries hook + question only |
| Player burden | Everyone reads orientation always | Opt-in — skip if you already know |
| Regression risk | High (rewriting ~16K stems) | Near-zero (stems unchanged, additive data) |
| Future-proof | Must enforce per-stem forever | Add `ladder_context` to pipeline schema; one gate |

---

## The hard rules

### Rule 1 — one blurb per topic ladder

The `topic` field already groups questions into ladders. Every unique topic gets one `context_blurb` string.

Blurb structure (3-5 sentences, ~200-400 words):

1. **WHO** — name/era tag: *"Anselm of Canterbury was an 11th-century Christian monk and archbishop."*
2. **WHAT** — their known-for / the ladder's subject: *"He is remembered for one strange, elegant argument that tries to prove God exists using nothing but pure reason — no scripture, no observations of the world, just a definition and some logic."*
3. **WHY** — the hook / stakes: *"The argument has been attacked and defended for a thousand years, and philosophers still disagree about whether it works."*
4. (Optional) **SETTING** — the time/place scaffolding the ladder's rungs draw on: *"Anselm wrote it down while he was prior at Bec Abbey in Normandy. The result was a little book called the Proslogion."*

### Rule 2 — the blurb MUST NOT leak any T1-T5 keyed answer

Before shipping, every blurb is cold-reader tested: feed the blurb + the four choices from each rung in the ladder to a judge LLM; if the judge can pick the keyed answer at better than chance (25% for 4 choices) across the ladder's rungs, the blurb leaks and must be rewritten.

**Positive example (Anselm blurb — safe for all 10 Anselm rungs across T1-T5):**
> "Anselm of Canterbury was an 11th-century Christian monk and later archbishop. He is remembered for one strange, elegant argument that tries to prove God exists using nothing but pure reason — no scripture, no observations of the world, just a definition and some logic. The argument appears in a little book called the Proslogion, written while he was prior at Bec Abbey in Normandy. Anselm already believed in God deeply before he wrote a word of it; his motto was that he believed so he could understand, not the other way around. The argument he landed on has been attacked and defended for a thousand years — including a famous reply from a monk named Gaunilo and a later critique from Immanuel Kant — and philosophers still disagree about whether it works."

Notice this blurb says NOTHING about:
- The specific starting definition Anselm chose (T3 question)
- The specific ranking Anselm relied on (T4 question)
- How Anselm's book finally survived (T1 question — parchment vs wax)
- Gaunilo's specific counter-example (T4 question — a lost island)
- Kant's hundred-coins example (T4 question)
- Anselm's second-move "necessary existence" argument (T5 question)

The blurb gives orientation (WHO, WHAT, WHY) without touching any of the keyed facts the ladder tests.

### Rule 3 — stems still need to be coherent as questions

Stems don't need WHO/WHAT/WHY front-matter anymore — the blurb carries that. But a stem must still make sense as a standalone question. A stem that reads "What did he choose?" without any noun to anchor "he" is still broken. The light stem audit (Phase 4) catches these — expected flag rate ~5-10%, not the 50-80% of the old stem-rewrite plan.

### Rule 4 — context is OPT-IN but DISCOVERABLE

- Button on the quiz panel: `[C] Context` (visible on every quiz).
- First-time encounter of a NEW topic in a session: auto-opens the context modal once (one-shot per topic per session).
- Subsequent encounters: hint only. Player presses C if they want.
- Math timer pauses while context modal is open. Other subjects are untimed so no pause needed.

### Rule 5 — ladder context must survive future bank rebuilds

The `bankbuild/` pipeline must require a `ladder_context` output for every topic ladder. Future bank builds without a passing blurb → gate fail → no ship.

---

## Why orientation regressed before (unchanged — root causes stay valid)

1. **Ladder-authoring produces ladder-coherent content, not question-coherent content.** Agents mentally scaffold rung 1, then let later rungs lean on it. The engine shuffles. The context-blurb design SOLVES this directly: the "scaffold" now lives in a durable, accessible place.
2. **`context` field was audit-time only.** Players never saw it. The new modal makes the orientation visible.
3. **`PIPELINE.md §16` was advisory, not a gate.** Phase 0 fixes this.
4. **MEMORY.md didn't carry the rule as a top-level bullet.** Phase 0 adds it.
5. **2026-09 audit was scoped to answer-correctness.** This plan is the orientation-dimension audit.

---

## The plan — 6 phases

### PHASE 0 — Lock the rule (prevents regression)

- New memory bullet: `feedback_ladder_context_blurb.md` → referenced from MEMORY.md. Rule: every topic ladder gets one `context_blurb` field; blurb carries WHO/WHAT/WHY; blurb must NOT leak keyed answers; players read it opt-in via a C-key modal.
- `bankbuild/PIPELINE.md §16` rewritten from advisory to a **hard pipeline gate**. Any bank build without `ladder_context` for all topics → fails the gate.
- `bankbuild/bank_pipeline.wf.js` adversarial judge adds the leak-check: cold-reader LLM gets the blurb + the 4 choices from each rung in the ladder; if accuracy > 25% on any rung, blurb fails and the ladder re-enters the authoring queue.
- `CLAUDE.md` "Rebuilding a Quiz Bank" section updated to reference the new rule.

**Agents:** 1 small Opus agent for the rule-lift work.

### PHASE 1 — Data-model + UI design doc

Short design doc at `docs/design/context_blurb_system.md`:
- Does `topic` field exist on every question today, and is it unique per ladder? **Verify** — this is the join key.
- New data file: `data/question_contexts.json` keyed by `topic` → `{context_blurb: "..."}`. Alternative: inline `context_blurb` on the first question in each ladder. **Decision needed** — standalone file is cleaner for pipeline authoring; inline is simpler for one-file loading. Lean standalone file.
- Load path: on game start, read `question_contexts.json` into a `topic → blurb` dict.
- UI: Context button + modal design (match the lore-dossier modal style).
- Keybind: `C` in `STATE_QUIZ` → open context modal.
- Timer handling: math timer pauses on modal-open, resumes on modal-close.
- Auto-open-once-per-session: track a per-session set of topics the player has seen; auto-open on first-ever encounter per session.

**Agents:** 1 Opus agent for the design doc.

### PHASE 2 — Implement the UI

- Add `data/question_contexts.json` (empty skeleton) and loader in `quiz_engine.py` or `main.py`.
- Add `STATE_QUIZ_CONTEXT` state (modal), input handler, draw function.
- Wire `C` key dispatch in `game_input.py` to open the context modal from within a quiz.
- Wire math-timer pause/resume on open/close.
- Wire first-time-this-session auto-open behavior.
- Add tests: context modal opens, timer pauses on math, timer resumes on close, context data loads cleanly.

**Agents:** 1 Opus agent for the UI implementation + tests.

### PHASE 3 — Author the context blurbs

Priority order (user-confirmed):

| Priority | Bank | Est. topics | Est. blurbs |
|---|---|---|---|
| 1 | philosophy | ~90 | ~90 |
| 2 | history | ~150 | ~150 |
| 3 | economics | ~90 | ~90 |
| 4 | ai | ~60 | ~60 |
| 5 | theology | ~80 | ~80 |
| 6 | geography | ~100 | ~100 (partial; place-anchored ladders may be a 1-sentence stub) |
| 7 | science | ~110 | ~110 |
| 8 | trivia | ~60 | ~60 |
| 9 | animal | ~80 | ~80 (short; the animal is self-anchoring) |
| 10 | cooking | ~80 | ~80 (short; the ingredient/dish is self-anchoring) |
| skip | math | — | — (snappy-rote) |
| skip | grammar | — | — (snappy-rote; vocab-teaching T1-T3 already does this) |

**Totals: ~900 blurbs across 10 banks.** (Topic counts are estimates — Phase 3 agents verify by reading the actual `topic` field distribution.)

10 parallel Opus agents, one per bank. Each:
- Reads its bank's `data/questions/<subject>.json`.
- Enumerates distinct `topic` values + the questions in each.
- For each topic, authors a WHO/WHAT/WHY blurb.
- Runs the self-check (cold-reader against every rung's choices).
- Writes to `data/question_contexts/<subject>.json`.
- Produces a report at `docs/audits/context_blurbs_<bank>_YYYY-MM-DD.md`.

**Checkpoint before Phase 4:** User reviews a sample of blurbs from each bank. Spot-check: pick a random blurb + random rung, verify the blurb doesn't leak the keyed answer, verify the WHO/WHAT/WHY are solid.

### PHASE 4 — Lightweight stem coherence sweep

Flag stems that are literally meaningless as standalone questions. Expected flag rate ~5-10%. Rewrite the few that need it (keep answer + distractors; just make the stem a coherent question).

10 parallel Opus agents, one per bank, mostly reading. Each produces a flag list + minimal rewrites.

### PHASE 5 — Re-gate, test, ship v2.19.0

- Run existing bank gate validator against each updated bank.
- Run full pytest suite + new context-modal tests.
- Commit everything.
- Bump version to v2.19.0 (major content/UX release).
- Tag + push → CI builds Windows setup + Linux AppImage → GitHub Release.

### PHASE 6 — Verify the gate holds

- Confirm `bankbuild/bank_pipeline.wf.js` adversarial judge blocks orientation-fail blurbs on new builds.
- Confirm MEMORY.md carries the bullet.
- Confirm CLAUDE.md points at the rule.
- Document how to add a new topic ladder with its blurb in `bankbuild/PIPELINE.md §16`.

---

## Hard constraint, repeated for every Phase 3 agent

**The context blurb MUST NOT state, paraphrase, or trivially imply the keyed answer of any rung in its ladder.**

Mechanical self-check given to every Phase 3 agent:

> After writing a blurb, iterate through every question in the ladder. For each question, read ONLY the blurb + the 4 choices (no stem). If the keyed answer is distinguishable from the distractors at better than 1-in-4 chance, your blurb has leaked and must be rewritten. All four choices on every rung must remain plausible from the blurb alone.

The adversarial judge in `bank_pipeline.wf.js` (Phase 0) enforces this as a shipping gate.

---

## Cost estimate

- Phase 0: 1 Opus agent — minutes
- Phase 1: 1 Opus agent (design doc) — minutes
- Phase 2: 1 Opus agent (UI implementation) — 30-60 min
- Phase 3: 10 parallel Opus agents (blurb authoring) — 1-2 hours wall time
- Phase 4: 10 parallel Opus agents (lightweight stem sweep) — 30-60 min
- Phase 5: me, direct — 15 min
- Phase 6: me, direct — 10 min

**Total: ~23 Opus agent sessions, ~2-4 hours wall-time, mostly parallel.**

Memory rule: `No API spend, explicit Opus — all LLM work via Claude Code Opus subagents`. All agents will carry `model: 'opus'`.

---

## Open decisions still awaiting your call

1. **Context data layout** — standalone `data/question_contexts.json` (clean for pipeline authoring, my preference) vs. inline `context_blurb` on first-question-of-each-topic (one less file to load)?
2. **Keybind** — `C` during quiz, OK? Nothing else is bound in `STATE_QUIZ` input except `1-4`, `SPACE`, `ESC`.
3. **Auto-open on first encounter** — once per session per topic (my proposal), or always-manual (`C` only)?
4. **Checkpoint after Phase 3** — review a sample of blurbs before I fire Phase 4? (I say yes.)
5. **Pedagogical core preservation during Phase 4 stem rewrites** — if a stem needs fixing, must keep the answer's reasoning move intact (not just the answer string)? (I say yes.)
6. **Priority ordering** — is the P0 → P1 → P2 ordering above correct, or do you want all 10 banks fired at once in Phase 3?

Give me the calls and I fire Phase 0 immediately.
