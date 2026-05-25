"""Extract answer-collision groups for each bank.

Uses the new validate_answer_collision gate to find groups of questions
that share normalized answers. Writes per-subject JSON files showing
each group with all member questions (so agents can decide which to
keep and what cool fact each tier-version should use instead).

Run: py tools/quizgen/scratch/_build_collision_groups.py all
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO))

from tools.quizgen.deterministic.answer_collision import (
    _normalize_answer,
    _bigrams,
    _jaccard,
    DEFAULT_ANSWER_JACCARD_THRESHOLD,
)


def find_groups(questions: list[dict], threshold: float = DEFAULT_ANSWER_JACCARD_THRESHOLD) -> list[list[int]]:
    """Return collision groups (lists of question indices). Each group has 2+ members
    whose normalized-answer bigram-Jaccard pairwise meets threshold.

    Uses union-find on pairwise matches.
    """
    n = len(questions)
    normalized = [_normalize_answer(str(q.get("answer", ""))) for q in questions]
    bigrams_list = [_bigrams(norm) for norm in normalized]

    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Build inverted index of words → questions (to limit pairwise check)
    word_to_qs: dict[str, list[int]] = defaultdict(list)
    for i, norm in enumerate(normalized):
        for w in set(norm.split()):
            if w:
                word_to_qs[w].append(i)

    # For each question, only compare against others sharing at least one word
    for i in range(n):
        if not bigrams_list[i]:
            continue
        candidates = set()
        for w in set(normalized[i].split()):
            for j in word_to_qs.get(w, []):
                if j > i:
                    candidates.add(j)
        for j in candidates:
            if not bigrams_list[j]:
                continue
            if _jaccard(bigrams_list[i], bigrams_list[j]) >= threshold:
                union(i, j)

    # Collect groups
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        if not bigrams_list[i]:
            continue
        groups[find(i)].append(i)
    # Only return groups with 2+ members
    return [sorted(grp) for grp in groups.values() if len(grp) >= 2]


def main() -> int:
    args = sys.argv[1:]
    targets = (
        ["history", "philosophy", "cooking", "animal", "geography"]
        if not args or args[0] == "all"
        else args
    )
    for subject in targets:
        p = REPO / "data" / "questions" / f"{subject}.json"
        if not p.exists():
            print(f"  {subject}: NO BANK FILE")
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        groups = find_groups(d)
        # Sort groups by size (largest collisions first)
        groups.sort(key=lambda g: -len(g))

        out_data = []
        for grp_idx, indices in enumerate(groups):
            members = [
                {
                    "index": i,
                    "tier": d[i].get("tier"),
                    "question": d[i].get("question", ""),
                    "answer": d[i].get("answer", ""),
                    "choices": d[i].get("choices", []),
                    "context": d[i].get("context", ""),
                }
                for i in indices
            ]
            out_data.append({
                "group_id": grp_idx,
                "size": len(indices),
                "canonical_answer_normalized": _normalize_answer(str(d[indices[0]].get("answer", ""))),
                "members": members,
            })

        out_path = REPO / f"_collisions_{subject}.json"
        out_path.write_text(json.dumps(out_data, indent=2, ensure_ascii=False), encoding="utf-8")
        affected = sum(g["size"] for g in out_data)
        print(f"  {subject}: {len(out_data)} groups, {affected} affected questions ({100*affected/len(d):.1f}% of bank) -> {out_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
