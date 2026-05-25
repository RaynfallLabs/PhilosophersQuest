# Bank Rebuild Playbook

How to rebuild a quiz subject bank from a small v0 (~500 questions) to a substantive bank (~3000 questions) with consistent voice, distinctive stance, and 99%+ gate-pass rate. This is the proven pattern from the May 2026 rebuild project (all 12 banks).

## Pipeline summary

1. **Scaffolding** — write subject doc, strategies doc, aggregator, register subject in gate config. Commit.
2. **Generation** — spawn 5 tier-agents in parallel (T1-T5). Each writes a Python builder in `scratch/` that emits a JSON batch in `state/queue/generated/`.
3. **Aggregation** — run `_aggregate_<subject>_final.py`. Survivors land in `state/queue/<subject>_final_keep.json` and `data/questions/<subject>.json` (5-field game schema).
4. **Supplement (if needed)** — for under-quota tiers, spawn focused supplement agents writing `<subject>_t<N>_batch002.json`. Re-aggregate.
5. **Validate + test + commit.**

## File layout

```
data/questions/<subject>.json                         # the bank (5-field schema)
data/questions/<subject>.json.backup                  # v0 backup (one-shot at first aggregate)
docs/quiz/subjects/<subject>.md                       # voice + stance + budgets (tracked)
docs/quiz/<subject>_strategies.md                     # 5-pillar taxonomy + strategy slots (tracked)
tools/quizgen/deterministic/length_parity.py          # register subject in ANSWER_OUTLIER_SUBJECTS
tools/quizgen/deterministic/length_budget.py          # register subject in SUBJECT_TIER_BUDGETS
tools/quizgen/state/queue/_aggregate_<subject>_final.py  # aggregator (gitignored)
tools/quizgen/state/queue/generated/<subject>_t<N>_batch001.json  # agent output (gitignored)
tools/quizgen/state/queue/<subject>_final_keep.json   # gate survivors with _meta (gitignored)
tools/quizgen/state/queue/<subject>_final_repair.json # gate failures (gitignored)
tools/quizgen/scratch/_build_<subject>_t<N>.py        # agent build scripts (gitignored)
```

## THE WONDER PATTERN (most important rule for any subject build, 2026-05-24)

**Read first**: `proposals/v2_audit/SHARED_PRINCIPLES.md` §13 + `proposals/v2_audit/HISTORY_TEMPLATES.md` §1.

Discovered/refined through five user-flagged failures during the 2026-05-24 history rebuild (Wesley, Nelson, Joan, Actium, lotus foot). The principle:

**The answer to every question must be the MOST memorable specific cool fact available.**

