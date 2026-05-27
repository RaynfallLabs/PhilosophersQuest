"""Apply symmetric-voice fixes to the 2 Christian-doctrinal drift hits."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

bank_path = Path("data/questions/theology.json")
bank = json.loads(bank_path.read_text(encoding="utf-8"))

FIXES = [
    {
        "bank_idx": 118,
        "field": "question",
        "old": "He saw the risen Christ amid seven golden lampstands",
        "new": "He saw a figure of Christ amid seven golden lampstands",
    },
    {
        "bank_idx": 120,
        "field": "question",
        "old": "the god who answers with fire is the true God",
        "new": "the god who answers with fire wins the contest",
    },
]

dup, ans = build_bank_indices(bank)

for fix in FIXES:
    idx = fix["bank_idx"]
    q = dict(bank[idx])
    original = q[fix["field"]]
    if fix["old"] not in original:
        print(f"#{idx}: SUBSTRING NOT FOUND: {fix['old']!r}")
        continue
    q[fix["field"]] = original.replace(fix["old"], fix["new"])

    # Validate
    r = validate_rewrite("theology", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    print(f"#{idx} T{q['tier']}: verdict {r['verdict']}")
    if r["verdict"] == "FAIL":
        for g, reason in r["hard_fails"][:3]:
            print(f"  HARD {g}: {reason[:200]}")
        continue

    bank[idx] = q
    print(f"  Applied: {fix['old']!r} -> {fix['new']!r}")

bank_path.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"\nWrote {bank_path}")
