"""Build a detailed JSON catalog of every gate-failing question across the
4 not-yet-fully-clean banks (history/philosophy/cooking/animal). Geography
is at 100% and skipped.

Each record includes:
  subject, index, tier, question, answer, choices, context,
  failed_gates (each with the gate name + verbatim failure reason)

Output: `_residuals_catalog.json` — for the residuals-fix agent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import (  # noqa: E402
    build_bank_indices,
    validate_rewrite,
)


def main() -> int:
    records = []
    for subject in ["history", "philosophy", "cooking", "animal", "grammar"]:
        bank = json.loads((REPO / "data" / "questions" / f"{subject}.json").read_text(encoding="utf-8"))
        dup_index, answer_index = build_bank_indices(bank)
        for i, q in enumerate(bank):
            r = validate_rewrite(subject, q, bank=bank, dup_index=dup_index, answer_index=answer_index, replace_idx=i)
            if r["verdict"] == "FAIL":
                records.append({
                    "subject": subject,
                    "index": i,
                    "tier": q.get("tier"),
                    "question": q.get("question", ""),
                    "answer": q.get("answer", ""),
                    "choices": q.get("choices", []),
                    "context": q.get("context", ""),
                    "failed_gates": [{"gate": g, "reason": reason} for g, reason in r["hard_fails"]],
                })
    out_path = REPO / "_residuals_catalog.json"
    out_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(records)} residual records to {out_path.name}")
    # Per-subject + per-gate summary
    by_subject_gate: dict[tuple[str, str], int] = {}
    for r in records:
        for g in r["failed_gates"]:
            key = (r["subject"], g["gate"])
            by_subject_gate[key] = by_subject_gate.get(key, 0) + 1
    print("\nPer-subject × per-gate counts:")
    for (subject, gate), count in sorted(by_subject_gate.items()):
        print(f"  {subject:11s} {gate:30s} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
