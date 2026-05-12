"""Anti-rote gate: flag questions whose prompts match definition-shell
patterns. These are the deterministic patterns named in
docs/quiz/moral_vision.md §6. A match sends the question for repair —
the repair must reframe as usage, consequence, mechanism, or story-led
hook rather than as a definition lookup.

KEEP IN SYNC with moral_vision.md §6. A test in tests/ verifies that
the patterns documented in the spec exactly match the list below.

Math and grammar are exempted (their action mapping in the game is
explicitly snappy/rote — combat and scroll-reading need immediate
recall).
"""
from __future__ import annotations

import re

from tools.quizgen.deterministic.types import GateResult, GateStatus, Question

# (pattern_source, comment). The source strings here must match the
# regex code block in docs/quiz/moral_vision.md §6 EXACTLY after both are
# stripped of trailing whitespace and aligning comments. The in-sync test
# enforces this.
#
# We use non-raw strings for patterns containing a quote character class
# (so that `['"]` is stored as a 3-character class rather than `['\"]`
# with a literal backslash). For all other patterns, raw strings are fine.
_QUOTE_CLASS = "['\"]"  # matches a single-quote or double-quote

_PATTERN_DEFS: list[tuple[str, str]] = [
    ("^What (is|does) " + _QUOTE_CLASS,                                              "What is 'X'? / What does 'X' mean?"),
    ("^What is the " + _QUOTE_CLASS,                                                 "What is the 'coherence theory of truth'?"),
    (r"^What (is|does) the (term|word|name|definition|meaning) (for|of) ",           "What is the term for...?"),
    (r"^What word means",                                                            "vocab-as-trivia"),
    (r"^Which (\w+ )?(city|country|nation|state|place|region|river|mountain|island|continent) ", "geography rote"),
    (r"^What is the capital of ",                                                    "capital-of trivia"),
    (r"^In what year (did|was) ",                                                    "date-recall trivia"),
    (r"^Who (wrote|invented|painted|composed|founded|tutored|discovered) ",          "name-the-creator trivia"),
    (r"^How many \w+ (are there|exist|did)",                                         "count-the-things trivia"),
    (r"^What is the chemical symbol",                                                "symbol-lookup"),
    (r"^Define\b",                                                                   "straight definition request"),
]

ANTI_ROTE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(src, re.IGNORECASE) for src, _ in _PATTERN_DEFS
]

ANTI_ROTE_PATTERN_SOURCES: list[str] = [src for src, _ in _PATTERN_DEFS]

EXEMPT_SUBJECTS = frozenset({"math", "grammar"})


def validate_anti_rote(q: Question, subject: str | None = None) -> GateResult:
    """Flag question prompts that match a rote-definition pattern.

    `subject` is optional. If it's "math" or "grammar", the gate returns NA.
    Otherwise the question text is checked against every pattern; on the
    first match the gate fails and names the pattern.
    """
    if subject in EXEMPT_SUBJECTS:
        return GateResult(
            gate="anti_rote",
            status=GateStatus.NA,
            detail=f"Subject {subject!r} is exempt from anti-rote gate.",
        )

    question_text = q.get("question", "")
    if not isinstance(question_text, str):
        return GateResult(
            gate="anti_rote",
            status=GateStatus.NA,
            detail="Question text not available.",
        )

    for pattern in ANTI_ROTE_PATTERNS:
        m = pattern.match(question_text.strip())
        if m:
            return GateResult(
                gate="anti_rote",
                status=GateStatus.FAIL,
                detail=f"Matches anti-rote pattern: {pattern.pattern!r}",
                metrics={
                    "pattern": pattern.pattern,
                    "match": m.group(0),
                },
            )

    return GateResult(gate="anti_rote", status=GateStatus.PASS)
