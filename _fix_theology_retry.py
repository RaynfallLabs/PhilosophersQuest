"""Retry theology fixes with length adjustments."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

bank = json.loads(Path("data/questions/theology.json").read_text(encoding="utf-8"))
dup, ans = build_bank_indices(bank)

# #27 - lengthen answer
q = dict(bank[27])
q["answer"] = "A manger for animal feed"
q["choices"] = [
    "A manger for animal feed",
    "A cradle in the innkeeper's loft",
    "A wooden basket beside the door",
    "A bed of straw on the temple floor",
]
r = validate_rewrite("theology", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=27)
print(f"#27: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[27] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]: print(f"  {g}: {reason[:150]}")

# #765 - trim stem (just changed phrasing)
q = dict(bank[765])
# Original was 'a beautiful woman bathing on a rooftop' replaced with 'from his palace roof a beautiful woman bathing below'
# That made it longer. Let me trim differently.
q["question"] = bank[765]["question"].replace(
    "saw a beautiful woman bathing on a rooftop",
    "saw a woman bathing below from his palace roof"
)
r = validate_rewrite("theology", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=765)
print(f"#765: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[765] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]: print(f"  {g}: {reason[:150]}")

# #46 - trim distractors to shorter parens form
q = dict(bank[46])
q["choices"] = [
    "Golgotha (Place of the Skull)",
    "Mount Sinai (desert mount)",
    "Mount Carmel (Elijah's mount)",
    "Mount Olives (Garden mount)",
]
q["answer"] = "Golgotha (Place of the Skull)"
r = validate_rewrite("theology", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=46)
print(f"#46: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[46] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]: print(f"  {g}: {reason[:150]}")

# #761 - lengthen "still small voice" to match
q = dict(bank[761])
q["answer"] = "A still small voice — a gentle whisper at the cave mouth"
q["choices"] = [
    "A still small voice — a gentle whisper at the cave mouth",
    "A blinding light brighter than the noon sun over Horeb",
    "A great voice like the roar of many waters from the cave",
    "A clap of thunder that shook the mountain to its roots",
]
r = validate_rewrite("theology", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=761)
print(f"#761: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[761] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]: print(f"  {g}: {reason[:150]}")

Path("data/questions/theology.json").write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("Wrote bank")
