"""Duplicate-detection gate: flag near-identical questions.

Two-stage detector:

1. **Candidate generation** — for each question, pre-compute a set of word
   bigrams ("shingles") and build an inverted index `bigram -> [idx, ...]`.
   At query time, walk the query's bigrams through the index and tally
   overlap per candidate. Candidates whose bigram-Jaccard with the query
   clears `JACCARD_CANDIDATE_THRESHOLD` advance to stage 2.

2. **Confirmation** — run `difflib.SequenceMatcher.ratio()` on the survivors
   and report any whose ratio meets the caller's `threshold`. This preserves
   the historical similarity semantics (callers still tune via the same
   threshold; math still uses 0.97; everything else still 0.85).

The inverted index turns the intra-bank scan from O(n²) full-string ratios
into O(n × avg_postings) cheap dict lookups plus a small number of
SequenceMatcher calls per question. On the 882-question philosophy bank
this cuts validation from ~280s to <10s on Windows/Python 3.14.

Why bigrams and not MinHash? At the scale we run (≤10k questions per bank),
exact bigram-Jaccard on a Python dict is already orders of magnitude faster
than the SequenceMatcher second stage. MinHash would add hash-function
tuning and probabilistic miss risk for no real speedup in this regime.

The Jaccard threshold is deliberately loose. Bigram overlap and SequenceMatcher
ratio aren't tightly coupled — e.g. a single-word swap in a 9-word question
drops bigram-Jaccard to ~0.5 while SeqMatcher stays >0.9. A low cutoff
(0.18) keeps the candidate set generous so we don't drop pairs the
SequenceMatcher stage would have caught. If a future false-negative surfaces,
lower it further before reaching for MinHash.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from tools.quizgen.deterministic.types import GateResult, GateStatus, Question

DEFAULT_SIMILARITY_THRESHOLD = 0.85
EXACT_MATCH_THRESHOLD = 0.999  # treated as duplicate even before fuzzy
JACCARD_CANDIDATE_THRESHOLD = 0.18

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


def _shingles(norm_text: str) -> frozenset[str]:
    """Word bigrams as `"w1\\x00w2"` strings; falls back to unigrams for
    1-word inputs so very short questions still produce a non-empty set."""
    words = norm_text.split()
    if len(words) < 2:
        return frozenset(words)
    return frozenset(f"{a}\x00{b}" for a, b in zip(words, words[1:]))


@dataclass
class DuplicateIndex:
    """Pre-normalized question texts + bigram inverted index for fast lookup."""

    normalized: list[str] = field(default_factory=list)
    originals: list[str] = field(default_factory=list)
    shingles: list[frozenset[str]] = field(default_factory=list)
    exact_to_idx: dict[str, list[int]] = field(default_factory=dict)
    _postings: dict[str, list[int]] = field(default_factory=dict)

    def add(self, question_text: str) -> int:
        idx = len(self.normalized)
        norm = _normalize(question_text)
        shings = _shingles(norm)
        self.normalized.append(norm)
        self.originals.append(question_text)
        self.shingles.append(shings)
        self.exact_to_idx.setdefault(norm, []).append(idx)
        for g in shings:
            self._postings.setdefault(g, []).append(idx)
        return idx

    def _candidates(
        self,
        query_shings: frozenset[str],
        exclude_idx: int | None,
    ) -> list[int]:
        """Return indices whose bigram-Jaccard with `query_shings` is at
        or above JACCARD_CANDIDATE_THRESHOLD."""
        if not query_shings:
            return []
        overlap: dict[int, int] = {}
        for g in query_shings:
            for idx in self._postings.get(g, ()):
                if idx == exclude_idx:
                    continue
                overlap[idx] = overlap.get(idx, 0) + 1
        q_size = len(query_shings)
        out: list[int] = []
        for idx, n_overlap in overlap.items():
            other_size = len(self.shingles[idx])
            union = q_size + other_size - n_overlap
            if union and n_overlap / union >= JACCARD_CANDIDATE_THRESHOLD:
                out.append(idx)
        return out

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

        # candidate generation via inverted bigram index
        query_shings = _shingles(norm)
        candidates = self._candidates(query_shings, exclude_idx)
        if not candidates:
            return []

        # confirmation: SequenceMatcher on survivors only
        matcher = SequenceMatcher(a=norm, autojunk=False)
        for idx in candidates:
            other = self.normalized[idx]
            matcher.set_seq2(other)
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
