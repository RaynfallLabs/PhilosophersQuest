"""Aggregator for grammar deterministic generators."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tools.quizgen.grammar_generators.confusables import generate_all_confusables
from tools.quizgen.grammar_generators.figurative import generate_all_figurative
from tools.quizgen.grammar_generators.loanwords import generate_all_loanwords
from tools.quizgen.grammar_generators.parts_of_speech import generate_all_parts_of_speech


def generate_all() -> list[dict]:
    out: list[dict] = []
    out.extend(generate_all_parts_of_speech())
    out.extend(generate_all_confusables())
    out.extend(generate_all_loanwords())
    out.extend(generate_all_figurative())
    return out


def main() -> None:
    qs = generate_all()
    out_path = Path(__file__).resolve().parent.parent / "state" / "queue" / "grammar_strategy_generated.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(qs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(qs)} strategy-generated grammar questions to {out_path}")
    print("\nBy tier:", dict(sorted(Counter(q["tier"] for q in qs).items())))
    print("By pillar:", dict(Counter(q["_meta"]["strategy_pillar"] for q in qs)))


if __name__ == "__main__":
    main()
