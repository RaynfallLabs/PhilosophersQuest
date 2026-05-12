"""Aggregator for all cooking generators.

Writes the combined output to state/queue/cooking_strategy_generated.json
for downstream merge with the LLM batches + existing bank.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tools.quizgen.cooking_generators.attribution import generate_all_attribution
from tools.quizgen.cooking_generators.etiquette import generate_all_etiquette
from tools.quizgen.cooking_generators.ratios import generate_all_ratios
from tools.quizgen.cooking_generators.safety import generate_all_safety


def generate_all() -> list[dict]:
    out: list[dict] = []
    out.extend(generate_all_attribution())
    out.extend(generate_all_safety())
    out.extend(generate_all_ratios())
    out.extend(generate_all_etiquette())
    return out


def main() -> None:
    qs = generate_all()
    out_path = Path(__file__).resolve().parent.parent / "state" / "queue" / "cooking_strategy_generated.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(qs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(qs)} strategy-generated cooking questions to {out_path}")
    print("\nBy tier:", dict(sorted(Counter(q["tier"] for q in qs).items())))
    print("By pillar:", dict(Counter(q["_meta"]["strategy_pillar"] for q in qs)))
    print("\nBy strategy:")
    for s, c in Counter(q["_meta"]["strategy"] for q in qs).most_common():
        print(f"  {s}: {c}")


if __name__ == "__main__":
    main()
