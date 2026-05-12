"""Aggregator for animal deterministic generators."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tools.quizgen.animal_generators.attribution import generate_all_attribution
from tools.quizgen.animal_generators.domestication import generate_all_domestication
from tools.quizgen.animal_generators.paleontology import generate_all_paleontology


def generate_all() -> list[dict]:
    out: list[dict] = []
    out.extend(generate_all_attribution())
    out.extend(generate_all_paleontology())
    out.extend(generate_all_domestication())
    return out


def main() -> None:
    qs = generate_all()
    out_path = Path(__file__).resolve().parent.parent / "state" / "queue" / "animal_strategy_generated.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(qs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(qs)} strategy-generated animal questions to {out_path}")
    print("\nBy tier:", dict(sorted(Counter(q["tier"] for q in qs).items())))
    print("By pillar:", dict(Counter(q["_meta"]["strategy_pillar"] for q in qs)))
    print("\nTop strategies:")
    for s, c in Counter(q["_meta"]["strategy"] for q in qs).most_common(15):
        print(f"  {s}: {c}")


if __name__ == "__main__":
    main()
