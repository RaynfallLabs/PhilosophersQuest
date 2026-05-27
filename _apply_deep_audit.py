"""Apply the deep-audit patches.

Per-bank patches:
- AI: _weasel_v2_fix_ai.json (rewrites) + _assumed_knowledge_ai.json (rewrites + adds)
- Science: _weasel_v2_fix_science.json + _assumed_knowledge_science.json
- Economics: _weasel_v2_fix_economics.json + _assumed_knowledge_economics.json
- Animal: _weasel_v2_fix_animal.json (rewrites only)
- Cooking: _weasel_v2_fix_cooking.json (rewrites only)

Each rewrite hits a specific bank_idx. Each add appends to the bank.
Validate the whole bank after, write back if PASS.
"""
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402

# Map subject -> list of patch files (each can be a list-of-ops or a dict-with-rewrites-and-adds)
PATCHES = {
    "ai": ["_weasel_v2_fix_ai.json", "_assumed_knowledge_ai.json"],
    "science": ["_weasel_v2_fix_science.json", "_assumed_knowledge_science.json"],
    "economics": ["_weasel_v2_fix_economics.json", "_assumed_knowledge_economics.json"],
    "animal": ["_weasel_v2_fix_animal.json"],
    "cooking": ["_weasel_v2_fix_cooking.json"],
}

dry_run = "--dry-run" in sys.argv[1:]
overall_pass = True
totals = {"rewrites": 0, "adds": 0}

for subject, patch_files in PATCHES.items():
    print(f"\n=== {subject} ===")
    bank_path = REPO / "data" / "questions" / f"{subject}.json"
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    print(f"  initial bank size: {len(bank)}")

    rewrite_ops = []
    add_ops = []

    for pf in patch_files:
        p = REPO / pf
        if not p.is_file():
            print(f"  -- {pf}: missing, skipping")
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        # Two shapes:
        # 1. list of {"bank_idx": N, "new": {...}}
        # 2. dict with {"rewrites": [...], "adds": [...]}
        if isinstance(data, list):
            for op in data:
                if op.get("bank_idx") is not None:
                    rewrite_ops.append(op)
        elif isinstance(data, dict):
            for op in data.get("rewrites", []):
                if op.get("bank_idx") is not None:
                    rewrite_ops.append(op)
            for op in data.get("adds", []):
                if "new" in op:
                    add_ops.append(op)
        print(f"  loaded {pf}")

    # Dedupe rewrites by bank_idx — last wins
    by_idx = {}
    for op in rewrite_ops:
        by_idx[op["bank_idx"]] = op["new"]

    # Apply rewrites
    for idx, newq in by_idx.items():
        if 0 <= idx < len(bank):
            bank[idx] = newq
        else:
            print(f"  !! bad rewrite idx {idx}")

    # Apply adds (append)
    for op in add_ops:
        bank.append(op["new"])

    rewrites_applied = len(by_idx)
    adds_applied = len(add_ops)
    print(f"  applied: {rewrites_applied} rewrites, {adds_applied} adds")
    print(f"  new bank size: {len(bank)}")

    # Validate the whole bank
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
        continue

    if not dry_run:
        bank_path.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  OK wrote {bank_path}")
    totals["rewrites"] += rewrites_applied
    totals["adds"] += adds_applied

print()
print(f"=== SUMMARY ===")
print(f"  rewrites: {totals['rewrites']}")
print(f"  adds:     {totals['adds']}")
print(f"  overall:  {'PASS' if overall_pass else 'FAIL'}")
if dry_run:
    print("  (dry-run, no files written)")
