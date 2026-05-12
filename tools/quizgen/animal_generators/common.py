"""Shared helpers for animal generators."""
from __future__ import annotations

from typing import Iterable


def make_question(
    *,
    tier: int,
    topic_cell: str,
    strategy: str,
    pillar: str,  # biology / evolution / husbandry / hunting / culture
    question: str,
    answer: str,
    distractors: Iterable[str],
    context: str,
) -> dict:
    """Construct an animal question in live-game schema + _meta sidecar."""
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


def pick_length_balanced_distractors(
    correct: str, candidates: list[str], k: int = 3
) -> list[str] | None:
    """Pick k distractors with similar length to correct (within 1.6× ratio).

    Returns None if k same-length-bucket distractors can't be found.
    """
    target_len = len(correct)
    # Same length first
    same = [c for c in candidates if c != correct and len(c) == target_len]
    if len(same) >= k:
        return same[:k]
    # Within ±2 chars
    close = [c for c in candidates if c != correct and abs(len(c) - target_len) <= 2]
    if len(close) >= k:
        return sorted(close, key=lambda x: abs(len(x) - target_len))[:k]
    # Up to 1.6x ratio
    ratio_ok = [
        c for c in candidates
        if c != correct
        and len(c) <= target_len * 1.6
        and len(c) * 1.6 >= target_len
    ]
    if len(ratio_ok) >= k:
        return sorted(ratio_ok, key=lambda x: abs(len(x) - target_len))[:k]
    return None
