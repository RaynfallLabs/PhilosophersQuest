"""Apply rewrite patches from the 4 audit agents.

Each patch file is a list of operations:
  - {"find_substring": "...", "new": {...}}   - replace question in-place
  - {"find_substring": "...", "_drop": true}  - remove question from bank
  - {"_add": true, "new": {...}}              - append new question

For each operation, the script:
  1. Finds the target question by stem-substring match (must be unique)
  2. Applies the operation (replace / drop / add)
  3. Re-validates the full bank against AI gate suite
  4. Writes the new bank if all pass; bails if anything fails

Usage:
  py _apply_audit_rewrites.py [--dry-run] [PATCH_FILE ...]
  py _apply_audit_rewrites.py            # default: apply _t2,_t3,_t4,_t5 in order
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = REPO / "data" / "questions" / "ai.json"

DEFAULT_PATCHES = [
    REPO / "_t2_rewrites.json",
    REPO / "_t3_rewrites.json",
    REPO / "_t4_rewrites.json",
    REPO / "_t5_rewrites.json",
]


def load_patches(paths: list[Path]) -> list[tuple[str, dict]]:
    """Load all patch operations from given files, tagged with origin."""
    ops: list[tuple[str, dict]] = []
    for p in paths:
        if not p.is_file():
            print(f"  -- {p.name}: not found, skipping")
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  !! {p.name}: JSON parse error: {e}")
            continue
        if not isinstance(data, list):
            print(f"  !! {p.name}: expected list, got {type(data).__name__}")
            continue
        for i, op in enumerate(data):
            ops.append((f"{p.name}[{i}]", op))
        print(f"  loaded {p.name}: {len(data)} operations")
    return ops


def find_question(bank: list[dict], needle: str) -> int | None:
    """Find a question whose stem contains needle. Returns None if 0 or >1 matches."""
    matches = [i for i, q in enumerate(bank) if needle in q.get("question", "")]
    if len(matches) == 0:
        return None
    if len(matches) > 1:
        print(f"    AMBIGUOUS: {needle!r} matched {len(matches)} questions: {matches[:5]}")
        return None
    return matches[0]


def apply_ops(bank: list[dict], ops: list[tuple[str, dict]]) -> tuple[list[dict], list[str], list[str]]:
    """Apply ops to a copy of bank. Returns (new_bank, applied_log, skipped_log)."""
    new_bank = list(bank)
    applied: list[str] = []
    skipped: list[str] = []

    # Process replaces and drops first (they reference existing questions).
    # Adds are appended at the end.
    pending_adds: list[tuple[str, dict]] = []
    pending_drops: set[int] = set()
    pending_replaces: list[tuple[int, dict, str]] = []

    for origin, op in ops:
        if op.get("_add"):
            pending_adds.append((origin, op["new"]))
            continue
        needle = op.get("find_substring", "")
        if not needle or len(needle) < 20:
            skipped.append(f"{origin}: needle too short or missing: {needle!r}")
            continue
        idx = find_question(new_bank, needle)
        if idx is None:
            skipped.append(f"{origin}: could not find {needle!r}")
            continue
        if idx in pending_drops or any(r[0] == idx for r in pending_replaces):
            skipped.append(f"{origin}: bank#{idx} already targeted by an earlier op")
            continue
        if op.get("_drop"):
            pending_drops.add(idx)
            applied.append(f"{origin}: DROP bank#{idx}")
        elif "new" in op:
            pending_replaces.append((idx, op["new"], origin))
            applied.append(f"{origin}: REPLACE bank#{idx}")
        else:
            skipped.append(f"{origin}: no recognized action (need _drop, _add, or new)")

    # Apply replaces (in place)
    for idx, new_q, _origin in pending_replaces:
        new_bank[idx] = new_q

    # Apply drops (descending so indices stay valid)
    for idx in sorted(pending_drops, reverse=True):
        del new_bank[idx]

    # Apply adds (append)
    for origin, new_q in pending_adds:
        new_bank.append(new_q)
        applied.append(f"{origin}: ADD (new bank#{len(new_bank) - 1})")

    return new_bank, applied, skipped


def validate_bank(bank: list[dict]) -> tuple[int, int, int, Counter]:
    """Re-validate the full bank. Returns (pass, fail, soft_warn, fail_by_gate)."""
    dup, ans = build_bank_indices(bank)
    pass_c = fail_c = soft_c = 0
    fail_by_gate: Counter = Counter()
    fail_details: list[tuple[int, str, list]] = []
    for i, q in enumerate(bank):
        r = validate_rewrite("ai", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=i)
        if r["verdict"] == "FAIL":
            fail_c += 1
            for g, _reason in r["hard_fails"]:
                fail_by_gate[g] += 1
            fail_details.append((i, q.get("question", "")[:80], r["hard_fails"]))
        else:
            pass_c += 1
            if r["verdict"] == "SOFT_WARN":
                soft_c += 1
    # Print fail details
    if fail_details:
        print()
        print("  Failure detail:")
        for i, stem, hf in fail_details[:20]:
            print(f"    bank#{i}: {stem!r}")
            for g, reason in hf[:3]:
                print(f"      - {g}: {reason}")
        if len(fail_details) > 20:
            print(f"    ... and {len(fail_details) - 20} more")
    return pass_c, fail_c, soft_c, fail_by_gate


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv[1:]
    if args:
        patches = [Path(a) for a in args]
    else:
        patches = DEFAULT_PATCHES

    print("=== Loading patches ===")
    ops = load_patches(patches)
    print(f"Total operations: {len(ops)}")
    print()

    print("=== Loading bank ===")
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    print(f"Bank size: {len(bank)}")
    print()

    print("=== Applying operations ===")
    new_bank, applied, skipped = apply_ops(bank, ops)
    for line in applied:
        print(f"  + {line}")
    if skipped:
        print()
        print("  SKIPPED:")
        for line in skipped:
            print(f"  - {line}")
    print()
    print(f"New bank size: {len(new_bank)} ({len(new_bank) - len(bank):+d})")
    print()

    print("=== Validating new bank ===")
    pass_c, fail_c, soft_c, fail_by_gate = validate_bank(new_bank)
    print(f"  PASS: {pass_c} (incl. {soft_c} soft-warn)")
    print(f"  FAIL: {fail_c}")
    if fail_by_gate:
        print("  By gate:")
        for gate, count in sorted(fail_by_gate.items(), key=lambda kv: -kv[1]):
            print(f"    {gate}: {count}")
    print()

    if fail_c > 0:
        print("  FAIL Validation failures - NOT writing. Patches with failures must be fixed.")
        return 1

    # Per-tier breakdown
    by_tier = Counter(q.get("tier") for q in new_bank)
    print("New tier distribution:")
    for t in (1, 2, 3, 4, 5):
        print(f"  T{t}: {by_tier.get(t, 0)}")
    print()

    if dry_run:
        print("(dry-run - bank not written)")
        return 0

    BANK_PATH.write_text(json.dumps(new_bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK Wrote {BANK_PATH}")
    print(f"   Bank size: {len(new_bank)} questions, {pass_c} PASS / {fail_c} FAIL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
