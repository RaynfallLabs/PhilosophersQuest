# Philosophy Bank Rewrite Plan (2026-05-20)

Based on `PHILOSOPHY_FRAMEWORK.md`. Current bank: 1139 active questions.

## Audit (machine-classified, manual spot-checked)

| Tier | NAME_RECALL | SCENE_LED | FALLACY | LONG_ABSTRACT | OTHER | Total |
|---|---:|---:|---:|---:|---:|---:|
| T1 | 27 (14%) | 45 (23%) | 0 | 3 | 125 | 200 |
| T2 | 78 (39%) | 14 (7%) | 2 | 17 | 89 | 200 |
| T3 | 116 (50%) | 3 (1%) | 4 | 70 | 41 | 234 |
| T4 | 151 (51%) | 1 (0.3%) | 4 | 113 | 28 | 297 |
| T5 | 106 (51%) | 0 | 13 | 65 | 24 | 208 |

**Headline numbers**:
- 478 questions (42%) are name-recall pattern → fail framework rule 1
- 268 questions (24%) have answers > 100 chars → fail length budget
- 63 questions (5.5%) are scene-led → far below target
- 23 fallacy questions across 1139 → target is ~230 (20%)
- T4 has SINGLE scene-led question out of 297

Answer length p90 by tier: T1=84, T2=114, T3=137, T4=161, T5=158.
Framework caps: T1=60, T2=80, T3=100, T4=110, T5=120. **Every tier T2-T5
exceeds the cap at p90.**

## Verdict on existing content

| Verdict | Count | Action |
|---|---:|---|
| **KEEP** | ~265 (23%) | Already framework-compliant — T1 scene-led + a few good T3-T5 thought experiments. |
| **REWRITE_KEEP_TOPIC** | ~478 (42%) | Name-recall stems with valid underlying ideas. Lift the idea into a scene; move the name to context. |
| **TRIM_ANSWERS** | ~150 (13%) | Question is fine, but the answer + distractors are too long. Trim choices to budget. |
| **DROP** | ~150 (13%) | Doctrine fragments where the kid has no foothold (Avicenna essence/existence, Nagarjuna emptiness-of-emptiness). Keep in dropped/ as source material. |
| **GENERATE_NEW** | ~96 fill | Replace dropped + bring fallacy ladder to 230 questions. |

## Goal after rewrite

| Tier | Current | Target | Pattern |
|---|---:|---:|---|
| T1 | 200 | 200 | mostly KEEP — only 27 name-recalls to rewrite |
| T2 | 200 | 220 | major rewrite — 78 name-recalls + thin fallacies; pad fallacy count |
| T3 | 234 | 230 | major rewrite — 116 name-recalls + 70 long-answer; flatten to thought-experiment scenes |
| T4 | 297 | 220 | LARGE rewrite + drop — 151 name-recalls + 113 long-abstract. Drop ~80 doctrine-fragment, rewrite the rest |
| T5 | 208 | 210 | major rewrite — 106 name-recalls. Newcomb / brain in vat / original position / Mary's room pattern |
| **TOTAL** | **1139** | **1080** | net -59, but quality not quantity |

Target shape after rewrite:
- 60% scene-led (was 5.5%)
- 20% fallacy (was 2%)
- 20% other (definitions checked against framework — must be conceptual not vocab)
- 0% name-in-stem (was 42%)

## Phased rewrite plan

### Phase 0 — Framework lock-in (DONE in this commit)
- `PHILOSOPHY_FRAMEWORK.md` written
- This plan committed
- A memory entry saved so future rebuilds don't repeat the drift

### Phase 1 — Tooling (next session, est. 1 hour)
- Build a `philosophy_scorer.py` in `tools/quizgen/scratch/`:
  - `is_name_in_stem(q)` → returns the philosopher name if found, else None
  - `is_long_answer(q)` → length > tier cap
  - `is_scene_led(q)` → first-sentence subject is a person/action, not a name
  - `is_fallacy(q)` → fallacy keyword anywhere
- Run scorer over the bank, produce per-question verdict CSV
- Spot-check 30 KEEP, 30 REWRITE, 30 DROP — confirm classifier agrees with human read

### Phase 2 — DROP the doctrine fragments (~30 min, ~150 questions)
- Move classifier-flagged DROP set to `data/questions/dropped/philosophy.json`
- Avicenna essence/existence, Nagarjuna emptiness-of-emptiness, Plotinus
  on the One, Ricoeur narrative identity, Heidegger fundamental ontology, etc.
- These were technically correct content at college level. Not 5th-10th grade.

### Phase 3 — TRIM the long answers (~1 hour, ~150 questions)
- For each TRIM_ANSWERS question: write a tighter answer + tighter
  distractors at the tier's cap. Same idea, shorter sentence.
- Validate after every batch with the new `q()` helper.

