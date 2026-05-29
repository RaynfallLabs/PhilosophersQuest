"""Aggregate 6 pillar outputs + cross-validate + replace data/questions/math.json."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

REPO = Path(__file__).resolve().parent
BANK_PATH = REPO / "data" / "questions" / "math.json"
PILLAR_FILES = [
    REPO / "proposals" / "v2_audit" / f"_math_p{i}_output.json" for i in range(1, 7)
]


def load_pillar(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and "questions" in raw:
        return raw["questions"]
    raise ValueError(f"{path} has unexpected shape: {type(raw)}")


# === Step 1: Load all pillars ===
all_questions = []
per_pillar_counts = {}
for i, path in enumerate(PILLAR_FILES, 1):
    if not path.exists():
        print(f"MISSING: {path}")
        sys.exit(1)
    qs = load_pillar(path)
    per_pillar_counts[f"P{i}"] = len(qs)
    # Tag each question with pillar (for diagnostic; will be stripped before save)
    for q in qs:
        q["_pillar"] = f"P{i}"
    all_questions.extend(qs)

print(f"=== Loaded {len(all_questions)} questions from 6 pillars ===")
for p, n in per_pillar_counts.items():
    print(f"  {p}: {n}")

# === Step 2: Tier distribution ===
tiers = Counter(q["tier"] for q in all_questions)
print(f"\n=== Tier distribution ===")
for t in sorted(tiers):
    print(f"  T{t}: {tiers[t]}")

# === Step 3: Cross-pillar duplicate detection ===
print(f"\n=== Cross-pillar duplicate check ===")
stem_counts = Counter(q["question"].strip() for q in all_questions)
duplicates = [(stem, n) for stem, n in stem_counts.items() if n > 1]
print(f"Exact-stem duplicates: {len(duplicates)}")
if duplicates:
    for stem, n in duplicates[:10]:
        print(f"  ×{n}: {stem[:60]}")

# === Step 4a: Dedup exact-stem cross-pillar duplicates (keep first occurrence) ===
seen_stems = set()
deduped = []
dropped = 0
for q in all_questions:
    stem = q["question"].strip()
    if stem in seen_stems:
        dropped += 1
        continue
    seen_stems.add(stem)
    deduped.append(q)
print(f"\n=== Dedup pass: dropped {dropped} exact-stem dupes; kept {len(deduped)} ===")
all_questions = deduped

# === Step 4: Validate every question against the FULL combined bank ===
# This catches cross-pillar collisions that per-pillar agents couldn't see.
print(f"\n=== Cross-pillar validation against full bank ===")
clean_bank = [{k: v for k, v in q.items() if not k.startswith("_")} for q in all_questions]
dup, ans = build_bank_indices(clean_bank)

results = {"PASS": 0, "SOFT_WARN": 0, "FAIL": 0}
fail_examples = []
for i, q in enumerate(clean_bank):
    r = validate_rewrite("math", q, bank=clean_bank, dup_index=dup, answer_index=ans, replace_idx=i)
    results[r["verdict"]] += 1
    if r["verdict"] == "FAIL":
        if len(fail_examples) < 10:
            fail_examples.append((i, q.get("tier"), q.get("question", "")[:60], r["hard_fails"]))

print(f"PASS: {results['PASS']}")
print(f"SOFT_WARN: {results['SOFT_WARN']}")
print(f"FAIL: {results['FAIL']}")

if fail_examples:
    print("\n=== FAIL examples (first 10) ===")
    for idx, tier, stem, fails in fail_examples:
        reasons = "; ".join(f"{g}: {r[:80]}" for g, r in fails[:2])
        print(f"  #{idx} T{tier} {stem!r}: {reasons}")

# === Step 5: Filter to PASS/SOFT_WARN only and replace bank ===
final_bank = []
for i, q in enumerate(clean_bank):
    r = validate_rewrite("math", q, bank=clean_bank, dup_index=dup, answer_index=ans, replace_idx=i)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        final_bank.append(q)

print(f"\n=== Final bank size: {len(final_bank)} (dropped {len(clean_bank) - len(final_bank)} FAIL records) ===")

# === Step 6: Save ===
BANK_PATH.write_text(json.dumps(final_bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"\nWrote {BANK_PATH} ({len(final_bank)} questions)")
