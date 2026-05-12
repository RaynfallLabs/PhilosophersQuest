"""Schema validator: required fields + answer-in-choices.

Catches malformed questions before any other gate runs. A fail here means
the record is structurally invalid; downstream gates may misbehave on it.
"""
from __future__ import annotations

from tools.quizgen.deterministic.types import GateResult, GateStatus, Question

REQUIRED_FIELDS = ("tier", "question", "answer", "choices", "context")
TIER_RANGE = range(1, 6)  # tiers 1..5 inclusive


def validate_schema(q: Question) -> GateResult:
    missing = [f for f in REQUIRED_FIELDS if f not in q]
    if missing:
        return GateResult(
            gate="schema",
            status=GateStatus.FAIL,
            detail=f"Missing required field(s): {', '.join(missing)}",
            metrics={"missing_fields": missing},
        )

    tier = q.get("tier")
    if not isinstance(tier, int) or tier not in TIER_RANGE:
        return GateResult(
            gate="schema",
            status=GateStatus.FAIL,
            detail=f"Tier must be int 1-5; got {tier!r}",
            metrics={"tier": tier},
        )

    question_text = q.get("question")
    if not isinstance(question_text, str) or not question_text.strip():
        return GateResult(
            gate="schema",
            status=GateStatus.FAIL,
            detail="Question text must be a non-empty string",
        )

    answer = q.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        return GateResult(
            gate="schema",
            status=GateStatus.FAIL,
            detail="Answer must be a non-empty string",
        )

    choices = q.get("choices")
    if not isinstance(choices, list) or len(choices) != 4:
        return GateResult(
            gate="schema",
            status=GateStatus.FAIL,
            detail=f"Choices must be a list of exactly 4 strings; got {type(choices).__name__} of length {len(choices) if isinstance(choices, list) else 'N/A'}",
            metrics={"n_choices": len(choices) if isinstance(choices, list) else 0},
        )
    for i, c in enumerate(choices):
        if not isinstance(c, str) or not c.strip():
            return GateResult(
                gate="schema",
                status=GateStatus.FAIL,
                detail=f"Choice {i} must be a non-empty string",
            )

    # answer must equal one of the choices (case-insensitive, stripped)
    norm_answer = answer.strip().lower()
    norm_choices = [c.strip().lower() for c in choices]
    if norm_answer not in norm_choices:
        return GateResult(
            gate="schema",
            status=GateStatus.FAIL,
            detail="Answer string does not match any choice (after lowercase+strip)",
            metrics={"answer": answer, "choices": list(choices)},
        )

    return GateResult(gate="schema", status=GateStatus.PASS)