### Phase 4 — REWRITE name-recalls (LARGEST, ~6-8 hours, 478 questions)
- Per tier, walk the name-recall set:
  - Read the underlying philosophical move
  - Author a scene/thought-experiment that LEADS the player to the same move
  - Move the philosopher name to the context field
- Old question moves to `dropped/philosophy.json` with `_dropped_reason: "name_recall_rewrite"`. New scene-led question takes its slot.
- Generation pattern: 30 questions per batch, validate, save, commit.
- Subagent or in-context — depends on user preference. Recommend in-context (Opus 4.7) given the bank's small enough size and the past trouble with subagents drifting from framework.

### Phase 5 — FALLACY ladder fill (~3 hours, ~210 questions)
- Currently 23 fallacy questions, target 230.
- Author per the tier ladder in framework. Each fallacy gets multiple
  scenarios across tiers (T1 kid-level → T5 motte-and-bailey).
- Heaviest single block of new content.

### Phase 6 — Topic-gap fill (~1 hour, ~30 questions)
- Run topic-coverage checker against the 8-branch × 5-tier matrix
- Each empty (branch, tier) cell gets 1-2 hand-authored fills
- Aesthetics is probably the thinnest — under-represented in current bank.

### Phase 7 — Validation + commit
- `py -m tools.quizgen validate --subject philosophy` → 0 REPAIR / 0 DISCARD
- All 612+ tests pass
- Commit with full report

## Total estimate

- Phase 1: 1 hour
- Phase 2: 30 minutes
- Phase 3: 1 hour
- Phase 4: 6-8 hours (the big one)
- Phase 5: 3 hours
- Phase 6: 1 hour
- Phase 7: 30 minutes

**Total: 12-15 hours of work.** Same order of magnitude as the original
bank-wide quality sweep, but focused on one bank.

## Why we keep failing at this

Honest assessment. Three rebuilds have drifted toward name-recall. The
pattern:

1. **Coverage feels like depth.** A bank with 50 named philosophers
   *looks* deep. The agent prioritizes breadth of names over depth of
   reasoning. The framework needs to explicitly reward fewer names + more
   reasoning per name.

2. **Memory entries weren't specific.** `feedback_no_rote_wonder.md` said
   "no rote in wonder subjects" but defined rote narrowly as
   "capitals/dates/definitions." It didn't say "name + doctrine = rote."
   I'm adding a specific memory for philosophy patterns now.

3. **No upfront framework.** Each rebuild's spec was a short prompt. This
   doc + the BANNED_NAMES enforcement at write time is the fix.

4. **Subagent drift.** Past rebuilds used parallel subagents. They each
   interpreted "scene-led" differently. For Phase 4, recommend doing the
   rewrites in this main Opus context with the framework loaded, batch by
   batch, with the user seeing samples after each batch.

## Decision points for the user

1. **Phase 4 execution**: in-context (slower, higher fidelity to framework)
   or subagents (faster, more drift risk)?
2. **DROP threshold**: aggressive (drop 200, rebuild 200 fresh) or
   conservative (drop 100, rewrite 100 in place)?
3. **Fallacy expansion priority**: 20% target right now, or build to that
   over time?
4. **Schedule**: do this in one push, or break across multiple sessions?

## USER DECISIONS (2026-05-20)

1. **In-context.** High fidelity over speed. No subagents for this work —
   the past three rebuilds drifted via subagent interpretation.
2. **Aggressive drop.** "Fewer good > more ok." Target ~200 drops, rebuild
   ~200 fresh.
3. **Fallacy up to 33%.** User stance verbatim: *"this is critical
   reasoning in today's social media and news environment ... kids need
   to be able to work through an argument logically and find the flaws.
   Philosophy may be a bit of a misnomer... the actual bank should be
   Logic, Reasoning, Debate, and Philosophy."*
   - Bank size target: ~1080 questions
   - Fallacy target: 33% = ~360 questions
   - Current: 23 → need ~337 new fallacy questions
4. **One push** if quality holds; checkpoint at phase boundaries via disk
   saves and commits so context drift doesn't lose work.

**Note on bank identity** (per user's "misnomer" comment): the subject ID
stays `philosophy` for code stability (loader paths, SUBJECT_TIMER, gate
registrations). The CONTENT scope broadens explicitly: Logic + Reasoning
+ Debate + Philosophy. The framework already supports this — the fallacy
ladder + Socratic move emphasis is exactly that scope.

## Revised tier targets (post-decisions)

| Tier | Current | Target | Fallacy share | Non-fallacy |
|---|---:|---:|---:|---:|
| T1 | 200 | 200 | 66 (33%) | 134 |
| T2 | 200 | 220 | 73 (33%) | 147 |
| T3 | 234 | 230 | 76 (33%) | 154 |
| T4 | 297 | 220 | 73 (33%) | 147 |
| T5 | 208 | 210 | 70 (33%) | 140 |
| **TOTAL** | **1139** | **1080** | **358 (33%)** | **722** |
