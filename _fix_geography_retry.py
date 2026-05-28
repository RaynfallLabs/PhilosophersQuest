"""Geography retry: shorter weasel closers + skip parens-strips that broke parity."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/geography.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))


def replace_closer(stem: str, new_closer: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', stem.rstrip())
    for i in range(len(sentences) - 1, -1, -1):
        if sentences[i].rstrip().endswith('?'):
            sentences[i] = new_closer
            break
    return ' '.join(sentences)


dup, ans = build_bank_indices(bank)

# Shorter closers
RETRIES = [
    (840, "Where does the chief temple sit, and what does that placement say?"),
    (861, "Which two coastal networks did Huguenot 'places of surety' cluster on?"),
    (870, "What two factors kept the Druze religion alive in their mountains?"),
    (903, "Which two American sub-cultures did the trial set against each other?"),
    (910, "What religious-ethnic identity did the Yugoslav wars track?"),
    (911, "What did the Belfast peace walls fuse together?"),
]

applied = 0
failed = []
for idx, new_closer in RETRIES:
    q = dict(bank[idx])
    q["question"] = replace_closer(q["question"], new_closer)
    r = validate_rewrite("geography", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    print(f"#{idx}: {r['verdict']}")
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q
        dup, ans = build_bank_indices(bank)
        applied += 1
    else:
        failed.append(idx)
        for g, reason in r["hard_fails"][:1]: print(f"  {g}: {reason[:140]}")

print(f"\nApplied: {applied}/{len(RETRIES)}")
if applied:
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote bank")
