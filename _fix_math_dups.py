"""Bug-bash B8: fix 25 math questions with duplicate choices.

Pattern: bulk-gen produced 4 distractors where the formula happened to
collide on certain inputs (e.g. Rectangle 6×3 → both base+width=9 and
some other formula = 18, plus 18 from the correct answer).

Strategy: regenerate the 3 distractors per question with simple plausible-
error perturbations of the correct answer:
  - off-by-one (±1, ±2)
  - common formula confusion (perimeter when asked area, etc.)
  - sign flip / dropped decimal

All math gates exempt or pass-friendly (no length_parity, no anti_rote)
so the fix can be mechanical.
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/math.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))

# Find all dup-choice questions
dup_ixs = [i for i, q in enumerate(bank) if len(set(q.get("choices", []))) != len(q.get("choices", []))]
print(f"Found {len(dup_ixs)} dup-choice math questions")


def _strip_pi(s):
    return s.replace("π", "").replace("pi", "").strip()


def _parse_num(s):
    """Parse a choice string to a numeric value. Returns (value, is_pi_form) or None."""
    if not isinstance(s, str):
        return None
    s = s.strip()
    is_pi = "π" in s
    bare = _strip_pi(s) if is_pi else s
    try:
        # Integer first
        return (int(bare), is_pi)
    except ValueError:
        try:
            return (float(bare), is_pi)
        except ValueError:
            return None


def _format(val, is_pi):
    if isinstance(val, float):
        if val == int(val):
            val = int(val)
        else:
            val = round(val, 2)
    return f"{val}π" if is_pi else str(val)


def regenerate_distractors(correct: str, rng) -> list[str]:
    """Generate 3 plausible-error distractors for a correct numeric answer."""
    parsed = _parse_num(correct)
    if parsed is None:
        return []
    val, is_pi = parsed
    candidates = set()
    # Off-by-one family (rectangle area perturbations)
    for delta in (-3, -2, -1, 1, 2, 3, -correct_off if False else 0):
        if delta == 0:
            continue
        candidates.add(_format(val + delta, is_pi))
    # Common formula confusion: half (radius vs diameter) / double / squared
    if val and val > 0:
        candidates.add(_format(val * 2, is_pi))
        if val % 2 == 0 and val >= 2:
            candidates.add(_format(val // 2, is_pi))
    # Off the actual answer
    candidates.discard(correct)
    # Pick 3 distinct
    candidates = list(candidates)
    rng.shuffle(candidates)
    return candidates[:3]


fixes_applied = 0
fixes_failed = 0
rng = random.Random(42)

dup, ans = build_bank_indices(bank)

for idx in dup_ixs:
    q = bank[idx]
    correct = q.get("answer", "")
    # Build new choices = correct + 3 fresh distractors
    new_dists = regenerate_distractors(correct, rng)
    if len(new_dists) < 3:
        print(f"  #{idx}: SKIP (could not generate 3 distractors for {correct!r})")
        fixes_failed += 1
        continue
    new_choices = [correct] + new_dists
    # Place correct in a random slot
    rng.shuffle(new_choices)
    q_new = dict(q)
    q_new["choices"] = new_choices
    q_new["answer"] = correct
    r = validate_rewrite("math", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q_new
        dup, ans = build_bank_indices(bank)
        fixes_applied += 1
    else:
        # Try once more with different RNG seed for that question
        for retry_seed in range(10):
            _r = random.Random(idx * 100 + retry_seed)
            new_dists = regenerate_distractors(correct, _r)
            if len(new_dists) < 3:
                continue
            new_choices = [correct] + new_dists
            _r.shuffle(new_choices)
            q_new = dict(q)
            q_new["choices"] = new_choices
            q_new["answer"] = correct
            r = validate_rewrite("math", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
            if r["verdict"] in ("PASS", "SOFT_WARN"):
                bank[idx] = q_new
                dup, ans = build_bank_indices(bank)
                fixes_applied += 1
                break
        else:
            print(f"  #{idx}: FAIL all retries — correct={correct!r}")
            for g, reason in r["hard_fails"][:2]:
                print(f"    {g}: {reason[:150]}")
            fixes_failed += 1

print(f"\nApplied: {fixes_applied}/{len(dup_ixs)}; Failed: {fixes_failed}")

if fixes_applied:
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {BANK_PATH}")

# Verify no more dups
final_dups = [i for i, q in enumerate(bank) if len(set(q.get("choices", []))) != len(q.get("choices", []))]
print(f"\nRemaining dup-choice questions: {len(final_dups)}")
