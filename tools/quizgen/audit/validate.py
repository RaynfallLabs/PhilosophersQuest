"""Universal rewrite validation harness.

Given a subject and a proposed rewrite (5-field question dict), runs ALL gates
that apply to that subject:

  1. Pipeline-level deterministic gates (tools/quizgen/deterministic/*):
       - schema, length_budget, length_parity, anti_rote,
         duplicate, answer_collision, math_correctness, trailing_tokens
  2. Subject-specific structural gates from
     tools/quizgen/scratch/<subject>_structural_gates.PER_QUESTION_GATES

Designed to be imported by `_apply_audit_rewrites.py` (and any future
applier) so we never apply a rewrite that the agent fluffed.

Verdicts:
  - PASS:      no failures
  - SOFT_WARN: only soft-warn gates flagged (still applicable, but logged)
  - FAIL:      one or more hard-reject gates failed (do NOT apply)

Per-rewrite cost is O(bank_size) due to dup/collision lookups, so a full
4-bank pass of ~300 rewrites takes a few seconds — fine for interactive use.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Callable, Optional

REPO = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.quizgen import specs  # noqa: E402
from tools.quizgen.deterministic import (  # noqa: E402
    AnswerCollisionIndex,
    DuplicateIndex,
    GateStatus,
    build_answer_collision_index,
    build_duplicate_index,
    validate_anti_rote,
    validate_answer_collision,
    validate_duplicate,
    validate_length_budget,
    validate_length_parity,
    validate_math_correctness,
    validate_schema,
    validate_trailing_tokens,
)


# Subject → structural-gate module under tools.quizgen.gates
_GATE_MODULES = {
    "history":    "tools.quizgen.gates.history",
    "philosophy": "tools.quizgen.gates.philosophy",
    "cooking":    "tools.quizgen.gates.cooking",
    "animal":     "tools.quizgen.gates.animal",
    "geography":  "tools.quizgen.gates.geography",
    "grammar":    "tools.quizgen.gates.grammar",
    "ai":         "tools.quizgen.gates.ai",
    "science":    "tools.quizgen.gates.science",
    "economics":  "tools.quizgen.gates.economics",
    "theology":   "tools.quizgen.gates.theology",
}


def _load_subject_gates(subject: str) -> tuple[list[tuple[str, Callable]], frozenset[str]]:
    """Returns (per_question_gates, soft_warn_set) for the subject.

    soft_warn_set defaults to empty for subjects that don't expose it.
    """
    if subject not in _GATE_MODULES:
        return [], frozenset()
    mod = importlib.import_module(_GATE_MODULES[subject])
    gates = getattr(mod, "PER_QUESTION_GATES", [])
    soft = getattr(mod, "SOFT_WARN_GATES", frozenset())
    if not isinstance(soft, (set, frozenset)):
        soft = frozenset(soft)
    return list(gates), soft


def _gate_result_to_status(gate_name: str, result: Any) -> tuple[Optional[str], Optional[str]]:
    """Normalize a gate result to (hard_reason, soft_reason) — exactly one
    is non-None, or both are None for PASS/NA.

    Pipeline gates return GateResult objects (status enum + detail).
    Scratch gates return Optional[str] (None on pass; otherwise reason).
    """
    # Pipeline GateResult duck-type
    if hasattr(result, "status"):
        if result.status == GateStatus.FAIL:
            return result.detail or "fail", None
        return None, None  # PASS or NA
    # Scratch-style optional string
    if result is None:
        return None, None
    if isinstance(result, str) and result.startswith("soft-warn:"):
        return None, result
    if isinstance(result, str):
        return result, None
    return str(result), None


def build_bank_indices(
    bank: list[dict],
    *,
    self_idx: int | None = None,
) -> tuple[DuplicateIndex, AnswerCollisionIndex]:
    """Pre-build dup + collision indices over a bank. Cache and reuse for a
    full validation batch — building them per-rewrite would be O(n²) work
    for nothing.
    """
    return build_duplicate_index(bank), build_answer_collision_index(bank)


def validate_rewrite(
    subject: str,
    new_q: dict,
    *,
    bank: list[dict],
    dup_index: DuplicateIndex,
    answer_index: AnswerCollisionIndex,
    replace_idx: int | None,
) -> dict:
    """Run all gates against a proposed rewrite.

    `replace_idx` is the position in `bank` where the new question would
    replace the old one — passed as `self_idx` to dup/collision gates so a
    rewrite isn't flagged as colliding with the OLD version of itself.

    Returns:
      {
        "verdict": "PASS" | "SOFT_WARN" | "FAIL",
        "hard_fails": [(gate_name, reason), ...],
        "soft_warns": [(gate_name, reason), ...],
        "all": [(gate_name, status, detail), ...],   # full audit trail
      }
    """
    spec_set = specs.load_all(subject=subject)
    hard: list[tuple[str, str]] = []
    soft: list[tuple[str, str]] = []
    audit: list[tuple[str, str, str]] = []

    # 1. Pipeline-level deterministic gates
    dup_threshold = 0.97 if subject == "math" else 0.85
    pipeline_results = {
        "schema":           validate_schema(new_q),
        "length_parity":    validate_length_parity(new_q, subject=subject),
        "length_budget":    validate_length_budget(new_q, subject=subject),
        "anti_rote":        validate_anti_rote(new_q, subject=subject),
        "duplicate":        validate_duplicate(new_q, dup_index, threshold=dup_threshold, self_idx=replace_idx),
        "answer_collision": validate_answer_collision(new_q, answer_index, self_idx=replace_idx, subject=subject),
        "math_correctness": validate_math_correctness(new_q, subject=subject),
        "trailing_tokens":  validate_trailing_tokens(new_q, subject=subject),
    }
    for gate, res in pipeline_results.items():
        hard_reason, soft_reason = _gate_result_to_status(gate, res)
        status = res.status.value if hasattr(res, "status") else ("FAIL" if hard_reason or soft_reason else "PASS")
        audit.append((gate, status, hard_reason or soft_reason or ""))
        if hard_reason:
            hard.append((gate, hard_reason))
        elif soft_reason:
            soft.append((gate, soft_reason))

    # 2. Subject-specific structural gates
    scratch_gates, soft_warn_set = _load_subject_gates(subject)
    for gate, fn in scratch_gates:
        try:
            res = fn(new_q)
        except Exception as e:  # noqa: BLE001
            res = f"gate-exception: {e!r}"
        if res is None:
            audit.append((gate, "PASS", ""))
            continue
        if gate in soft_warn_set or (isinstance(res, str) and res.startswith("soft-warn:")):
            soft.append((gate, res))
            audit.append((gate, "SOFT", res))
        else:
            hard.append((gate, res))
            audit.append((gate, "FAIL", res))

    if hard:
        verdict = "FAIL"
    elif soft:
        verdict = "SOFT_WARN"
    else:
        verdict = "PASS"

    return {
        "verdict": verdict,
        "hard_fails": hard,
        "soft_warns": soft,
        "all": audit,
    }


__all__ = [
    "build_bank_indices",
    "validate_rewrite",
]
