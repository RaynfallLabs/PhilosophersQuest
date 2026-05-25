# Quiz Bank Rewrite Runbook

The repeatable process for rebuilding or auditing a question bank. Captures the
Pass-1 / Pass-2 / Pass-3 sequence used 2026-05-25 to bring 5 banks (history,
philosophy, cooking, animal, geography) up to ≥96% gate-pass + 100% on
geography. Every step here is exercised by real commits on `main` —
nothing in this runbook is aspirational.

> **Read order**: This runbook assumes you already understand the Wonder
> Pattern (`proposals/v2_audit/SHARED_PRINCIPLES.md §13` + `HISTORY_TEMPLATES.md
> §1`) and the per-subject FRAMEWORK / TEMPLATES under `proposals/v2_audit/`.
> Those are the *what* and *why*. This runbook is the *how*.

---

## What the three passes accomplish

| Pass | Goal | Targets | Cost | Output |
|---|---|---|---|---|
| **Pass 1** | Wonder Pattern audit | scan-flagged candidates + cross-tier collision groups | 1 opus agent / subject | per-subject rewrite JSON |
| **Pass 2** | Same-answer dedup (only needed if many collisions) | every collision group in the bank | 1-3 opus agents / subject (sharded) | per-shard dedup JSON |
| **Pass 3** | Residual gate cleanup (formal violations) | every gate-failing question | 1 opus agent across all banks | per-bank fix JSON |

After all three passes, every rewrite passes the full gate suite. The bank
overall hits 96-100% (residual fails are content the agents *chose not to
touch* — exempt cases or flagged-for-human).

---

## Prerequisites for a new bank

Before any pass, the subject must have:

1. **`proposals/v2_audit/<SUBJECT>_FRAMEWORK.md`** — voice rules, topic
   coverage, register guidance, moral-vision-anchored stance
2. **`proposals/v2_audit/<SUBJECT>_TEMPLATES.md`** — approved stem patterns,
   choice shapes, tier conceptual ladder, anti-patterns
3. **`tools/quizgen/gates/<subject>.py`** — subject-specific gates exposed
   as `PER_QUESTION_GATES: list[tuple[str, Callable]]` and optionally
   `SOFT_WARN_GATES: frozenset[str]`. See `tools/quizgen/gates/history.py`
   as the reference shape.
4. **Per-subject entry in `tools/quizgen/deterministic/length_budget.py`** —
   tier total caps (history/cooking/animal use {500,620,770,900,1100};
   geography is {500,620,770,900,1000}; philosophy is {660,770,930,1100,1200})
5. **Per-subject entry in `tools/quizgen/deterministic/length_parity.py`** —
   include the subject in `ANSWER_OUTLIER_SUBJECTS` if it follows the
   wonder-voice pattern (looser 1.6× answer-outlier rule); otherwise the
   strict 1.30 ratio applies
6. **`SUBJECT_TIMER` entry in `src/player.py`** — chain-mode timer per WIS
   point; calibration must accommodate worst-case stem + 4 choices
7. **(Recommended)** `tools/quizgen/scratch/_<subject>_exemplars.py` — 30
   exemplars (6 pillars × 5 tiers) that all pass the structural gates
8. **Subject exemption decision** for `answer_collision.EXEMPT_SUBJECTS`:
    - Add the subject if templated drills legitimately recur (math, grammar)
    - Add it if the answer IS a canonical concept name and multiple scenes
      legitimately test the same concept (philosophy)
    - Otherwise, leave it on the strict path

---

## Pass-1 sequence (audit-and-rewrite)

The "Wonder Pattern + all-gates audit" pass. Spawn an opus agent that
proposes rewrites for scan-flagged questions; gate-validate every rewrite
before applying; hand-fix anything the gates reject.

### Step 1: Build audit candidates

```bash
py -m tools.quizgen.audit.build_audit_candidates <subject>
# OR
py -m tools.quizgen.audit.build_audit_candidates all
```

This runs 5 heuristic scans:
- `drama_available`: stem has drama keywords AND asks venue/date/label
  (Drama-Available Rule violation candidates)
- `magnitude_pick`: "How many" stem with numeric distractors
- `generic_label`: answer is a place/date/battle-name (Tier-5 banned)
- `single_word_distinction`: all 4 choices differ by ~1 word
- `paraphrased_distractor`: distractor overlaps answer heavily

Outputs: `_audit_<subject>_t1.json`, `_audit_<subject>_t23.json`, `_audit_<subject>_t45.json`

