"""Shared helpers for math generators.

`make_question` is the canonical constructor: it builds the dict in the
live-game schema with `_meta.strategy` provenance. All generator
functions use it.
"""
from __future__ import annotations

from typing import Iterable


def make_question(
    *,
    tier: int,
    topic_cell: str,
    strategy: str,
    pillar: str,
    question: str,
    answer: str | int | float,
    distractors: Iterable[str | int | float],
    context: str = "",
) -> dict:
    """Construct one math question in live-game schema + _meta sidecar.

    `distractors` is an iterable of 3 wrong-answer values. The function
    coerces everything to str, deduplicates against `answer`, and pads if
    fewer than 3 unique distractors remain (rare; indicates a generator
    bug).
    """
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
    # pad with a tilted-near-the-answer fallback if generator under-produced
    fallback = 0
    while len(final_distractors) < 3:
        guess = str(int(answer) + 100 + fallback) if str(answer).lstrip("-").isdigit() else f"NA{fallback}"
        if guess not in seen:
            seen.add(guess)
            final_distractors.append(guess)
        fallback += 1

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


def off_by_one(n: int) -> list[int]:
    """Common-error distractors: ±1, ±2."""
    return [n - 1, n + 1, n - 2]


def magnitude_off(n: int) -> list[int]:
    """Common-error distractors: ×10, /10, +10."""
    return [n * 10, n // 10 if n >= 10 else n + 10, n + 10]
