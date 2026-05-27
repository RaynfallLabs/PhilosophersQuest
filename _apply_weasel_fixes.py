"""Apply weasel-closer fix patches across 6 banks."""
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402

PATCHES = [
    ("ai", "_weasel_fix_ai.json"),
    ("animal", "_weasel_fix_animal.json"),
    ("cooking", "_weasel_fix_cooking.json"),
    ("economics", "_weasel_fix_economics.json"),
    ("geography", "_weasel_fix_geography.json"),
    ("science", "_weasel_fix_science.json"),
]

dry_run = "--dry-run" in sys.argv[1:]
total_applied = 0
total_failed = 0
overall_pass = True

for subject, patch_name in PATCHES:
    print(f"\n=== {subject} ({patch_name}) ===")
    bank_path = REPO / "data" / "questions" / f"{subject}.json"
    patch_path = REPO / patch_name
    if not patch_path.exists():
        print(f"  -- patch file not found: {patch_name}")
        continue
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    patch = json.loads(patch_path.read_text(encoding="utf-8"))
    print(f"  bank: {len(bank)} questions, patch: {len(patch)} ops")

    # Apply replacements by bank_idx
    skipped = []
    for op in patch:
        idx = op.get("bank_idx")
        if idx is None or not (0 <= idx < len(bank)):
            skipped.append(f"bad idx {idx}")
            continue
        bank[idx] = op["new"]

    print(f"  applied: {len(patch) - len(skipped)} (skipped: {len(skipped)})")

    # Validate
    dup, ans = build_bank_indices(bank)
    pass_c = fail_c = soft_c = 0
    fails = []
    for i, q in enumerate(bank):
        r = validate_rewrite(subject, q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=i)
        if r["verdict"] == "FAIL":
            fail_c += 1
            fails.append((i, q.get("question", "")[:70], r["hard_fails"]))
        else:
            pass_c += 1
            if r["verdict"] == "SOFT_WARN":
                soft_c += 1
    print(f"  PASS: {pass_c} (incl {soft_c} soft) / FAIL: {fail_c}")
    if fails:
        for i, s, hf in fails[:5]:
            print(f"    bank#{i}: {s!r}")
            for g, r in hf[:2]:
                print(f"      - {g}: {r}")
        overall_pass = False
        total_failed += fail_c
        continue

    if not dry_run:
        bank_path.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  OK wrote {bank_path}")
    total_applied += len(patch) - len(skipped)

print()
print(f"=== SUMMARY ===")
print(f"  applied: {total_applied}")
print(f"  failed: {total_failed}")
print(f"  overall: {'PASS' if overall_pass else 'FAIL'}")
if dry_run:
    print("  (dry-run — no files written)")
