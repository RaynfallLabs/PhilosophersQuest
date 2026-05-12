"""Deterministic cooking question generators.

Each module emits questions for one strategy category (attribution,
ratios, safety, etiquette, ...). Pure Python, no LLM. See
`docs/quiz/cooking_strategies.md` for the five-pillar taxonomy.

Generators use scene-led phrasing (anti-rote enforced) — never
"What is X?", always "A chef does Y. The term for this is ___?"
"""
