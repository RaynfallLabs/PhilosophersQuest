"""Shared types for deterministic gates."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GateStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NA = "na"  # gate does not apply to this question


@dataclass(frozen=True)
class GateResult:
    """Outcome of one gate on one question."""

    gate: str
    status: GateStatus
    detail: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate,
            "status": self.status.value,
            "detail": self.detail,
            "metrics": dict(self.metrics),
        }


# Question is just a dict matching data/questions/*.json shape. We don't
# wrap it in a class because (a) the JSON is the contract, (b) wrapping
# adds friction with no real benefit.
Question = dict[str, Any]
