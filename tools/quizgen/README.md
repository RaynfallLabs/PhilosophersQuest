# tools/quizgen — Quiz generation + validation pipeline

The pipeline produces and validates quiz questions for Philosopher's Quest.
It is designed around two complementary executions:

1. **Deterministic Python** — pure functions, no LLM calls. Cheap, fast,
   reproducible. Catches schema errors, length-parity violations, anti-rote
   patterns, and duplicates.
2. **Claude Code subagents** — LLM judgment for moral fit, wonder/fun, tier
   fit, factual accuracy, gameplay viability, viral check, and repair. Each
   subagent reads a prompt template from `llm_jobs/`.

The pipeline runs entirely on the user's Max plan (Claude Code) — there is
no Anthropic API spend. Python orchestrates; subagents do the LLM work.

## Layout

```
tools/quizgen/
├── __init__.py
├── __main__.py            CLI: `py -m tools.quizgen <subcommand>`
├── specs.py               Loads moral_vision.md, subject specs, taxonomy
├── pipeline.py            Resumable orchestrator
├── deterministic/         Pure-Python validators
│   ├── __init__.py
│   ├── types.py             GateResult, GateStatus
│   ├── schema.py            Required fields + answer-in-choices
│   ├── length_parity.py     ±15% rule, longest/shortest ≤ 1.30
│   ├── length_budget.py     Total record cost: T1-T3 ≤600, T4-T5 ≤800
│   ├── anti_rote.py         Regex list from moral_vision.md §6
│   └── duplicate.py         Difflib SequenceMatcher (v1); embeddings later
├── llm_jobs/              Prompt templates for subagents
│   ├── __init__.py
│   ├── generate.md
│   ├── validate_moral.md
│   ├── validate_wonder.md
│   ├── validate_tier_fit.md
│   ├── validate_facts.md
│   ├── validate_context.md
│   ├── validate_gameplay.md
│   ├── repair.md
│   └── viral_check.md
├── reports/               Tracked: persistent analyses, calibration reports
├── state/                 Mostly gitignored: pipeline run state
│   ├── *.md               Tracked: voice analysis + calibration reports
│   ├── *.py               Tracked: reproducible sampler scripts
│   ├── *.json             Tracked: sample dumps
│   ├── runs/              IGNORED: timestamped per-run dirs
│   └── queue/             IGNORED: batches needing LLM judgment
└── cache/                 IGNORED: LLM response cache (keyed by prompt hash)
```

## Running it

### Validate the existing bank (deterministic-only)

```bash
py -m tools.quizgen validate --subject philosophy
```

Reads `data/questions/philosophy.json`, runs all deterministic gates, writes
results to `state/runs/<timestamp>/validate_philosophy.{json,md}`. Useful for
seeing how the current bank scores before any LLM work.

### Calibrate against a stratified sample (deterministic-only)

```bash
py -m tools.quizgen calibrate --subject philosophy --sample 100 --seed 20260511
```

Same as validate, but on a stratified random sample. Outputs match the
calibration reports already in `state/`.

### LLM judgment passes (driven from Claude Code session)

The Python pipeline only writes batches needing LLM judgment to
`state/queue/<gate>/<batch-id>.json`. Inside the Claude Code session, the
user (or Claude) reads those batches and spawns subagents pointed at the
relevant prompt template in `llm_jobs/`. Results are written back to
`state/queue/<gate>/<batch-id>.scores.json`.

This split is deliberate: it lets the deterministic work be reproducible
and version-controlled, while the LLM judgment runs through the user's
Claude Code Max-plan session rather than billed API calls.

## Why this design

- **Pure-Python deterministic gates** = reproducible, testable, no cost.
  The calibration reports in `state/` are reproducible from the sampler
  scripts.
- **No Anthropic API** = no billing. All LLM work goes through Claude Code
  subagents on the user's Max plan.
- **Subject-by-subject batches** = each subject can be reviewed and
  approved independently. Philosophy is the pilot subject.
- **Resumable** = pipeline state lives on disk. A crash, a `/clear`, or a
  session break does not lose progress.
- **Spec-driven** = `docs/quiz/moral_vision.md`, `docs/quiz/subjects/*.md`,
  and `docs/quiz/taxonomy.yaml` are the authoritative inputs. Pipeline
  records the SHA-256 hash of each spec applied to a generation run.

## Status

| Component | Status |
|---|---|
| Spec loader (`specs.py`) | implemented |
| Deterministic gates | implemented (schema, length parity, length budget, anti-rote, duplicate) |
| Pipeline orchestrator | implemented (validate + calibrate subcommands) |
| LLM job templates | written but invocation is manual from session |
| Pytest suite | covers all deterministic gates |
| Calibration vs philosophy.json | matches n=100 subagent calibration |
