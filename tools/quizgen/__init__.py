"""Philosopher's Quest quiz generation + validation pipeline.

The pipeline is split into deterministic (pure Python) and LLM (Claude Code
subagent) work:

- `tools.quizgen.specs`         — loads moral_vision.md, per-subject spec,
                                  taxonomy.yaml; records version hashes.
- `tools.quizgen.deterministic` — pure-Python gates: schema, length parity,
                                  length budget, anti-rote regex, duplicate.
- `tools.quizgen.llm_jobs`      — prompt templates for subagent validators;
                                  invocation happens in the Claude Code
                                  session, not from Python.
- `tools.quizgen.pipeline`      — resumable orchestrator. Loads questions,
                                  runs all deterministic gates, writes
                                  results + a needs-LLM-work queue to
                                  state/. The session then drives LLM
                                  subagents over the queue.

State lives in `tools/quizgen/state/` (gitignored). Cache in
`tools/quizgen/cache/` (also gitignored).

Run via:
    py -m tools.quizgen validate --subject philosophy
    py -m tools.quizgen calibrate --subject philosophy --sample 100 --seed 20260511
"""
__version__ = "0.1.0"
