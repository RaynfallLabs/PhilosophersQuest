"""Phase E animal fixes: weasel closers + parens skim-tells + minor."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/animal.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))


def replace_closer(stem: str, new_closer: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', stem.rstrip())
    for i in range(len(sentences) - 1, -1, -1):
        if sentences[i].rstrip().endswith('?'):
            sentences[i] = new_closer
            break
    return ' '.join(sentences)


FIXES = []

# === WEASEL CLOSERS — replace with pointed concrete questions ===
WEASEL_CLOSERS = [
    (30, "What was Alex's last spoken sentence the night before he died?"),  # 'You be good, I love you, see you tomorrow'
    (75, "How does a young cuckoo know to perform the egg-ejection if it has never seen another cuckoo do it?"),
    (81, "What do forebrain-neuron counts reveal about avian brains compared to mammalian brains of the same size?"),
    (82, "What did the 19th-century specimen-collecting practice produce that modern naturalists can no longer match?"),
    (114, "When female manakins from one population reject males from another, what evolutionary process has begun?"),
    (190, "What body covering does the presence of quill knobs on Velociraptor's forearm bones directly confirm?"),
    (246, "About what fraction of the food on a typical human plate comes from crops bees help pollinate?"),
    (247, "About how much do American farmers save each year from bat-eaten crop pests?"),
    (301, "When two species this distantly related arrive at the same gliding body plan, what process explains it?"),
    (340, "What is the evolutionary process called when marsupial and placental versions independently evolve the same body plan?"),
    (615, "When ants, bees, and termites independently evolve queen-plus-sterile-worker colonies, what process explains it?"),
    (620, "What specific arrangement defines a moray-and-cleaner-shrimp relationship?"),
    (662, "What kind of evolutionary event does the four-Devonian-arachnid-order coincidence signal?"),
    (678, "What does the Tibbetts wasp result overturn about which animals can do face recognition?"),
    (682, "What unit of selection does Sacculina's manipulation of crab behavior favor in the Dawkins frame?"),
    (869, "Where does a wild poison dart frog actually get its skin toxin from, since zoo-raised ones lose it?"),
]

for idx, new_closer in WEASEL_CLOSERS:
    old_stem = bank[idx]["question"]
    new_stem = replace_closer(old_stem, new_closer)
    FIXES.append({
        "idx": idx,
        "patch": {"question": new_stem},
        "reason": f"Replace §15 weasel closer: {new_closer[:60]}...",
    })


# === CITATION SKIM-TELLS — move citation from answer to context ===
# Pattern: strip "(Author et al. YYYY)" from answer text

CITATION_RE = re.compile(r"\s*\((?:[A-Z][a-z]+(?:\s+(?:et al\.|and\s+[A-Z][a-z]+))?)\s*,?\s*(?:\d{4}[a-z]?)\)", re.IGNORECASE)
CITATION_RE2 = re.compile(r"\s*[—\-]\s*(?:[A-Z][a-z]+(?:\s+(?:et al\.|and\s+[A-Z][a-z]+))?,?\s*\d{4}[a-z]?)", re.IGNORECASE)

CITATION_FIXES = [63, 679, 689, 705, 708]  # citation-only-in-correct skim-tells

for idx in CITATION_FIXES:
    q = bank[idx]
    new_answer = q["answer"]
    # Try both patterns
    new_answer2 = CITATION_RE.sub("", new_answer)
    if new_answer2 == new_answer:
        new_answer2 = CITATION_RE2.sub("", new_answer)
    new_answer2 = new_answer2.strip()

    if new_answer2 != new_answer and new_answer2 in q.get("choices", []) + [new_answer]:
        # Update both answer and choices
        new_choices = [new_answer2 if c == new_answer else c for c in q["choices"]]
        FIXES.append({
            "idx": idx,
            "patch": {
                "answer": new_answer2,
                "choices": new_choices,
            },
            "reason": f"Move citation from answer to context: removed {q['answer'][len(new_answer2):]!r}",
        })


# === PARENS-DECORATION skim-tells: strip parens-explanation from answer ===

# Helper to strip parens from an answer if the parens are the only ones across all 4 choices
def strip_parens_skimtell(idx, bank):
    q = bank[idx]
    if "(" not in q["answer"]:
        return None
    # Count parens-bearing choices
    n_parens = sum(1 for c in q["choices"] if "(" in c)
    if n_parens != 1:
        return None  # not a unique skim-tell
    # Strip parens from answer
    new_answer = re.sub(r"\s*\([^)]+\)", "", q["answer"]).strip()
    if not new_answer:
        return None
    new_choices = [new_answer if c == q["answer"] else c for c in q["choices"]]
    return {"answer": new_answer, "choices": new_choices}


PARENS_FIXES = [226, 433, 505, 533, 686, 698, 700, 782, 784, 829, 897, 926, 933]

for idx in PARENS_FIXES:
    patch = strip_parens_skimtell(idx, bank)
    if patch:
        FIXES.append({
            "idx": idx,
            "patch": patch,
            "reason": "Strip parens-decoration skim-tell from answer.",
        })


# === APPLY ===
dup, ans = build_bank_indices(bank)
print(f"Applying {len(FIXES)} animal fixes...\n")

results = {"applied": [], "failed": []}
for fix in FIXES:
    idx = fix["idx"]
    q_new = dict(bank[idx])
    for k, v in fix["patch"].items():
        q_new[k] = v
    r = validate_rewrite("animal", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q_new
        results["applied"].append((idx, fix["reason"], r["verdict"]))
        dup, ans = build_bank_indices(bank)
    else:
        results["failed"].append((idx, [f"{g}: {reason[:200]}" for g, reason in r["hard_fails"]]))

print(f"Applied: {len(results['applied'])}")
print(f"Failed: {len(results['failed'])}")

if results["failed"]:
    print("\n=== FAILED ===")
    for idx, reasons in results["failed"]:
        print(f"  #{idx}: {reasons}")

if results["applied"]:
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {BANK_PATH}")
