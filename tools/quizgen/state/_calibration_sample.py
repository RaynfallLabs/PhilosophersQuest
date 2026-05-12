"""
Stratified-by-tier random sample of philosophy bank for v4 moral_vision calibration.
Reproducible with seed 20260510.
"""
import json
import random
import re
import statistics
from pathlib import Path

SRC = Path(r"C:\Users\brand\Documents\PhilosophersQuest\data\questions\philosophy.json")
SEED = 20260510
PER_TIER = 5
TIERS = [1, 2, 3, 4, 5]

with SRC.open("r", encoding="utf-8") as fh:
    bank = json.load(fh)

print(f"Bank total: {len(bank)}")

# Group by tier
by_tier = {t: [] for t in TIERS}
for i, q in enumerate(bank):
    t = q.get("tier")
    if t in by_tier:
        # Attach original index so we can refer back unambiguously
        by_tier[t].append((i, q))

for t in TIERS:
    print(f"  T{t}: {len(by_tier[t])}")

random.seed(SEED)

# Stratified sample
sample = []
for t in TIERS:
    pool = by_tier[t]
    picks = random.sample(pool, PER_TIER)
    for idx, q in picks:
        q2 = dict(q)
        q2["_idx"] = idx
        sample.append(q2)

# Deterministic gate computation per question
ANTI_ROTE_PATTERNS = [
    re.compile(r"\bwhat (is|does)\b.*\bmean\b", re.IGNORECASE),
    re.compile(r"\bwho (wrote|invented|tutored|founded)\b", re.IGNORECASE),
    re.compile(r"\bin what year\b", re.IGNORECASE),
    re.compile(r"\bwhat is the (german|greek|latin|french|sanskrit|chinese) term\b", re.IGNORECASE),
    re.compile(r"\bwhat is the definition of\b", re.IGNORECASE),
]


def deterministic_gates(q):
    tier = q.get("tier")
    question = q.get("question", "")
    answer = q.get("answer", "")
    choices = q.get("choices", [])
    context = q.get("context", "")

    # Gate 1: schema
    schema_present = bool(tier) and bool(question) and bool(answer) and isinstance(choices, list) and len(choices) == 4 and bool(context)
    answer_in_choices = answer in choices if isinstance(choices, list) else False
    schema_ok = schema_present and answer_in_choices

    # Gate 2: length parity
    lens = [len(c) for c in choices] if isinstance(choices, list) else []
    if lens:
        mean = statistics.mean(lens)
        longest = max(lens)
        shortest = min(lens) if min(lens) > 0 else 1
        ratio = longest / shortest
        # Any choice >+/-15% from mean?
        deviates = any(abs(L - mean) / mean > 0.15 for L in lens)
        parity_ok = (not deviates) and (ratio <= 1.30)
    else:
        mean = 0
        longest = 0
        shortest = 0
        ratio = 0
        parity_ok = False

    # Gate 3: total record cost
    total_cost = len(question) + sum(lens)
    if tier in (1, 2, 3):
        cost_ok = total_cost <= 600
    else:
        cost_ok = total_cost <= 800

    # Gate 4: anti-rote regex
    rote_matches = [p.pattern for p in ANTI_ROTE_PATTERNS if p.search(question)]
    rote_ok = len(rote_matches) == 0

    return {
        "schema_ok": schema_ok,
        "schema_detail": f"present={schema_present}, answer_in_choices={answer_in_choices}",
        "parity_ok": parity_ok,
        "parity_detail": f"mean={mean:.1f} ratio={ratio:.2f} lens={lens}",
        "cost_ok": cost_ok,
        "cost_detail": f"total={total_cost} (cap={'600' if tier in (1,2,3) else '800'})",
        "rote_ok": rote_ok,
        "rote_detail": (", ".join(rote_matches) if rote_matches else "ok"),
    }


# Output structured data for downstream analysis
out_path = Path(r"C:\Users\brand\Documents\PhilosophersQuest\tools\quizgen\state\_calibration_sample.json")
records = []
for q in sample:
    g = deterministic_gates(q)
    records.append({
        "idx": q["_idx"],
        "tier": q["tier"],
        "question": q["question"],
        "answer": q["answer"],
        "choices": q["choices"],
        "context": q.get("context", ""),
        "gates": g,
    })

with out_path.open("w", encoding="utf-8") as fh:
    json.dump(records, fh, ensure_ascii=False, indent=2)

print(f"Sample written to {out_path}")
print(f"Sample size: {len(records)} (expected {PER_TIER * len(TIERS)})")
print("Tiers present:", sorted({r['tier'] for r in records}))

# Quick aggregate
print("\n--- Deterministic gate fails per tier ---")
for t in TIERS:
    tier_recs = [r for r in records if r["tier"] == t]
    fail_schema = sum(1 for r in tier_recs if not r["gates"]["schema_ok"])
    fail_parity = sum(1 for r in tier_recs if not r["gates"]["parity_ok"])
    fail_cost = sum(1 for r in tier_recs if not r["gates"]["cost_ok"])
    fail_rote = sum(1 for r in tier_recs if not r["gates"]["rote_ok"])
    print(f"T{t}: schema_fail={fail_schema} parity_fail={fail_parity} cost_fail={fail_cost} rote_fail={fail_rote}")
