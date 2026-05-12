"""Length-parity gate: prevent length-leaks-the-answer.

A choice that is much longer or shorter than its sibling distractors
telegraphs the correct answer to a skimming player. moral_vision.md §6
mandates ±15% from the mean choice length and longest/shortest ratio
≤ 1.30 (matching the calibration agent's A2 gate exactly).

Math and grammar are exempt: math.md §5 / grammar voice rules require
parallel *form* (all numeric or all verbal) but not parallel *length* —
the distractor `68` for `8` (wrong-operation) is a 2x ratio that the
gate's strict 1.30 cap would reject despite being pedagogically valuable.
"""
from __future__ import annotations

from tools.quizgen.deterministic.types import GateResult, GateStatus, Question

MAX_DEVIATION_FROM_MEAN = 0.15  # 15%
MAX_LONGEST_SHORTEST_RATIO = 1.30

EXEMPT_SUBJECTS = frozenset({"math", "grammar"})


def validate_length_parity(q: Question, subject: str | None = None) -> GateResult:
    if subject in EXEMPT_SUBJECTS:
        return GateResult(
            gate="length_parity",
            status=GateStatus.NA,
            detail=f"Subject {subject!r} is exempt — parallel form required, not parallel length.",
        )
    choices = q.get("choices") or []
    if not isinstance(choices, list) or len(choices) != 4 or not all(
        isinstance(c, str) and c.strip() for c in choices
    ):
        return GateResult(
            gate="length_parity",
            status=GateStatus.NA,
            detail="Cannot evaluate parity: choices not in expected shape (schema gate handles this).",
        )

    lengths = [len(c) for c in choices]
    mean = sum(lengths) / 4.0
    if mean == 0:
        return GateResult(
            gate="length_parity",
            status=GateStatus.FAIL,
            detail="All choices are empty",
            metrics={"lengths": lengths},
        )
    deviations = [abs(L - mean) / mean for L in lengths]
    max_dev = max(deviations)
    longest = max(lengths)
    shortest = max(min(lengths), 1)  # guard div-by-zero
    ratio = longest / shortest

    failed_dev = max_dev > MAX_DEVIATION_FROM_MEAN
    failed_ratio = ratio > MAX_LONGEST_SHORTEST_RATIO
    metrics = {
        "lengths": lengths,
        "mean": round(mean, 2),
        "max_deviation_pct": round(max_dev * 100, 1),
        "longest_over_shortest": round(ratio, 2),
    }

    if failed_dev or failed_ratio:
        reasons = []
        if failed_dev:
            reasons.append(f"max deviation {max_dev * 100:.1f}% > 15%")
        if failed_ratio:
            reasons.append(f"longest/shortest {ratio:.2f} > 1.30")
        return GateResult(
            gate="length_parity",
            status=GateStatus.FAIL,
            detail="; ".join(reasons),
            metrics=metrics,
        )

    return GateResult(gate="length_parity", status=GateStatus.PASS, metrics=metrics)
