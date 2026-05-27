"""Fix the last 5 weasel closers found in re-hunt."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402

# subject -> [(bank_idx, new_closer_question, optional_new_answer_text)]
FIXES = {
    "animal": [
        {
            "bank_idx": 450,
            "new_closer_question": "Without genes carrying the recipe, what mechanism passes the behavior from one orca to the next?",
        },
    ],
    "economics": [
        {
            "bank_idx": 408,
            "new_closer_question": "What specifically did Volcker do?",
        },
        {
            "bank_idx": 1159,
            "new_closer_question": "What changed inside one day?",
        },
    ],
    "philosophy": [
        {
            "bank_idx": 612,
            "new_closer_question": "What does the room operator have that a real Chinese speaker has but his rule-book doesn't supply?",
        },
        {
            "bank_idx": 635,
            "new_closer_question": "What does it mean that the right hemisphere acts on visual information the patient denies seeing?",
        },
    ],
}


def apply_one(subject, idx, new_closer):
    bank_path = Path(f"data/questions/{subject}.json")
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    if not (0 <= idx < len(bank)):
        print(f"  !! bad idx {idx}")
        return False

    q = dict(bank[idx])
    # Replace the closing question only — find last "?" and rebuild
    stem = q["question"].rstrip()
    # Find the final question (after last sentence-end or period before final ?)
    # Simplest: split on ". " and take everything before the last sentence
    parts = stem.split(". ")
    # The last part is the question. Replace it.
    parts[-1] = new_closer
    q["question"] = ". ".join(parts)

    # Validate
    dup, ans = build_bank_indices(bank)
    r = validate_rewrite(subject, q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    status = r["verdict"]
    print(f"  {subject}#{idx}: {status}")
    if status == "FAIL":
        for g, reason in r["hard_fails"][:3]:
            print(f"    - {g}: {reason}")
        return False
    bank[idx] = q
    bank_path.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


total = 0
ok = 0
for subject, fix_list in FIXES.items():
    for f in fix_list:
        total += 1
        if apply_one(subject, f["bank_idx"], f["new_closer_question"]):
            ok += 1

print()
print(f"Applied {ok}/{total}")
