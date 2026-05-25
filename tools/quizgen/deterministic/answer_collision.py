"""Answer-collision gate: catch same-answer / near-same-answer duplicates
across the bank, regardless of how different the stems are.

The existing `validate_duplicate` gate compares STEMS (it asks "is this
question text a paraphrase of another?"). It never reads the answer
field. As a result, two questions with the same answer wrapped in very
different stem text both pass — even though a player drawing from the
pool would learn the SAME cool fact twice.

This gate closes that gap. It normalizes the answer text and flags any
question whose normalized answer appears in 2+ questions across the
bank, regardless of tier.

Discovered 2026-05-25 — user-flagged after the overnight Wonder Pattern
audit produced 64 cross-tier answer collisions in the history bank,
including 6 instances each of "Eppur si muove" and "Molon labe."

Per HISTORY_TEMPLATES.md §1 "Cross-tier same-answer duplicates."
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from tools.quizgen.deterministic.types import GateResult, GateStatus, Question

# Bigram-Jaccard threshold for "same answer" — answers are short so we
# need a high overlap before flagging. Empirically: "Eppur si muove" vs
# "Eppur si muove — and yet it moves" should match (>0.7); "Sic semper
# tyrannis" vs "Veni vidi vici" should not (~0.0).
DEFAULT_ANSWER_JACCARD_THRESHOLD = 0.70

# Subjects where same-answer recurrence is legitimately by-design:
#  - math / grammar — templated drills ("5 + 7 = ?" → "12" recurs;
#    "verb tense of 'ran'" → "past tense" recurs).
#  - philosophy — the answer IS a canonical position name
#    ("Memory continuity — the same person if memories carry forward").
#    Multiple legitimate scenes (Ship of Theseus, Parfit teletransporter,
#    monastery thought-experiment) can — and pedagogically should — test
#    the same position. User-confirmed 2026-05-25: dedup philosophy by
#    SCENE variety, not by answer text.
EXEMPT_SUBJECTS = frozenset({"math", "grammar", "philosophy"})

_PUNCT_RE = re.compile(r"[^\w\s]")
_SPACE_RE = re.compile(r"\s+")


def _normalize_answer(text: str) -> str:
    """Normalize an answer string for comparison. Strips Unicode marks,
    lowercase, removes punctuation, collapses whitespace."""
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _SPACE_RE.sub(" ", text).strip()
    return text


def _bigrams(text: str) -> set[tuple[str, str]]:
    """Word-bigrams of the normalized text. For 1-word answers, fall back
    to the singleton word so very short answers still produce a comparable
    fingerprint."""
    words = text.split()
    if not words:
        return set()
    if len(words) == 1:
        return {(words[0], "")}
    return set(zip(words, words[1:]))


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(len(a | b), 1)


@dataclass(frozen=True)
class AnswerCollisionIndex:
    """Index of normalized answers across the bank for collision lookup."""

    normalized: list[str]
    bigrams: list[set[tuple[str, str]]]

    def find_collisions(
        self,
        answer_text: str,
        threshold: float = DEFAULT_ANSWER_JACCARD_THRESHOLD,
        exclude_idx: int | None = None,
    ) -> list[tuple[int, float]]:
        """Return (idx, jaccard_score) for any other question in the bank
        whose normalized answer matches at or above threshold."""
        query = _normalize_answer(answer_text)
        if not query:
            return []
        query_bg = _bigrams(query)
        hits: list[tuple[int, float]] = []
        for j, other_bg in enumerate(self.bigrams):
            if j == exclude_idx:
                continue
            if not other_bg:
                continue
            score = _jaccard(query_bg, other_bg)
            if score >= threshold:
                hits.append((j, score))
        return sorted(hits, key=lambda t: -t[1])


def build_answer_collision_index(questions: list[Question]) -> AnswerCollisionIndex:
    """Build an index over all questions' answers for collision detection."""
    normalized: list[str] = []
    bigrams: list[set[tuple[str, str]]] = []
    for q in questions:
        norm = _normalize_answer(str(q.get("answer", "")))
        normalized.append(norm)
        bigrams.append(_bigrams(norm))
    return AnswerCollisionIndex(normalized=normalized, bigrams=bigrams)


def validate_answer_collision(
    q: Question,
    index: AnswerCollisionIndex,
    threshold: float = DEFAULT_ANSWER_JACCARD_THRESHOLD,
    self_idx: int | None = None,
    subject: str | None = None,
) -> GateResult:
    """Flag a question whose answer matches 1+ other questions' answers.

    `subject` is optional. If it's "math" or "grammar" (templated drill
    subjects where same-answer recurrence is by design), the gate
    returns NA.
    """
    if subject in EXEMPT_SUBJECTS:
        return GateResult(
            gate="answer_collision",
            status=GateStatus.NA,
            detail=f"Subject {subject!r} is exempt — templated drills legitimately recur.",
        )
    answer_text = str(q.get("answer", ""))
    if not answer_text.strip():
        return GateResult(
            gate="answer_collision",
            status=GateStatus.NA,
            detail="Empty answer.",
        )
    collisions = index.find_collisions(
        answer_text, threshold=threshold, exclude_idx=self_idx
    )
    if not collisions:
        return GateResult(gate="answer_collision", status=GateStatus.PASS)
    return GateResult(
        gate="answer_collision",
        status=GateStatus.FAIL,
        detail=(
            f"Answer collides with {len(collisions)} other question(s); "
            f"top match idx={collisions[0][0]} jaccard={collisions[0][1]:.2f}"
        ),
        metrics={"collisions": [{"idx": i, "jaccard": s} for i, s in collisions[:5]]},
    )