Hierarchy (always prefer higher tiers):
1. **NAMED THINGS** — quotes, cultural terms, titles, named objects (`"Victory or Death"`, `"lotus foot"`, `"Sic semper tyrannis"`)
2. **VIVID ACTIONS** — specific physical acts (Pascal sewing parchment into coat; Cleopatra fleeing with 60 ships)
3. **OBJECTS / MATERIALS** — items with memorable properties (Tycho's silver nose, herringbone bricks, the asp)
4. **NUMBERS** (weak) — ONLY when singular + unforgettable (Wright 12 sec, Lincoln 272 words). NEVER magnitude picks.
5. **GENERIC LABELS** (BANNED) — battle names, place names, dates, country names.

Three-question test (every question must pass):
1. **Dinner Test** — does the answer ALONE make a parent ask "wait, why?"
2. **Most-memorable** — is THIS the most memorable detail available about the event?
3. **Drama-Available Rule** ⚠ STRICTEST — if stem has drama (fire/blood/death/escape/last-words/etc.) and question asks for venue/date/label, the question is WRONG. Ask about the drama.

**Every tier-agent prompt must include**: "Read SHARED_PRINCIPLES.md §13 + HISTORY_TEMPLATES.md §1 — The Wonder Pattern. Every q() call must pass the three-question test."

## The double-assert pattern (CRITICAL)

The `q()` helper used by every agent must enforce BOTH budget and parity:

```python
def q(pillar, strategy, question, answer, d1, d2, d3, context):
    total = len(question) + len(answer) + len(d1) + len(d2) + len(d3)
    assert total <= <tier_cap_minus_5>, f"OVER BUDGET T<N>: {total}"
    a = len(answer)
    ds = [len(d1), len(d2), len(d3)]
    assert a <= max(ds) * 1.6, f"PARITY (long): a={a}, max_d={max(ds)}"
    assert a * 1.6 >= min(ds), f"PARITY (short): a={a}, min_d={min(ds)}"
    QUESTIONS.append({
        "tier": <N>,
        "topic_cell": pillar,
        "question": question,
        "answer": answer,
        "choices": [answer, d1, d2, d3],
        "context": context,
        "_meta": {"strategy": strategy, "strategy_pillar": pillar}
    })
```

Tier caps (per `length_budget.py`): T1=280, T2=480, T3=680, T4=900, T5=1100.
Assert cap = tier_cap - 5 for safety margin.

**Why this matters**: budget-only asserts (early-project pattern) let many length_parity failures through to aggregation. Banks using the double-assert had **99%+ gate-pass rates** vs. ~70% for budget-only.

**Tell agents to write distractors FIRST, then size the answer to match.** This is the discipline that makes parity work.

## Save-as-you-go for T5

T5 agents have repeatedly run out of context after only 1-2 pillars. Include this in every T5 prompt:

```python
def save():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(QUESTIONS, indent=2, ensure_ascii=False), encoding="utf-8")

# First pass: ~25 questions/pillar across all 5 pillars, save() between each
# Second pass: depth, save() every 50
```

Without this, T5 socket errors or context-exhaustion lose ALL output. With it, agents that 529 / socket-error after partial work still leave a usable batch.

## Voice convention (proven across rebuilds)

| Tier | Voice |
|---|---|
| T1 | **Crisp moment + named person/place/concept + the wonder**. Scene-led, full sentences, ends with `?`. NOT noun-phrase fragments. |
| T2 | One scene + named figure + the action. |
| T3 | Scene + stakes + the deeper detail or mechanism. |
| T4 | Multi-sentence setup + named details + payoff. |
| T5 | Deep story with rich detail + payoff. Easter-egg level for trivia-style banks. |

**Banks built before this convention was locked in (May 12: ai, science, animal, cooking) initially had noun-phrase-fragment T1 (e.g., "Planet famous for its rings:"). Those were repaired in commit `1d23f76` via dedicated T1-rewrite agents.**

## Tier-agent prompt template

Every tier-agent prompt should contain:

1. **Vision** — the bank's distinctive frame (3-5 sentences). Specific stance commitments.
2. **Read first** — list 3 files: subject doc, strategies doc, an existing build script as example.
3. **Specific assignment** — target candidate count, pillar IDs (use these exactly), per-pillar allocation.
4. **Voice + length** — tier-specific budget, voice description, 2-3 exemplars in target voice.
5. **CRITICAL GATE RULES** — double-assert code block, anti-rote BANNED openings, schema, distractor quality, "real facts only."
6. **Stance reminders** — short list of stance commitments.
7. **Output paths** — script path, JSON path.
8. **Script structure** — full template with double-assert + save() + main write.
9. **Closing imperative** — "Distractors first. Real facts. Go."

Length: target ~150-250 lines. Too short → agent drifts. Too long → agent burns context on reading.

## API resilience

The Anthropic API has socket-closed errors and 529 Overloaded periods. Behaviors observed:

- **All-parallel-spawn 529**: occasionally all 5 agents fail simultaneously within ~3.5 min. **Retry strategy**: re-spawn all 5 unchanged; 529s are usually brief.
- **Mid-run socket error**: an agent dies after producing partial output. **Save-as-you-go** preserves partial work. Re-spawn a focused supplement agent if needed.
- **Mid-run "Overloaded"**: similar pattern to socket. Save partial work.

Always include save-as-you-go for T5 and any bank-sized batch ≥ 300 questions per agent. Add to the q() helper itself by calling `save()` after each ~50 entries appended.

## Supplement pattern

When tiers come in under target, spawn a SUPPLEMENT agent that:
- Reads the original batch (e.g., `<subject>_t<N>_batch001.json`) to see covered strategies
- Writes a NEW batch (`<subject>_t<N>_batch002.json`) with different strategies (no duplicates against batch001)
- Same double-assert discipline
- Use focused per-pillar quotas (heavy on the under-represented ones from batch001)

Add the new batch to the aggregator's `SOURCES` list and re-run. The duplicate gate's growing index will catch cross-batch dupes.

## Explicit `model: "opus"` on all Agent calls

Going forward, ALL Agent calls should include `model: "opus"` explicitly. Per the per-project memory `feedback_no_api_spend.md`: "all LLM work runs through Claude Code on the Max plan (me + Opus subagents)." Without explicit model, agents may inherit from parent or default — proven during the May 2026 audit that this could be silent.

```python
Agent(
    description="...",
    subagent_type="general-purpose",
    model="opus",                       # explicit
    prompt="..."
)
```

## What NOT to do

- **Don't trim gate-passing curated content to make a histogram balance.** Per `feedback_no_delete_validated_content.md` — content was already validated, removing it for an aesthetic ratio is destruction. Add, don't subtract.
- **Don't enforce a single duplicate-gate threshold across all subjects.** Math uses 0.97 (templated drill questions); other subjects use 0.85. Templated questions in science/animal/cooking ("Latin argentum, chemical symbol for silver" vs "Latin kalium, chemical symbol for potassium") trip the 0.85 threshold but are pedagogically distinct. False-positives at 0.85 are tolerated; don't drop them.
- **Don't ship a bank with T1 = noun-phrase fragments.** Use the matured voice convention from the start. If you inherit a bank with fragment-T1, repair it (see commit `1d23f76` for the proven T1-rewrite pattern).
- **Don't skip the double-assert in q() helpers.** Budget-only is not enough.

## Per-bank state snapshot (post May 14 rebuild)

| Bank | Count | Stance highlights |
|------|------:|---|
| math | 2,693 | Drill-style by design (combat = snappy); sympy validator for math correctness |
| grammar | 1,505 | Snappy-rote OK (exception to no-rote rule) |
| science | 2,389 | WONDER-DRIVEN with HONEST contested-topic framing (climate, COVID, vaccines, gene therapy) |
| animal | 1,885 | Wonder-driven natural history |
| cooking | 2,482 | 5-pillar strategy taxonomy (techniques, ingredients, dishes, safety, dining) |
| philosophy | 949 | 58 taxonomy cells, classical-liberal-traditionalist stance |
| ai | 1,492 | Practical safety + power-recognition focus (P4+P5 heavy) |
| geography | 3,308 | Places as portals to wonder; cross-link history/science/culture |
| history | 2,865 | PERSON/MOMENT → STORY → WONDER; Western tradition top billing; communist atrocities heavy |
| theology | 2,551 | Christianity 3/8 weight (civilizational impact NOT truth-claim); Greek + Norse 2/8 each; world religions 1/8 |
| economics | 3,054 | Austrian school CORRECT; Bitcoin its own pillar; Fed/Keynes/MMT critiqued |
| trivia | 3,472 | Geek-dad canon, *Ready Player One* deep-lore vibe, NO MAJOR SPOILERS |
| **Total** | **28,645** | All banks 99%+ gate-clean |

## See also

- `docs/quiz/moral_vision.md` — the universal rubric every question must pass
- `docs/quiz/subjects/<subject>.md` — per-subject voice + stance specs
- `docs/quiz/<subject>_strategies.md` — per-subject pillar taxonomy
- `tools/quizgen/llm_jobs/generate.md` — original LLM job spec (pre-double-assert era)
