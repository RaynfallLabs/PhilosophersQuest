"""Deterministic math question generators.

Each module emits questions for one strategy category (additive,
multiplicative, vocabulary, ...). All output is pure Python, no LLM,
no external API. Generation is deterministic — same seeds, same output.

Each question carries `_meta.strategy` (the named pedagogical move) and
`_meta.strategy_pillar` ("computation" or "vocabulary") so coverage can
be audited.

Schema matches the live game schema plus the _meta sidecar:
    tier, topic_cell, question, answer, choices, context, _meta

See docs/quiz/math_strategies.md for the strategy taxonomy.
"""
