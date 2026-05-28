"""Cooking retry: length-parity + stem-budget failures."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/cooking.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))


def replace_closer(stem: str, new_closer: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', stem.rstrip())
    for i in range(len(sentences) - 1, -1, -1):
        if sentences[i].rstrip().endswith('?'):
            sentences[i] = new_closer
            break
    return ' '.join(sentences)


dup, ans = build_bank_indices(bank)

# === #416 — tighten answer to match distractors (~105 chars) ===
q = dict(bank[416])
q["answer"] = "Sous-vide gives uniform doneness with no smoke; smoke deposits flavor compounds in patchwork"
q["choices"] = [
    "Sous-vide gives uniform doneness with no smoke; smoke deposits flavor compounds in patchwork",
    "Sous-vide builds a thicker bark on the surface while smoking keeps the exterior pale and gel-like",
    "Sous-vide develops more pronounced Maillard during the bath while smoking just sears for color",
    "Sous-vide reduces total cook time because the bath operates hotter than a wood-fired smoker",
]
r = validate_rewrite("cooking", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=416)
print(f"#416: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[416] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]: print(f"  {g}: {reason[:160]}")

# === #464 — tighten distractors to match answer (142 chars) ===
q = dict(bank[464])
q["choices"] = [
    "Salt brine selects for lactic-acid bacteria and inhibits spoilage organisms; the cucumber ferments slowly into a sour pickle via Lactobacillus",
    "Salt brine cools the cucumber faster than vinegar alone; rapid cooling locks in green color and crunch before vinegar softens the cucumber",
    "Salt brine adds dietary minerals to the cucumber over long pickling; a fermented pickle has higher mineral content than a fresh cucumber does",
    "Salt brine seals the cucumber's surface with crystal layers; the crystals shield it from air during the long pickling and slow aging in the jar",
]
q["answer"] = q["choices"][0]
r = validate_rewrite("cooking", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=464)
print(f"#464: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[464] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]: print(f"  {g}: {reason[:160]}")

# === #469 — extend answer to match distractors (~110 chars) ===
q = dict(bank[469])
q["answer"] = "Maillard needs amino acid plus reducing sugar near 140C; caramelization is sugar alone above ~160C dry heat"
q["choices"] = [
    "Maillard needs amino acid plus reducing sugar near 140C; caramelization is sugar alone above ~160C dry heat",
    "Maillard requires no sugar and high dry heat alone; caramelization is the same reaction but with water added",
    "Both are the same chemistry at progressively higher temperatures; the names just label different stages",
    "Maillard is enzymatic and happens at room temperature on protein; caramelization requires baking specifically",
]
r = validate_rewrite("cooking", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=469)
print(f"#469: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[469] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]: print(f"  {g}: {reason[:160]}")

# === #478 — rewrite for parity (~155 chars each) ===
q = dict(bank[478])
q["choices"] = [
    "Brisket: deep collagen-to-gelatin plus extensive smoke compound deposition; char siu: rapid Maillard plus caramelized glaze plus surface char",
    "Brisket: full surface drying to dense dark bark; char siu: full meat hydration through a wet glaze that prevents Maillard browning from forming",
    "Brisket: slow caramelization of internal sugars from the rub; char siu: slow caramelization of the marinade across long roasting at low heat",
    "Brisket: enzymatic conversion of fat to muscle during long smoke; char siu: enzymatic protein denaturation producing tender meat at high heat",
]
q["answer"] = q["choices"][0]
r = validate_rewrite("cooking", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=478)
print(f"#478: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[478] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]: print(f"  {g}: {reason[:160]}")

# === #484 — rewrite for parity (~170 chars each) ===
q = dict(bank[484])
q["choices"] = [
    "Recognize that fast-grill achieves surface Maillard quickly but cannot melt collagen; slow-smoke does the collagen plus deep smoke deposition",
    "Recognize that fast-grill is for tender cuts only while slow-smoke is for tough cuts only; both styles are valid for their target cuts only",
    "Recognize that fast-grill is a modern industrial invention while slow-smoke is the only authentic barbecue worth eating in any restaurant ever",
    "Recognize that fast-grill produces nutritionally inferior food while slow-smoke preserves more vitamins; the slow method is the healthier choice",
]
q["answer"] = q["choices"][0]
r = validate_rewrite("cooking", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=484)
print(f"#484: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[484] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]: print(f"  {g}: {reason[:160]}")

# === #489 — rewrite for parity (~175 chars each) ===
q = dict(bank[489])
q["choices"] = [
    "Claim: cooking is fully scientific and benefits from systematic measurement; critique: knowing the chemistry is not the same as trained-hand intuition that lives in long practice",
    "Claim: traditional cooking is wrong and should be replaced by laboratory methods; critique: traditional methods produced good food for centuries without any need for replacement",
    "Claim: home cooks should buy equipment to match restaurants; critique: the gear is too expensive for home use and modernist methods stay limited to commercial kitchens only",
    "Claim: chemistry alone determines food quality; critique: ingredient quality matters more than technique, so modernist focus on technique misses the deeper source of cooking",
]
q["answer"] = q["choices"][0]
r = validate_rewrite("cooking", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=489)
print(f"#489: {r['verdict']}")
if r["verdict"] in ("PASS", "SOFT_WARN"):
    bank[489] = q
    dup, ans = build_bank_indices(bank)
else:
    for g, reason in r["hard_fails"][:2]: print(f"  {g}: {reason[:160]}")

# === STEM-BUDGET retries: shorter closers ===

STEM_RETRIES = [
    (39, "Why does the city sourdough taste like the city?"),
    (358, "What process does this case study expose about cuisine identity?"),
    (716, "What did salt-fish trade buy across northern Europe?"),
    (722, "What did the no-meat days do to fish-preservation industry?"),
]

for idx, new_closer in STEM_RETRIES:
    q = dict(bank[idx])
    old_stem = q["question"]
    q["question"] = replace_closer(old_stem, new_closer)
    r = validate_rewrite("cooking", q, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    print(f"#{idx}: {r['verdict']}")
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q
        dup, ans = build_bank_indices(bank)
    else:
        for g, reason in r["hard_fails"][:2]: print(f"  {g}: {reason[:160]}")


BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("\nWrote bank")
