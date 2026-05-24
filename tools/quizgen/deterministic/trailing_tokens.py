"""Trailing-token corruption gate: catch 3+ consecutive repeated words.

A generation-pass artifact where an LLM bulk pass loops on the last word
as it approaches the length cap — yielding strings like
"...benefits ecosystems overall overall overall overall overall". This is
always a bug; no legitimate teaching content contains 3+ consecutive
identical words.

Discovered 2026-05-24 during the animal post-geography audit (14 corrupted
strings across 11 T5 questions). The deterministic regex is general — it
catches the trailing-overall signature AND any analogous mid-string
token-loop a future bulk pass might emit.

Specification: docs are in proposals/v2_audit/SHARED_PRINCIPLES.md §12.

Subject exemption: `grammar` is exempt because it teaches grammar curiosities
that legitimately use 3+ identical consecutive words — e.g. the canonical
"James while John had had had had had had had had had had had a better
effect on the teacher" puzzle, or the German "Toi toi toi" idiom. No other
subject has a legitimate trigger.
"""
from __future__ import annotations

import re

from tools.quizgen.deterministic.types import GateResult, GateStatus, Question

# 3+ consecutive repeats of any \w+ token, separated by whitespace.
# Case-insensitive so "Word Word word" still trips.
TRAILING_TOKEN_PATTERN = re.compile(r"\b(\w+)(\s+\1){2,}\b", re.IGNORECASE)

# String fields to check on the question object. Choices are handled
# separately (list of strings).
_SCALAR_STRING_FIELDS = ("question", "answer", "context")

# Grammar's bank legitimately contains repeated-token teaching examples
# (the "had had" puzzle, German "Toi toi toi", etc.). No other subject
# has a plausible legitimate use of 3+ consecutive identical words.
EXEMPT_SUBJECTS = frozenset({"grammar"})


def _find_repeats(text: object) -> list[str]:
    """Return all repeated-token matches in `text`. Non-strings return []."""
    if not isinstance(text, str):
        return []
    return [m.group(0) for m in TRAILING_TOKEN_PATTERN.finditer(text)]


def validate_trailing_tokens(q: Question, subject: str | None = None) -> GateResult:
    """Flag questions containing 3+ consecutive repeated words in any field.

    Grammar is exempt (legitimate repeated-token teaching examples). All
    other subjects: any 3+ consecutive identical words is a generation-pass
    artifact and a hard fail.
    """
    if subject in EXEMPT_SUBJECTS:
        return GateResult(
            gate="trailing_tokens",
            status=GateStatus.NA,
            detail=f"Subject {subject!r} is exempt — repeated-token examples are legitimate teaching content.",
        )

    hits: list[tuple[str, str]] = []

    for field in _SCALAR_STRING_FIELDS:
        for match in _find_repeats(q.get(field)):
            hits.append((field, match))

    choices = q.get("choices")
    if isinstance(choices, list):
        for i, choice in enumerate(choices):
            for match in _find_repeats(choice):
                hits.append((f"choices[{i}]", match))

    if hits:
        first_field, first_match = hits[0]
        return GateResult(
            gate="trailing_tokens",
            status=GateStatus.FAIL,
            detail=(
                f"Repeated-token corruption: {first_field} contains {first_match!r}"
                + (f" (+{len(hits) - 1} more)" if len(hits) > 1 else "")
            ),
            metrics={"hits": [{"field": f, "match": m} for f, m in hits]},
        )

    return GateResult(gate="trailing_tokens", status=GateStatus.PASS)
