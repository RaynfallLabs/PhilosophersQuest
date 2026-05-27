"""Fix the answer_collision between AI bank#997 and bank#1151 — two
different topics (COVID surveillance/mandate infrastructure vs COVID
censorship infrastructure) got identical generic answers.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402

# Load and modify the _weasel_v2_fix_ai patch in place
patch_path = Path("_weasel_v2_fix_ai.json")
patch = json.loads(patch_path.read_text(encoding="utf-8"))

# #997: COVID surveillance/mandate infrastructure — differentiate answer
# #1151: COVID censorship infrastructure — differentiate answer
DIFFERENTIATED = {
    997: {
        "answer": "Vaccine-passport apps, mandate registries, and contact-tracing systems are usually NOT formally repealed — they sit on the shelf available for re-activation",
        "choice_idx_to_replace": 0,
    },
    1151: {
        "answer": "It persists on the tech stack — flagging pipelines stay even after the original framing fades",
        "choice_idx_to_replace": 0,
    },
}

# Find and update
for op in patch:
    idx = op.get("bank_idx")
    if idx in DIFFERENTIATED:
        new_q = op["new"]
        new_answer = DIFFERENTIATED[idx]["answer"]
        new_q["answer"] = new_answer
        new_q["choices"][0] = new_answer

patch_path.write_text(json.dumps(patch, indent=2, ensure_ascii=False), encoding="utf-8")

# Validate the two fixed questions against the bank
bank = json.loads(Path("data/questions/ai.json").read_text(encoding="utf-8"))
# Apply all weasel-v2 rewrites first (simulation)
for op in patch:
    idx = op.get("bank_idx")
    if idx is not None and 0 <= idx < len(bank):
        bank[idx] = op["new"]
dup, ans = build_bank_indices(bank)
for idx in (997, 1151):
    r = validate_rewrite("ai", bank[idx], bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    print(f"bank#{idx}: {r['verdict']}")
    if r["verdict"] == "FAIL":
        for g, reason in r["hard_fails"][:3]:
            print(f"  - {g}: {reason}")
