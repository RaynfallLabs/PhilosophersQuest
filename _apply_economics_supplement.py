"""Apply the 5 financial-literacy supplemental files to the existing
economics bank — APPEND, not replace.

The five _gen_economics_supp_finlit_*.json files contain 220 fresh
questions (banking+tax, investing+retirement, entrepreneurship,
accounting+fraud, insurance+risk). This applier loads them, dedupes
against the existing 1196-question bank, validates each, appends to
the bank, and writes back.

Usage:
  py _apply_economics_supplement.py [--dry-run]
"""
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402
from tools.quizgen.deterministic.answer_collision import _normalize_answer  # noqa: E402

BANK_PATH = REPO / "data" / "questions" / "economics.json"
SUPP_GLOB = "_gen_economics_supp_*.json"

assert BANK_PATH.name == "economics.json", "BANK_PATH check failed"


def _normalize_stem(stem: str) -> str:
    return _normalize_answer(stem)


def main() -> int:
    dry_run = "--dry-run" in sys.argv[1:]

    print(f"=== Applying economics financial-literacy supplement ===")
    print(f"  bank: {BANK_PATH}")

    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    print(f"  existing bank size: {len(bank)}")

    # Pre-compute stem set on existing bank for dedup
    existing_stems = {_normalize_stem(q.get("question", "")) for q in bank}

    supp_files = sorted(REPO.glob(SUPP_GLOB))
    if not supp_files:
        print("  !! no supplement files found")
        return 1

    new_questions: list[dict] = []
    skipped_dup = 0
    for path in supp_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  !! {path.name}: parse error {e}")
            continue
        qs = data if isinstance(data, list) else data.get("questions", [])
        print(f"  loaded {path.name}: {len(qs)} questions")
        for q in qs:
            if not isinstance(q, dict):
                continue
            stripped = {k: v for k, v in q.items() if not k.startswith("_")}
            stem_norm = _normalize_stem(stripped.get("question", ""))
            if stem_norm in existing_stems:
                skipped_dup += 1
                continue
            existing_stems.add(stem_norm)
            new_questions.append(stripped)
    print()
    print(f"Supplement candidates: {len(new_questions)} (skipped {skipped_dup} stem-duplicates)")

    if not new_questions:
        print("Nothing to apply.")
        return 0

    # Validate each new question against the combined bank
    print("Validating supplementals against combined bank...")
    combined = list(bank) + new_questions
    dup, ans = build_bank_indices(combined)
    pass_idxs = []
    fail_count = 0
    fail_records = []
    fail_by_gate: Counter = Counter()
    base = len(bank)
    for i, q in enumerate(new_questions):
        # Use combined-bank index for self-collision exemption
        r = validate_rewrite("economics", q, bank=combined, dup_index=dup, answer_index=ans, replace_idx=base + i)
        if r["verdict"] == "FAIL":
            fail_count += 1
            for g, _reason in r["hard_fails"]:
                fail_by_gate[g] += 1
            fail_records.append({
                "supp_idx": i,
                "stem": q.get("question", "")[:80],
                "tier": q.get("tier"),
                "hard_fails": r["hard_fails"][:3],
            })
        else:
            pass_idxs.append(i)

    print(f"  PASS: {len(pass_idxs)}")
    print(f"  FAIL: {fail_count}")
    if fail_by_gate:
        print("  By gate:")
        for gate, count in sorted(fail_by_gate.items(), key=lambda kv: -kv[1]):
            print(f"    {gate}: {count}")

    accepted = [new_questions[i] for i in pass_idxs]
    new_bank = list(bank) + accepted
    by_tier = Counter(q.get("tier") for q in new_bank)
    print()
    print("Final bank tier distribution:")
    for t in (1, 2, 3, 4, 5):
        print(f"  T{t}: {by_tier.get(t, 0)}")
    print(f"  Total: {len(new_bank)}")

    if dry_run:
        print()
        print("(dry-run — no files written)")
        return 0

    BANK_PATH.write_text(json.dumps(new_bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print()
    print(f"OK wrote {BANK_PATH}")
    print(f"   Bank size: {len(new_bank)} questions ({len(accepted)} appended)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
