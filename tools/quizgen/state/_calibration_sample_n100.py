"""
Stratified-by-tier random sample of philosophy bank for v4 moral_vision calibration (n=100).
Reproducible with seed 20260511 (disjoint from n=25 seed 20260510).

Applies the patched §6 anti-rote regex set from moral_vision.md v4 and the
deterministic gates A1-A4. Emits a JSON dump for downstream LLM scoring.
"""
import json
import random
import re
import statistics
from pathlib import Path

SRC = Path(r"C:\Users\brand\Documents\PhilosophersQuest\data\questions\philosophy.json")
SEED = 20260511
PER_TIER = 20
TIERS = [1, 2, 3, 4, 5]

with SRC.open("r", encoding="utf-8") as fh:
    bank = json.load(fh)

print(f"Bank total: {len(bank)}")

by_tier = {t: [] for t in TIERS}
for i, q in enumerate(bank):
    t = q.get("tier")
    if t in by_tier:
        by_tier[t].append((i, q))

for t in TIERS:
    print(f"  T{t}: {len(by_tier[t])}")

random.seed(SEED)

sample = []
for t in TIERS:
    pool = by_tier[t]
    picks = random.sample(pool, PER_TIER)
    for idx, q in picks:
        q2 = dict(q)
        q2["_idx"] = idx
        sample.append(q2)


# Patched §6 anti-rote regex set (from moral_vision.md v4)
PATCHED_ANTI_ROTE_PATTERNS = [
    (re.compile(r"^What (is|does) ['\"]", re.IGNORECASE), "what_is_quoted"),
    (re.compile(r"^What (is|does) the (term|word|name|definition|meaning) (for|of)", re.IGNORECASE), "what_is_term_for"),
    (re.compile(r"^What is the capital of", re.IGNORECASE), "capital_of"),
    (re.compile(r"^In what year (did|was)", re.IGNORECASE), "in_what_year"),
    (re.compile(r"^Who (wrote|invented|painted|composed|founded|tutored|discovered)", re.IGNORECASE), "who_did_thing"),
    (re.compile(r"^How many \w+ (are there|exist|did)", re.IGNORECASE), "how_many"),
    (re.compile(r"^What is the chemical symbol", re.IGNORECASE), "chemical_symbol"),
    (re.compile(r"^Define\b", re.IGNORECASE), "define_x"),
]

# Old (n=25) regex set, for comparison
OLD_ANTI_ROTE_PATTERNS = [
    (re.compile(r"\bwhat (is|does)\b.*\bmean\b", re.IGNORECASE), "what_x_mean"),
    (re.compile(r"\bwho (wrote|invented|tutored|founded)\b", re.IGNORECASE), "who_did_thing_old"),
    (re.compile(r"\bin what year\b", re.IGNORECASE), "in_what_year_old"),
    (re.compile(r"\bwhat is the (german|greek|latin|french|sanskrit|chinese) term\b", re.IGNORECASE), "foreign_term"),
    (re.compile(r"\bwhat is the definition of\b", re.IGNORECASE), "definition_of"),
]


def length_parity(choices):
    lens = [len(c) for c in choices] if isinstance(choices, list) else []
    if not lens or 0 in lens:
        return False, lens, 0, 0, 0
    mean = statistics.mean(lens)
    longest = max(lens)
    shortest = min(lens)
    ratio = longest / shortest
    deviates = any(abs(L - mean) / mean > 0.15 for L in lens)
    parity_ok = (not deviates) and (ratio <= 1.30)
    return parity_ok, lens, mean, longest / shortest, max(abs(L - mean) / mean for L in lens)