### Step 2: Build collision groups

```bash
py -m tools.quizgen.audit.build_collision_groups <subject>
# OR
py -m tools.quizgen.audit.build_collision_groups all
```

Uses union-find on bigram-Jaccard normalized-answer similarity (threshold
0.70). Outputs: `_collisions_<subject>.json` listing each group with all
member questions. The Pass-1 agent will look at these groups too.

### Step 3: Spawn the Pass-1 audit agent

One opus agent per subject. Required prompt fields (the literal text used
2026-05-25 lives below in [Appendix: Pass-1 Agent Prompt
Template](#appendix-pass-1-agent-prompt-template)).

**Always include `model: "opus"` explicitly** — per
`feedback_no_api_spend.md`, all LLM work goes through Claude Code subagents
with explicit opus.

Run agents in **parallel** (multiple Agent tool calls in a single message)
when handling several subjects at once.

### Step 4: Apply the rewrites

```bash
py -m tools.quizgen.audit.apply_pass1 <subject>
# OR
py -m tools.quizgen.audit.apply_pass1 all
```

For each proposed rewrite:
1. Normalize the input (3 agent schemas handled — see [Agent output
   schema variants](#agent-output-schema-variants))
2. Find the bank target (by `_target_index` if provided, else by prefix
   match, else by substring containment)
3. Try the rewrite at the agent's proposed tier; if any gate fails, retry
   at tier+1 up to T5 before giving up
4. Apply only if `verdict ∈ {PASS, SOFT_WARN}`
5. Reject and log everything else

Writes: `data/questions/<subject>.json` (mutated in place) and
`_pass1_<subject>_log.md` (per-question rewrite log for review).

### Step 5: Hand-fix the rejections

Read the rejection log. For each gate failure, apply the standard fix
pattern from [Common gate failures + fix patterns](#common-gate-failures--fix-patterns).
Write a `_handfix_pass1_<subject>.py` script following the shape of
`_handfix_pass1_rejections.py`:

```python
FIXES = [
    {
        "subject": "...",
        "match_key": "...",
        "fix_note": "...",
        "new_q": {tier, question, answer, choices, context}
    },
    ...
]
```

The script loads each bank, runs `validate_rewrite` on each fix, applies
PASS/SOFT_WARN, and prints REJECT/NOT_FOUND for anything that still fails.
Iterate until everything applies.

### Step 6: Validate + commit

```bash
py -m pytest tests/ -q
```

Then a single per-bank commit with subject-prefixed message:

```
feat(quizgen): Pass 1 — Wonder Pattern + full-gate rewrites for <subject>

Applies N validated rewrites following the Wonder Pattern audit...
```

---

## Pass-2 sequence (dedup-by-diversification)

Only needed if the answer_collision gate flags many groups. After Pass 1
this happens when:
- Pass-1's audit didn't deduplicate (only flagged candidates)
- The subject is NOT in `EXEMPT_SUBJECTS`

For history (72 groups, 189 affected questions) we ran 3 sharded agents in
parallel. For smaller collision sets (under ~20 groups), one agent is
sufficient.

### Step 1: Slice the collisions

```bash
py -m tools.quizgen.audit.slice_collisions
```

Currently hard-coded for history; generalize per-subject when needed.
Default slicing:
- Shard A: groups of size 4-6 (most complex; need most diverse rewrites)
- Shard B: groups of size 3
- Shard C: groups of size 2 (one rewrite per group)

### Step 2: Spawn dedup agents

One opus agent per shard (or one agent total for small subjects). Use
[Appendix: Pass-2 Agent Prompt Template](#appendix-pass-2-agent-prompt-template).
Always explicit `model: "opus"`.

Agents write `_dedup_<subject>_shard_<X>.json`.

### Step 3: Apply with rebuilding indices

```bash
py -m tools.quizgen.audit.apply_pass2_dedup
```

**Critical detail**: this applier **rebuilds the answer-collision index
after every apply**, so within-batch rewrites cannot silently collide with
each other. Pass 1's applier does NOT do this (Pass 1 doesn't typically
introduce new collisions); Pass 2 must.

### Step 4: Hand-fix rejections

Same pattern as Pass 1. The most common Pass-2 rejection is
"agent picked answer X which is already canonical in some OTHER bank
question elsewhere" — the agent only sees its own collision group, not
the full bank. The fix is to pivot to yet another cool fact from the same
scene.

Example from 2026-05-25: agent rewrote Travis at the Alamo to use "Victory
or Death" as the answer, not knowing that "Victory or Death" was already
Washington's Christmas 1776 password at idx 292. Fix: line-in-the-sand
sword gesture (March 3) instead.

### Step 5: Validate + commit

Same as Pass 1.

---

## Pass-3 sequence (residuals cleanup)

After Pass 1 + Pass 2, run a bank-wide validation and clean up any
remaining gate failures — typically formal violations (parity, shape,
overlap) in content the audit agents didn't touch.

### Step 1: Catalog the residuals

```bash
py -m tools.quizgen.audit.build_residuals_report
```

Writes `_residuals_catalog.json` — one record per gate-failing question
with full question + gate-failure reason.

### Step 2: Spawn the residuals-fix agent

One opus agent across all banks. See [Appendix: Pass-3 Agent Prompt
Template](#appendix-pass-3-agent-prompt-template). The prompt includes the
gate-failure → fix-pattern map (lengthen distractors, rephrase answer,
etc.).

Agent writes `_pass3_residuals_fixes.json` with fixes keyed by **explicit
bank index** (not prefix — prefix-collisions are common in the residuals
because choice-shape-parity failures often share opening text).

### Step 3: Apply

```bash
py -m tools.quizgen.audit.apply_pass3_residuals
```

The applier reads the index-keyed fixes, validates each, applies PASS/SOFT.

### Step 4: Validate + commit

Same pattern.

---

## Common gate failures + fix patterns

The fix patterns below are validated against real failures from
2026-05-25's Pass 1 and Pass 2 work.

### `length_parity` (max/min choice ratio > 1.30, or answer-outlier 1.6×)

**Cause**: one choice (usually the correct answer) is much longer/shorter
than the others.

**Fix**: equalize **up** — lengthen the short distractors with content-true
elaboration. NEVER strip the correct answer.

Example (Pass 1, cooking Grace prayer):
- Original distractors at 76-79c, Grace answer at 94c → 15.7% deviation
- Fix: lengthen distractors to 87-88c by appending content-true detail
  ("...each day at sunset time", "...recited at the very end of the
  Catholic liturgy day")

For wonder-subject T5s where answers are scholarly/long, you can
elaborate distractors with scholarly tone ("...; debated since X" or
"...; per Y et al. NNNN").

### `length_budget` (stem or stem+choices over tier cap)

**Cause**: a richer rewrite overflowed the tier's character budget.

**Fix #1**: trim redundancies from the stem.

**Fix #2**: promote to next tier. The Pass-1/Pass-2 appliers do this
automatically via per-tier retry up to T5.

If even T5 overflows, the content needs hard trimming. Context is
**uncapped** by design — push detail into context rather than stem.

### `choice_shape_parity` (skim-tell: only correct answer has dash structure)

**Cause**: the correct answer uses `— X` for a consequence clause while the
3 distractors do not. Kids spot the answer by shape alone.

**Fix**: add `— <consequence>` to all 3 distractors. The follow-up must be
content-true. Example (Pass 1, geography Mariana Trench):
- Correct: "A window in the entry tube cracked — they continued the dive
  anyway"
- Distractor (was): "A ballast hopper jammed open and they fell faster"
- Distractor (now): "A ballast hopper jammed open — they fell faster than
  planned for minutes"

The em-dash equalize-up usually pushes a T1 question over its 525-char
total cap; auto-promote to T2.

### `stem_answer_overlap` (answer reuses 3+ distinctive stem tokens)

**Cause**: the answer literally repeats words from the stem — kids match
by repetition, not by content understanding.

**Fix path A** (prefer): rephrase the answer to drop overlapping tokens.
Example (Pass 1, cooking saffron):
- Stem: "...about how many crocus *flowers* does it take..."
- Answer (was): "About 150,000 hand-picked flowers, three threads each"
- Answer (now): "Around 150,000 of them" (drops "about/flowers/threads")

**Fix path B**: rephrase the stem to drop tokens that appear in the answer.

### `forcing_constraint` (stem too short or too sparse)

**Cause**: the stem doesn't have enough content tokens or character length
to force a choice.

**Fix**: enrich the stem with named anchors (person/date/place/specific
moment phrase). Each tier has a minimum char count (T1=60, T2=90, T3=110,
T4=130, T5=150) AND a minimum content-token count.

### `duplicate` (stem bigram-Jaccard > 0.85 against another question)

**Cause**: the stem is a near-paraphrase of another bank question's stem.

**Fix**: pick a pair to keep (the better Wonder Pattern fit) and rewrite
the other to test a DIFFERENT cool fact from the same scene. The new
stem's first 60 chars must NOT start with the kept question's first 60
chars (to prevent prefix-lookup ambiguity).

### `answer_collision` (answer bigram-Jaccard > 0.70 against another)

**Cause**: same canonical answer text as another bank question, even if
stems differ.

**Fix**: pivot to a different cool fact from the same scene. Always
check `bank[colliding_idx].answer` first to ensure your replacement
doesn't collide further.

For subjects where same-answer-recurrence is by-design (math drills,
philosophy positions), add the subject to `EXEMPT_SUBJECTS` instead.

### `no_verdict_on_contested` (yes/no stem on a contested topic)

**Cause**: the stem asks for a verdict on a topic where reasonable people
differ (metaphysics, mind, aesthetics, religion).

**Fix**: rephrase to position-defended form. Either:
- "Did X cause Y?" → "Which position fits the consensus among modern
  historians on X's role in Y?"
- Or drop the verdict frame entirely and describe a scene with a specific
  cool-fact question.

### `anti_pattern_clear` (banned stem phrasing)

**Cause**: stem matches a banned phrase regex (see
`BANNED_STEM_PATTERNS` in the per-subject gates file). Common offenders:
"In what year", "What is the capital of", "Who was the leader of", "is
still the same".

**Fix**: rephrase the stem with a different structure. Often easiest to
add a scene before the question.

### `stem_pattern_match` (stem isn't recognizably interrogative or directive)

**Cause**: the stem doesn't end with `?` AND doesn't end with one of the
approved imperative/declarative closers (`identify|diagnose|name (the|which)|
choose|select|state|consider|exposes? a tension|asks: did|asks: could|the
(puzzle|case|thought experiment)`).

**Fix**: end the stem with `?` and ensure an interrogative word is
present (`which|what|how|why|where|identify|diagnose|name|did|does|do|
is|are|was|were|can|could|should|would`). Or use an approved closer.

### `scenario_anchored_correct` topic-inference false positive

**Cause**: the philosophy topic-inference uses keyword counting, and
substring matches can misfire. E.g. "psychological" contains "logical",
which is a logic_fallacy keyword.

**Fix**: rephrase context to drop the offending substring. E.g.
"psychological continuity" → "mental continuity".

### `register_consistency`

**Cause**: vocab register mismatch between stem and choices.

**Fix**: pull the choice register up or down to match the stem's. Don't
mix academic vocab in answers with picture-book vocab in stems.

---

## Agent output schema variants

We've seen three agent output schemas in the wild. The applier's
`_normalize_rewrite` handles all three:

### Schema A (history-style — preferred)

```json
{
  "question_prefix": "first 60 chars of original stem",
  "tier": 3,
  "promote_to_tier": null,
  "new_question": "stem text",
  "new_answer": "answer text",
  "new_choices": ["answer", "d1", "d2", "d3"],
  "new_context": "context",
  "rationale": "..."
}
```

### Schema B (animal-style)

```json
{
  "match_key": "first 60 chars of original stem",
  "tier": 1,
  "issue": "rationale",
  "new_question": {
    "tier": 1,
    "question": "...",
    "answer": "...",
    "choices": [...],
    "context": "..."
  }
}
```

### Schema C (geography-style)

```json
{
  "match_key": "...",
  "tier": "1",          // string, not int
  "reason": "rationale",
  "rewrite": {
    "tier": 1,
    "question": "...",
    "answer": "...",
    "choices": [...],
    "context": "..."
  }
}
```

### Extra field that any schema may include

```json
"_target_index": 462    // explicit bank-position lookup, takes priority
```

The Shard-A history-dedup agent added this when 60-char prefixes
collided across collision-group siblings. The applier prefers this when
present, falls back to `startswith(match_key)`, then to substring
containment.

To reduce future schema drift, **always include the schema A
specification in the agent prompt** (as the prompt template does).

---

## Validation harness usage

The universal validation harness sits in `tools/quizgen/audit/validate.py`:

```python
from tools.quizgen.audit.validate import (
    build_bank_indices, validate_rewrite,
)
import json

bank = json.loads(open(f"data/questions/{subject}.json", encoding="utf-8").read())
dup_index, answer_index = build_bank_indices(bank)

new_q = {tier, question, answer, choices, context}
result = validate_rewrite(
    subject,
    new_q,
    bank=bank,
    dup_index=dup_index,
    answer_index=answer_index,
    replace_idx=target_idx,    # so the question isn't flagged against its old self
)
# result["verdict"] in {"PASS", "SOFT_WARN", "FAIL"}
# result["hard_fails"] = [(gate_name, reason), ...]
# result["soft_warns"] = [(gate_name, reason), ...]
# result["all"] = full audit trail
```

Use this for any one-off validation — including ad-hoc inspection,
hand-fix scripts, and bank-wide post-pass surveys.

---

## When to add a subject to `EXEMPT_SUBJECTS`

`tools/quizgen/deterministic/answer_collision.EXEMPT_SUBJECTS` skips the
collision gate. Current members: `math`, `grammar`, `philosophy`.

Add a subject if **either**:
1. Templated drills legitimately produce same-answer recurrence ("5+7=?
   → 12" recurs across math; "verb tense of 'ran' → past" recurs across
   grammar), OR
2. The answer IS a canonical concept name and multiple legitimate scenes
   pedagogically test the same concept (philosophy's "Memory continuity"
   tested via Ship of Theseus, Parfit teletransporter, Locke
   prince-and-cobbler, etc.).

Add a test (`test_answer_collision_exempt_<subject>`) following the
pattern in `tests/test_quizgen_deterministic.py:626`. It should construct
two same-answer questions and assert `r.status == GateStatus.NA`.

---

## Cost notes

Per `feedback_no_api_spend.md`, all LLM work uses Claude Code opus subagents.
Empirical token + time costs from the 2026-05-25 run:

| Agent type | Tokens | Time | Output |
|---|---:|---:|---|
| Pass-1 audit (per subject) | 150-285k | 8-26 min | 1-55 rewrites + flags |
| Pass-2 dedup (per shard) | 200-275k | 16-28 min | 35-44 rewrites |
| Pass-3 residuals (cross-bank) | ~150-300k | 15-30 min | ~55 fixes |

Total for the 2026-05-25 5-bank work: 4 Pass-1 + 3 Pass-2 + 1 Pass-3 = 8
opus agents, ~2M tokens total. Apply + hand-fix + validation is all
deterministic and costs nothing.

For each new bank, expect: 1 Pass-1 agent (always), 1-3 Pass-2 agents
(only if many collisions), 1 Pass-3 agent (always). Total: 2-5 opus
agents per bank.

---

## Anti-patterns to avoid

These were learned the hard way in earlier sessions; documenting them
here so future runs don't relearn:

### "I'll let the agent self-validate"

The agents almost always claim "all gates pass" in their final report and
the applier rejects 10-40% of their proposed rewrites. The independent
validator is non-negotiable.

### Stripping the correct answer to fix parity

"Equalize up, never strip down." Removing detail from the correct answer
is the most common way to break the Wonder Pattern. The cool fact lives
in the answer; protecting that is the whole point.

### Cosmetic-only "fixes"

When the agent fixes a question by stripping em-dashes or shortening
distractors but doesn't actually change the underlying answer, the
Wonder Pattern is destroyed for the sake of formal compliance. See
HISTORY_TEMPLATES.md §"Cosmetic-only rewrites" for the four cases
caught 2026-05-24 (Pu Yi, Stradivari, Machu Picchu, Warsaw Ghetto).

### Topic-inference false positives

The philosophy gate's keyword-counting topic-inference matches on
substrings — "psychological" contains "logical" (logic_fallacy keyword)
which can trip `scenario_anchored_correct`. When a gate fires on
content that obviously isn't its target, suspect substring matching.

### Skipping pre-rewrite survey

Always survey the bank with `build_residuals_report.py` BEFORE the
agent runs, so you know what was pre-existing vs. agent-introduced.
This saves an iteration where you spend time investigating gate
failures the agent didn't cause.

### Reading the full agent transcript

Per Agent tool guidance: do NOT read the output JSONL file. It will
overflow context. Use the agent's final summary message and the JSON
artifacts it writes.

---

## Appendix: Pass-1 Agent Prompt Template

Use this verbatim, substituting `<subject>` and any subject-specific
docs. Always launch with `model: "opus"`.

```
You are the Pass-1 audit agent for the Philosopher's Quest <subject> bank.
Your job: review the bank for Wonder Pattern + all-gate compliance, and
propose rewrites for problem questions.

## Required reading FIRST (in order)

1. docs/quiz/moral_vision.md — SUPREME — overrides everything else
2. proposals/v2_audit/SHARED_PRINCIPLES.md (esp. §13 Wonder Pattern)
3. proposals/v2_audit/<SUBJECT_UPPER>_TEMPLATES.md
4. proposals/v2_audit/<SUBJECT_UPPER>_FRAMEWORK.md
5. proposals/v2_audit/HISTORY_TEMPLATES.md §1 (Wonder Pattern bible —
   universal across subjects)
6. tools/quizgen/REBUILD_PLAYBOOK.md

## Input

- `_audit_<subject>_t1.json` — scan candidates at T1
- `_audit_<subject>_t23.json` — at T2-T3
- `_audit_<subject>_t45.json` — at T4-T5
- `_collisions_<subject>.json` — same-answer groups

## Process

1. For each scan candidate: KEEP if it passes Wonder Pattern + all
   gates; otherwise REWRITE (preserve scene, swap to a stronger cool
   fact) or FLAG (if uncertain).
2. For each collision group: KEEP one canonical, REWRITE the others
   with DIFFERENT cool facts (different answer text) from the same
   scene/figure/era.
3. ~30 random unflagged spot-checks for cross-validation.

## Gate compliance — Wonder Pattern + all of these

[full gate list — pipeline + per-subject scratch gates, see master
prompt at tools/quizgen/scratch/__pass1_prompt_template.md]

## Output schema (Schema A)

[JSON spec as shown in the runbook's Schema A section]

## Self-validation before output

[full checklist]

Begin.
```

(For the literal text used in the 2026-05-25 run, see the git history
for the Agent tool calls in commit `be46aa5` and prior.)

---

## Appendix: Pass-2 Agent Prompt Template

Same shape as Pass-1 but mission narrows to dedup-by-diversification.
Key differences:

- Input is a shard of `_collisions_<subject>.json` (groups)
- Output includes `kept_canonicals: [{group_id, kept_index, rationale}]`
  alongside `rewrites`
- Agents should explicitly check that their proposed answer doesn't
  match any OTHER bank answer (not just their group's canonical)
- For groups where the agent can't see the full bank, the applier's
  collision check is the safety net

Full template is in the dedup-shard Agent calls in commit `b0af038`.

---

## Appendix: Pass-3 Agent Prompt Template

Mission: hand-fix every gate-failing question across all banks.

- Input: `_residuals_catalog.json` (output of `_build_residuals_report.py`)
- Output: `_pass3_residuals_fixes.json` keyed by explicit `index`
  (not prefix — prefix collisions are common in choice-shape-parity
  residuals)
- The prompt embeds the gate-failure → fix-pattern map from
  [Common gate failures](#common-gate-failures--fix-patterns)
- Agent must self-validate against the same gate suite before output

Full template is in the Pass-3 Agent call in commit `<TBD post-Pass-3>`.

---

## Maintenance: adding a new subject

When adding subject `N` (not in current 5):

1. Author `proposals/v2_audit/<N>_FRAMEWORK.md` + `<N>_TEMPLATES.md`
2. Write `tools/quizgen/gates/<n>.py` exposing `PER_QUESTION_GATES`.
   Reuse subject-agnostic gates from `tools.quizgen.gates.philosophy`
   and `tools.quizgen.gates.cooking` where applicable.
3. Add `<n>` to `_GATE_MODULES` in `tools/quizgen/audit/validate.py`
4. Add length-budget + length-parity entries
5. Decide on `EXEMPT_SUBJECTS` membership
6. Build ~30 exemplars and ensure they pass the structural gates
7. Generate initial T1-T5 content (per
   `tools/quizgen/REBUILD_PLAYBOOK.md` "Bulk Generation" section)
8. Run Pass 1 → Pass 2 (if needed) → Pass 3
9. Commit, push, update MEMORY.md bank-state entry

---

## Appendix: References

- `docs/quiz/moral_vision.md` — supreme; the bank's soul
- `proposals/v2_audit/SHARED_PRINCIPLES.md` — cross-subject rules
- `proposals/v2_audit/HISTORY_TEMPLATES.md` §1 — the Wonder Pattern bible
- `tools/quizgen/REBUILD_PLAYBOOK.md` — the bulk-generation playbook
- `feedback_no_api_spend.md` — opus-only LLM rule
- `feedback_wonder_pattern.md` — cross-session Wonder Pattern memory
- `feedback_no_content_warping.md` — principles are menus, not checklists
- `feedback_no_delete_validated_content.md` — additive over destructive

---

*Document last calibrated 2026-05-25 after the 5-bank rewrite work.
When the process changes, update both this runbook and any prompts the
runbook references.*
