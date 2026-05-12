"""Shared helpers for grammar generators."""
from __future__ import annotations

from typing import Iterable


def make_question(
    *,
    tier: int,
    topic_cell: str,
    strategy: str,
    pillar: str,
    question: str,
    answer: str,
    distractors: Iterable[str],
    context: str,
) -> dict:
    """Construct a grammar question in live-game schema + _meta sidecar."""
    ans = str(answer)
    seen: set[str] = {ans}
    final_distractors: list[str] = []
    for d in distractors:
        s = str(d)
        if s in seen:
            continue
        seen.add(s)
        final_distractors.append(s)
        if len(final_distractors) == 3:
            break
    while len(final_distractors) < 3:
        fallback = f"alt{len(final_distractors)}"
        if fallback not in seen:
            seen.add(fallback)
            final_distractors.append(fallback)

    return {
        "tier": int(tier),
        "topic_cell": topic_cell,
        "question": question,
        "answer": ans,
        "choices": [ans, *final_distractors],
        "context": context,
        "_meta": {
            "strategy": strategy,
            "strategy_pillar": pillar,
        },
    }
