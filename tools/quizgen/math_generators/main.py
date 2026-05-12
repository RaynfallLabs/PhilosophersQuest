"""Aggregator: combine all strategy-driven generators into one bank.

Writes the combined output to state/queue/math_strategy_generated.json
for downstream merge with the existing bank.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tools.quizgen.math_generators.additive import generate_all_additive
from tools.quizgen.math_generators.algebra import generate_all_algebra
from tools.quizgen.math_generators.exponents import generate_all_exponents
from tools.quizgen.math_generators.fractions_decimals import generate_all_fractions_decimals
from tools.quizgen.math_generators.geometry import generate_all_geometry
from tools.quizgen.math_generators.multiplicative import generate_all_multiplicative
from tools.quizgen.math_generators.number_sense import generate_all_number_sense
from tools.quizgen.math_generators.number_theory import generate_all_number_theory
from tools.quizgen.math_generators.percentages import generate_all_percentages
from tools.quizgen.math_generators.vocabulary import generate_all_vocabulary


def generate_all() -> list[dict]:
    out: list[dict] = []
    out.extend(generate_all_additive())
    out.extend(generate_all_multiplicative())
    out.extend(generate_all_number_sense())
    out.extend(generate_all_fractions_decimals())
    out.extend(generate_all_percentages())
    out.extend(generate_all_algebra())
    out.extend(generate_all_number_theory())
    out.extend(generate_all_exponents())
    out.extend(generate_all_geometry())
    out.extend(generate_all_vocabulary())
    return out


def main() -> None:
    qs = generate_all()
    out_path = Path(__file__).resolve().parent.parent / "state" / "queue" / "math_strategy_generated.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(qs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(qs)} strategy-generated questions to {out_path}")
    print("\nBy tier:", dict(Counter(q["tier"] for q in qs)))
    print("\nBy pillar:", dict(Counter(q["_meta"]["strategy_pillar"] for q in qs)))
    print("\nBy strategy:")
    for s, c in Counter(q["_meta"]["strategy"] for q in qs).most_common():
        print(f"  {s}: {c}")


if __name__ == "__main__":
    main()
