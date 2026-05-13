"""Aggregator for science deterministic generators."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tools.quizgen.science_generators.chemistry import generate_all_chemistry
from tools.quizgen.science_generators.physics_units import generate_all_physics_units
from tools.quizgen.science_generators.scientists import generate_all_scientists


def generate_all() -> list[dict]:
    out: list[dict] = []
    out.extend(generate_all_chemistry())
    out.extend(generate_all_physics_units())
    out.extend(generate_all_scientists())
    return out


def main() -> None:
    qs = generate_all()
    out_path = Path(__file__).resolve().parent.parent / "state" / "queue" / "science_strategy_generated.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(qs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(qs)} strategy-generated science questions to {out_path}")
    print("\nBy tier:", dict(sorted(Counter(q["tier"] for q in qs).items())))
    print("By pillar:", dict(Counter(q["_meta"]["strategy_pillar"] for q in qs)))


if __name__ == "__main__":
    main()
