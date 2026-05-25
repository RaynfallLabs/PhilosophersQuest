"""Slice `_collisions_<subject>.json` into 3 shards for parallel dedup agents.

Shard A: all groups of size 4+ (the most complex; needs the most diverse rewrites)
Shard B: all groups of size 3
Shard C: all groups of size 2 (single rewrite per group; simplest)

Each shard becomes `_collisions_<subject>_shard_A.json` etc.

Usage:
    py -m tools.quizgen.audit.slice_collisions <subject> [<subject> ...]
    py -m tools.quizgen.audit.slice_collisions history theology trivia
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent


def slice_subject(subject: str) -> int:
    src = REPO / f"_collisions_{subject}.json"
    if not src.exists():
        print(f"  ! missing: {src.name}")
        return 1
    groups = json.loads(src.read_text(encoding="utf-8"))
    shard_a, shard_b, shard_c = [], [], []
    for g in groups:
        sz = g["size"]
        if sz >= 4:
            shard_a.append(g)
        elif sz == 3:
            shard_b.append(g)
        else:
            shard_c.append(g)
    print(f"== {subject} ==")
    for name, shard in (("A", shard_a), ("B", shard_b), ("C", shard_c)):
        out = REPO / f"_collisions_{subject}_shard_{name}.json"
        out.write_text(json.dumps(shard, indent=2, ensure_ascii=False), encoding="utf-8")
        total_rewrites = sum(g["size"] - 1 for g in shard)
        total_members = sum(g["size"] for g in shard)
        print(f"  Shard {name}: {len(shard)} groups, {total_members} members, {total_rewrites} rewrites needed -> {out.name}")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        # Default: legacy history-only behavior
        return slice_subject("history")
    for subject in args:
        slice_subject(subject)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