def deterministic_gates(q):
    tier = q.get("tier")
    question = q.get("question", "") or ""
    answer = q.get("answer", "") or ""
    choices = q.get("choices", [])
    context = q.get("context", "") or ""

    # A1 — Schema
    schema_present = (
        bool(tier)
        and bool(question)
        and bool(answer)
        and isinstance(choices, list)
        and len(choices) == 4
        and bool(context)
    )
    if isinstance(choices, list):
        choices_lc = [c.lower() if isinstance(c, str) else "" for c in choices]
        answer_in_choices = answer.lower() in choices_lc if isinstance(answer, str) else False
    else:
        answer_in_choices = False
    schema_ok = schema_present and answer_in_choices

    # A2 — Length parity
    parity_ok, lens, mean, ratio, max_dev = length_parity(choices)

    # A3 — Total record cost
    total_cost = len(question) + sum(lens)
    cap = 600 if tier in (1, 2, 3) else 800
    cost_ok = total_cost <= cap

    # A4 — Patched anti-rote regex
    patched_matches = [name for (p, name) in PATCHED_ANTI_ROTE_PATTERNS if p.search(question)]
    rote_ok_patched = len(patched_matches) == 0

    # A4-old — for delta comparison
    old_matches = [name for (p, name) in OLD_ANTI_ROTE_PATTERNS if p.search(question)]
    rote_ok_old = len(old_matches) == 0

    return {
        "A1_schema_ok": schema_ok,
        "A1_detail": f"present={schema_present}, answer_in_choices={answer_in_choices}",
        "A2_parity_ok": parity_ok,
        "A2_detail": f"lens={lens} mean={mean:.1f} ratio={ratio:.2f} max_dev={max_dev:.2%}",
        "A3_cost_ok": cost_ok,
        "A3_detail": f"total={total_cost} cap={cap}",
        "A4_rote_ok_patched": rote_ok_patched,
        "A4_patched_matches": patched_matches,
        "A4_rote_ok_old": rote_ok_old,
        "A4_old_matches": old_matches,
    }


out_path = Path(r"C:\Users\brand\Documents\PhilosophersQuest\tools\quizgen\state\_calibration_sample_n100.json")
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

# Aggregate determinstic results
print("\n--- Deterministic gate fail counts per tier ---")
for t in TIERS:
    tier_recs = [r for r in records if r["tier"] == t]
    fA1 = sum(1 for r in tier_recs if not r["gates"]["A1_schema_ok"])
    fA2 = sum(1 for r in tier_recs if not r["gates"]["A2_parity_ok"])
    fA3 = sum(1 for r in tier_recs if not r["gates"]["A3_cost_ok"])
    fA4_new = sum(1 for r in tier_recs if not r["gates"]["A4_rote_ok_patched"])
    fA4_old = sum(1 for r in tier_recs if not r["gates"]["A4_rote_ok_old"])
    print(f"T{t} (n={len(tier_recs)}): A1={fA1} A2={fA2} A3={fA3} A4_patched_fail={fA4_new} A4_old_fail={fA4_old}")

# Cross-comparison: which questions are caught by patched only?
patched_only = [r for r in records if not r["gates"]["A4_rote_ok_patched"] and r["gates"]["A4_rote_ok_old"]]
old_only = [r for r in records if r["gates"]["A4_rote_ok_patched"] and not r["gates"]["A4_rote_ok_old"]]
both = [r for r in records if not r["gates"]["A4_rote_ok_patched"] and not r["gates"]["A4_rote_ok_old"]]

print(f"\n--- Anti-rote regex delta ---")
print(f"Caught by patched only (NEW catches): {len(patched_only)}")
print(f"Caught by old only (regressions): {len(old_only)}")
print(f"Caught by both: {len(both)}")
print(f"Caught by neither: {len(records) - len(patched_only) - len(old_only) - len(both)}")

if patched_only:
    print("\nPatched-only matches (new catches):")
    for r in patched_only:
        print(f"  T{r['tier']} idx={r['idx']}  q={r['question'][:80]!r}  matches={r['gates']['A4_patched_matches']}")

if old_only:
    print("\nOld-only matches (regressions, should be empty if patch is monotonic):")
    for r in old_only:
        print(f"  T{r['tier']} idx={r['idx']}  q={r['question'][:80]!r}  old_matches={r['gates']['A4_old_matches']}")
