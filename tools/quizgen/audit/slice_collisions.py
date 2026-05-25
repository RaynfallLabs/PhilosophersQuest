"""Slice _collisions_history.json into 3 shards for parallel dedup agents.

Shard A: all groups of size 4-6 (the most complex; needs the most diverse rewrites)
Shard B: all groups of size 3
Shard C: all groups of size 2 (single rewrite per group; simplest)

Each shard becomes _collisions_history_shard_A.json etc.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
SRC = REPO / "_collisions_history.json"


def main() -> int:
    groups = json.loads(SRC.read_text(encoding="utf-8"))
    shard_a, shard_b, shard_c = [], [], []
    for g in groups:
        sz = g["size"]
        if sz >= 4:
            shard_a.append(g)
        elif sz == 3:
            shard_b.append(g)
        else:
            shard_c.append(g)
    for name, shard in (("A", shard_a), ("B", shard_b), ("C", shard_c)):
        out = REPO / f"_collisions_history_shard_{name}.json"
        out.write_text(json.dumps(shard, indent=2, ensure_ascii=False), encoding="utf-8")
        total_rewrites = sum(g["size"] - 1 for g in shard)
        total_members = sum(g["size"] for g in shard)
        print(f"  Shard {name}: {len(shard)} groups, {total_members} members, {total_rewrites} rewrites needed -> {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
