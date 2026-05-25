"""Deterministic validators (pure Python, no LLM calls).

Each gate is a callable that accepts a `Question` dict and returns a
`GateResult`. Gates are pure — same input, same output, no side effects.

Public API:
    from tools.quizgen.deterministic import (
        validate_schema,
        validate_length_parity,
        validate_length_budget,
        validate_anti_rote,
        validate_duplicate,
        GateResult,
    )
"""
from tools.quizgen.deterministic.types import GateResult, GateStatus
from tools.quizgen.deterministic.schema import validate_schema
from tools.quizgen.deterministic.length_parity import validate_length_parity
from tools.quizgen.deterministic.length_budget import validate_length_budget
from tools.quizgen.deterministic.anti_rote import validate_anti_rote, ANTI_ROTE_PATTERNS
from tools.quizgen.deterministic.duplicate import build_duplicate_index, validate_duplicate
from tools.quizgen.deterministic.math_correctness import validate_math_correctness
from tools.quizgen.deterministic.trailing_tokens import validate_trailing_tokens
from tools.quizgen.deterministic.answer_collision import (
    build_answer_collision_index,
    validate_answer_collision,
)

__all__ = [
    "GateResult",
    "GateStatus",
    "validate_schema",
    "validate_length_parity",
    "validate_length_budget",
    "validate_anti_rote",
    "ANTI_ROTE_PATTERNS",
    "build_duplicate_index",
    "validate_duplicate",
    "validate_math_correctness",
    "validate_trailing_tokens",
    "build_answer_collision_index",
    "validate_answer_collision",
]
