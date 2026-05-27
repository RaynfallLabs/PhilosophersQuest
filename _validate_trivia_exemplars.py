"""Validate the 30 trivia exemplars against the full gate pipeline."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.exemplars.trivia import EXEMPLARS
from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

empty_bank: list[dict] = []
dup, ans = build_bank_indices(empty_bank)

print(f"Validating {len(EXEMPLARS)} trivia exemplars...\n")

by_tier = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
by_verdict = {"PASS": 0, "SOFT_WARN": 0, "FAIL": 0}
failures: list[dict] = []

for i, q in enumerate(EXEMPLARS):
    by_tier[q["tier"]] += 1
    r = validate_rewrite("trivia", q, bank=empty_bank, dup_index=dup, answer_index=ans, replace_idx=None)
    by_verdict[r["verdict"]] += 1
    if r["verdict"] != "PASS":
        stem_preview = q["question"][:80].replace("\n", " ")
        failures.append({
            "idx": i, "tier": q["tier"], "stem_preview": stem_preview,
            "verdict": r["verdict"], "hard_fails": r["hard_fails"], "soft_warns": r["soft_warns"],
        })

print("=== Per-tier count ===")
for t, c in by_tier.items():
    print(f"  T{t}: {c}")

print("\n=== Verdict counts ===")
for v, c in by_verdict.items():
    print(f"  {v}: {c}")

if failures:
    print(f"\n=== Failures ({len(failures)}) ===")
    for f in failures:
        print(f"\n#{f['idx']} T{f['tier']} [{f['verdict']}]: {f['stem_preview']}...")
        for g, r in f["hard_fails"]:
            print(f"  HARD  {g}: {r[:300]}")
        for g, r in f["soft_warns"]:
            print(f"  SOFT  {g}: {r[:300]}")
else:
    print("\nALL 30 EXEMPLARS PASS")
