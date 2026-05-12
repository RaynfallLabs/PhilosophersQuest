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

# Default calibration (philosophy + wonder subjects with substantive-phrase choices)
MAX_DEVIATION_FROM_MEAN = 0.15  # 15%
MAX_LONGEST_SHORTEST_RATIO = 1.30

EXEMPT_SUBJECTS = frozenset({"math", "grammar"})

# Per-subject ratio calibration. Default if not listed = 1.30 (philosophy standard).
# Cooking: single-word answers (cuisine/technique names) need 1.50 to allow natural
# length variation while still catching blatant "Yes" vs "Yes if X is greater than 10"
# leak-by-length cases.
SUBJECT_RATIO_OVERRIDES: dict[str, float] = {
    "cooking": 1.50,
}

SUBJECT_DEVIATION_OVERRIDES: dict[str, float] = {
    "cooking": 0.22,  # 22% mean-deviation allowance — matches the 1.50 ratio relaxation
}


def validate_length_parity(q: Question, subject: str | None = None) -> GateResult:
    if subject in EXEMPT_SUBJECTS:
        return GateResult(
            gate="length_parity",
            status=GateStatus.NA,
            detail=f"Subject {subject!r} is exempt — parallel form required, not parallel length.",
        )
    max_ratio = SUBJECT_RATIO_OVERRIDES.get(subject or "", MAX_LONGEST_SHORTEST_RATIO)
    max_dev = SUBJECT_DEVIATION_OVERRIDES.get(subject or "", MAX_DEVIATION_FROM_MEAN)
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
    actual_max_dev = max(deviations)
    longest = max(lengths)
    shortest = max(min(lengths), 1)  # guard div-by-zero
    ratio = longest / shortest

    failed_dev = actual_max_dev > max_dev
    failed_ratio = ratio > max_ratio
    metrics = {
        "lengths": lengths,
        "mean": round(mean, 2),
        "max_deviation_pct": round(actual_max_dev * 100, 1),
        "longest_over_shortest": round(ratio, 2),
        "threshold_ratio": max_ratio,
        "threshold_deviation_pct": round(max_dev * 100, 1),
    }

    if failed_dev or failed_ratio:
        reasons = []
        if failed_dev:
            reasons.append(f"max deviation {actual_max_dev * 100:.1f}% > {max_dev * 100:.0f}%")
        if failed_ratio:
            reasons.append(f"longest/shortest {ratio:.2f} > {max_ratio:.2f}")
        return GateResult(
            gate="length_parity",
            status=GateStatus.FAIL,
            detail="; ".join(reasons),
            metrics=metrics,
        )

    return GateResult(gate="length_parity", status=GateStatus.PASS, metrics=metrics)
