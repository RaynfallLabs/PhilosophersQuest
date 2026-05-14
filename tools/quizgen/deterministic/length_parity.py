"""Length-parity gate: prevent length-leaks-the-answer.

A choice that is much longer or shorter than its sibling distractors
telegraphs the correct answer to a skimming player. moral_vision.md §6
mandates ±15% from the mean choice length and longest/shortest ratio
≤ 1.30 (matching the calibration agent's A2 gate exactly).

Math and grammar are exempt: math.md §5 / grammar voice rules require
parallel *form* (all numeric or all verbal) but not parallel *length* —
the distractor `68` for `8` (wrong-operation) is a 2x ratio that the
gate's strict 1.30 cap would reject despite being pedagogically valuable.

Cooking uses an "answer-outlier" rule instead of the strict ratio rule.
The leak risk is real ONLY when the *correct answer* is the length
outlier — a player skimming by length can pick the longest or shortest
choice and be right. Distractor-length variation among the 3 wrong
choices is fine — the question "Sharp / Dull / Both equally safe /
Depends on the food" has natural length spread (5/4/17/19) but the
answer "Sharp" sits in the middle by length, so no tell. See cooking.md §8.
"""
from __future__ import annotations

from tools.quizgen.deterministic.types import GateResult, GateStatus, Question

# Default calibration (philosophy + wonder subjects with substantive-phrase choices)
MAX_DEVIATION_FROM_MEAN = 0.15  # 15%
MAX_LONGEST_SHORTEST_RATIO = 1.30

EXEMPT_SUBJECTS = frozenset({"math"})

# Per-subject ratio calibration. Default if not listed = 1.30 (philosophy standard).
SUBJECT_RATIO_OVERRIDES: dict[str, float] = {}
SUBJECT_DEVIATION_OVERRIDES: dict[str, float] = {}

# Subjects using the "answer-outlier" rule (cooking-style). For these, the
# only fail condition is: correct answer is dramatically longer or shorter
# than every distractor. Distractor-length variation among the 3 wrong
# choices is allowed.
ANSWER_OUTLIER_SUBJECTS = frozenset({"cooking", "animal", "grammar", "science", "ai", "geography", "history", "theology", "economics"})

# Multiplier for "dramatically": answer is an outlier if its length exceeds
# (longest distractor × multiplier) or is below (shortest distractor / multiplier).
# 1.6 calibration: still catches "answer is the long obvious one" tells while
# allowing T4-T5 substantive answers that are naturally 50-60% longer than
# their distractors (e.g., a chemistry explanation vs. 3 wrong-mechanism
# distractors of similar length to each other). The agent's discipline + this
# threshold together is what enforces "no length tell" in practice.
ANSWER_OUTLIER_MULTIPLIER = 1.6


def _check_answer_outlier(q: Question) -> GateResult:
    """Cooking-style parity check: fail only if the correct answer is the
    length outlier (longer than every distractor by >50%, or shorter by
    >50%). Allows legitimate short-decisive-answer questions where
    distractors are naturally longer "weasel" options.
    """
    choices = q.get("choices") or []
    answer = q.get("answer", "")
    if not isinstance(choices, list) or len(choices) != 4 or not all(
        isinstance(c, str) and c.strip() for c in choices
    ):
        return GateResult(
            gate="length_parity",
            status=GateStatus.NA,
            detail="Cannot evaluate parity: choices not in expected shape.",
        )
    # locate answer in choices (case-insensitive, stripped match)
    norm_answer = answer.strip().lower() if isinstance(answer, str) else ""
    distractor_strings = [c for c in choices if c.strip().lower() != norm_answer]
    if len(distractor_strings) != 3:
        return GateResult(
            gate="length_parity",
            status=GateStatus.NA,
            detail="Cannot locate answer among choices for outlier check.",
        )
    ans_len = len(answer)
    dist_lens = [len(d) for d in distractor_strings]
    max_dist = max(dist_lens)
    min_dist = max(min(dist_lens), 1)  # guard div-by-zero
    metrics = {
        "answer_len": ans_len,
        "distractor_lens": dist_lens,
        "longest_distractor": max_dist,
        "shortest_distractor": min_dist,
        "outlier_multiplier": ANSWER_OUTLIER_MULTIPLIER,
    }
    if ans_len > max_dist * ANSWER_OUTLIER_MULTIPLIER:
        return GateResult(
            gate="length_parity",
            status=GateStatus.FAIL,
            detail=(
                f"Length-leak risk: correct answer ({ans_len} chars) is "
                f"dramatically longer than longest distractor ({max_dist})"
            ),
            metrics=metrics,
        )
    if ans_len * ANSWER_OUTLIER_MULTIPLIER < min_dist:
        return GateResult(
            gate="length_parity",
            status=GateStatus.FAIL,
            detail=(
                f"Length-leak risk: correct answer ({ans_len} chars) is "
                f"dramatically shorter than shortest distractor ({min_dist})"
            ),
            metrics=metrics,
        )
    return GateResult(gate="length_parity", status=GateStatus.PASS, metrics=metrics)


def validate_length_parity(q: Question, subject: str | None = None) -> GateResult:
    if subject in EXEMPT_SUBJECTS:
        return GateResult(
            gate="length_parity",
            status=GateStatus.NA,
            detail=f"Subject {subject!r} is exempt — parallel form required, not parallel length.",
        )
    if subject in ANSWER_OUTLIER_SUBJECTS:
        return _check_answer_outlier(q)
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
