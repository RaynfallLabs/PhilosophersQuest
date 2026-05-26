"""Validate science T5 generated questions against the full gate suite.

Loads `_gen_science_t5_p1.json` (or specified file) and runs each question through
`validate_rewrite("science", ...)`. Prints fail/soft-warn summary and dumps failures.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite


def main() -> None:
    paths = sys.argv[1:] or ["_gen_science_t5_p1.json", "_gen_science_t5_p2.json", "_gen_science_t5_p3.json"]
    bank_path = REPO / "data" / "questions" / "science.json"
    with open(bank_path, "r", encoding="utf-8") as f:
        bank = json.load(f)
    dup_idx, ans_idx = build_bank_indices(bank)

    all_questions: list[dict] = []
    for p in paths:
        full = REPO / p
        if not full.exists():
            print(f"  skip (missing): {p}")
            continue
        with open(full, "r", encoding="utf-8") as f:
            obj = json.load(f)
        all_questions.extend(obj.get("questions", []))
        print(f"  loaded {len(obj.get('questions', []))} from {p}")

    pass_count = 0
    soft_count = 0
    fail_count = 0
    fails: list[tuple[int, dict, list]] = []
    softs: list[tuple[int, dict, list]] = []

    for i, q in enumerate(all_questions):
        result = validate_rewrite(
            "science", q,
            bank=bank,
            dup_index=dup_idx,
            answer_index=ans_idx,
            replace_idx=None,
        )
        if result["verdict"] == "PASS":
            pass_count += 1
        elif result["verdict"] == "SOFT_WARN":
            soft_count += 1
            softs.append((i, q, result["soft_warns"]))
        else:
            fail_count += 1
            fails.append((i, q, result["hard_fails"]))

    print(f"\n=== RESULTS ===")
    print(f"PASS: {pass_count}")
    print(f"SOFT_WARN: {soft_count}")
    print(f"FAIL: {fail_count}")
    print(f"TOTAL: {len(all_questions)}")

    if fails:
        print(f"\n=== HARD FAILURES ({len(fails)}) ===")
        for i, q, hard in fails:
            print(f"\nQ[{i}]: {q['question'][:100]}...")
            for gate, reason in hard:
                print(f"  [{gate}] {reason[:200]}")

    if softs:
        print(f"\n=== SOFT WARNS ({len(softs)}) ===")
        for i, q, soft in softs:
            print(f"\nQ[{i}]: {q['question'][:100]}...")
            for gate, reason in soft:
                print(f"  [{gate}] {reason[:200]}")


if __name__ == "__main__":
    main()
