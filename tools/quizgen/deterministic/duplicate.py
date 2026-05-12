"""Duplicate-detection gate: flag near-identical questions.

v1 uses normalized exact match + difflib.SequenceMatcher.ratio() for fuzzy
near-rewordings. This catches the bulk of in-bank dupes (which tend to be
verbatim or near-verbatim) without external dependencies.

v2 (later) will swap in sentence-transformer embeddings for true semantic
dedup — needed when generated content paraphrases existing questions in
ways difflib won't catch.

Performance note: difflib is O(n*m) per comparison. For 615 questions
that's ~378k pairwise checks. We short-circuit using `real_quick_ratio`
(O(1) length-based upper bound) before doing the full ratio.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from tools.quizgen.deterministic.types import GateResult, GateStatus, Question

DEFAULT_SIMILARITY_THRESHOLD = 0.85
EXACT_MATCH_THRESHOLD = 0.999  # treated as duplicate even before fuzzy

_PUNCT_RE = re.compile(r"[^\w\s]")
_SPACE_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """Lowercase, strip diacritics, drop punctuation, collapse whitespace."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _SPACE_RE.sub(" ", text).strip()
    return text


@dataclass
class DuplicateIndex:
    """Pre-normalized question texts for fast similarity lookup."""

    normalized: list[str] = field(default_factory=list)
    originals: list[str] = field(default_factory=list)
    exact_to_idx: dict[str, list[int]] = field(default_factory=dict)

    def add(self, question_text: str) -> int:
        idx = len(self.normalized)
        norm = _normalize(question_text)
        self.normalized.append(norm)
        self.originals.append(question_text)
        self.exact_to_idx.setdefault(norm, []).append(idx)
        return idx

    def find_matches(
        self,
        question_text: str,
        threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        exclude_idx: int | None = None,
    ) -> list[tuple[int, float]]:
        """Return list of (idx, ratio) for any question similar to `question_text`.

        Always includes exact-match (post-normalization) hits.
        """
        norm = _normalize(question_text)
        hits: list[tuple[int, float]] = []

        # exact-match shortcut
        for idx in self.exact_to_idx.get(norm, ()):
            if idx == exclude_idx:
                continue
            hits.append((idx, 1.0))

        if hits:
            return sorted(hits, key=lambda t: -t[1])

        # fuzzy fallback
        matcher = SequenceMatcher(a=norm, autojunk=False)
        for idx, other in enumerate(self.normalized):
            if idx == exclude_idx:
                continue
            matcher.set_seq2(other)
            # quick filter: length-based upper bound
            if matcher.real_quick_ratio() < threshold:
                continue
            if matcher.quick_ratio() < threshold:
                continue
            ratio = matcher.ratio()
            if ratio >= threshold:
                hits.append((idx, ratio))

        return sorted(hits, key=lambda t: -t[1])


def build_duplicate_index(questions: list[Question]) -> DuplicateIndex:
    """Build a DuplicateIndex from a list of question dicts."""
    idx = DuplicateIndex()
    for q in questions:
        idx.add(str(q.get("question", "")))
    return idx


def validate_duplicate(
    q: Question,
    index: DuplicateIndex,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    self_idx: int | None = None,
) -> GateResult:
    """Check `q` for near-duplicate matches in `index`. If `self_idx` is
    provided, exclude that index from results (used when scanning a
    corpus against itself).
    """
    question_text = q.get("question", "")
    if not isinstance(question_text, str) or not question_text.strip():
        return GateResult(
            gate="duplicate",
            status=GateStatus.NA,
            detail="Question text empty or missing.",
        )

    matches = index.find_matches(question_text, threshold=threshold, exclude_idx=self_idx)
    if matches:
        top_idx, top_ratio = matches[0]
        return GateResult(
            gate="duplicate",
            status=GateStatus.FAIL,
            detail=(
                f"Near-duplicate of index {top_idx} (ratio {top_ratio:.3f}). "
                f"Original: {index.originals[top_idx]!r}"
            ),
            metrics={
                "top_match_idx": top_idx,
                "top_match_ratio": round(top_ratio, 3),
                "n_matches": len(matches),
                "all_matches": [(i, round(r, 3)) for i, r in matches[:5]],
            },
        )

    return GateResult(gate="duplicate", status=GateStatus.PASS)
