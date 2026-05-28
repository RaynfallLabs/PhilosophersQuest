"""Phase E economics fixes: critical + distractor-suffix strip + weasels + name fixes."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/economics.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))


def replace_closer(stem: str, new_closer: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', stem.rstrip())
    for i in range(len(sentences) - 1, -1, -1):
        if sentences[i].rstrip().endswith('?'):
            sentences[i] = new_closer
            break
    return ' '.join(sentences)


# === Telegraph suffix patterns to strip from distractors ===
TELEGRAPH_PATTERNS = [
    r"\s*[—\-]\s*a position contradicting the Austrian record",
    r"\s*[—\-]\s*a position contradicting Rothbard'?s reputation",
    r"\s*[—\-]\s*a position contradicting [A-Z][a-z]+'?s",
    r"\s*[—\-]\s*inversion(?:\b|$)",
    r"\s*[—\-]\s*a denial(?:\b|$)",
    r"\s*[—\-]\s*legal technicality",
    r"\s*[—\-]\s*a misreading of (?:Mises|Hayek|Friedman)",
    r"\s*[—\-]\s*Austrians anticipated this",
    r"\s*[—\-]\s*Mises anticipated this",
]


def strip_telegraph(text: str) -> str:
    """Strip telegraph suffix from a single choice text."""
    for pat in TELEGRAPH_PATTERNS:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)
    return text.rstrip(" —-")


FIXES = []

# === CRITICAL #59: Austrians warned of 1929 not 2008 ===
FIXES.append({
    "idx": 59,
    "patch": {
        "question": "Austrian economists predicted a major American economic bust using their business-cycle theory BEFORE it happened. Hayek's monthly bulletins at the Austrian Institute for Business Cycle Research predicted the US stock-market collapse beginning months in advance. Which historic bust did the Austrians famously call FIRST?",
        "answer": "The 1929 Wall Street crash and Great Depression",
        "choices": [
            "The 1929 Wall Street crash and Great Depression",
            "The 2008 US housing collapse and global financial crisis",
            "The 2000 dot-com bubble crash in technology stocks",
            "The 1973 oil shock recession across Western economies",
        ],
        "context": "Hayek and Mises both warned that the US Federal Reserve's easy-credit policies in the 1920s would produce a bust. Hayek's prediction in early 1929 monthly bulletins at the Vienna Austrian Institute for Business Cycle Research is well-documented. Both Mises and Hayek would later be cited for predicting the 2008 crash as well (Mises was dead but his framework predicted it), but the FIRST famous Austrian call was 1929.",
    },
    "reason": "Fix factual: Austrians' first major predictive call was 1929 (Hayek's bulletins), not 2008.",
})

# === FACTUAL #484: Heilbroner was at The New School not Harvard ===
q484 = bank[484]
new_ctx = q484.get("context", "").replace("Harvard", "The New School for Social Research")
FIXES.append({
    "idx": 484,
    "patch": {"context": new_ctx},
    "reason": "Fix factual: Heilbroner was at The New School his entire career, not Harvard.",
})

# === FACTUAL #965, #966: Lewellyn → Llewellyn Rockwell ===
for idx in [965, 966]:
    q = bank[idx]
    new_q = q["question"].replace("Lewellyn", "Llewellyn")
    new_a = q["answer"].replace("Lewellyn", "Llewellyn")
    new_c = [c.replace("Lewellyn", "Llewellyn") for c in q["choices"]]
    new_ctx = q.get("context", "").replace("Lewellyn", "Llewellyn")
    FIXES.append({
        "idx": idx,
        "patch": {"question": new_q, "answer": new_a, "choices": new_c, "context": new_ctx},
        "reason": "Fix misspelling: Lewellyn → Llewellyn H. Rockwell Jr.",
    })

# === TELEGRAPH-SUFFIX STRIP across all affected questions ===
TELEGRAPH_IDX = [423, 449, 451, 456, 460, 960, 977, 985, 986, 988, 991, 992, 993, 997, 998, 999, 1002, 1005, 1007, 1008, 1011, 1013, 1014, 1016, 1019, 1023, 1024, 1026, 1030, 1032, 1033, 1035, 1037, 1038]

for idx in TELEGRAPH_IDX:
    q = bank[idx]
    stripped_choices = [strip_telegraph(c) for c in q["choices"]]
    stripped_answer = strip_telegraph(q["answer"])
    # Apply only if something actually changed
    if stripped_choices != q["choices"] or stripped_answer != q["answer"]:
        # Sync answer text if it appears in stripped choices
        if stripped_answer in stripped_choices:
            FIXES.append({
                "idx": idx,
                "patch": {"answer": stripped_answer, "choices": stripped_choices},
                "reason": "Strip telegraph-suffix from distractors (scaffold artifact).",
            })

# === WEASEL CLOSERS ===
WEASEL_REWRITES = [
    (137, "Why does dilution of money supply matter for a saver?"),
    (538, "What property does Bitcoin's design give every node owner?"),
    (543, "What's missing from Bitcoin's design that every fiat currency has?"),
    (564, "What single technical property distinguishes Bitcoin from other cryptos?"),
    (817, "What does Bitcoin specifically protect users from?"),
    (823, "What protection does Bitcoin specifically NOT offer holders against?"),
    (868, "What's the seen-and-unseen distinction in this case?"),
    (926, "What's the unseen cost of rent control?"),
    (1155, "What does public choice theory predict bureaucrats will maximize?"),
    (1269, "Who pays the corporate income tax, ultimately?"),
    (1325, "What did the entrepreneur risk that VCs typically don't?"),
    (1364, "What pattern in Madoff's returns should have signaled fraud?"),
    (1410, "What three things should a young investor check before believing a stock tip?"),
    (1411, "What recurring institutional failure do these four fraud cases share?"),
]

for idx, new_closer in WEASEL_REWRITES:
    old_stem = bank[idx]["question"]
    new_stem = replace_closer(old_stem, new_closer)
    FIXES.append({
        "idx": idx,
        "patch": {"question": new_stem},
        "reason": f"Replace §15 weasel: {new_closer[:60]}...",
    })


# Apply
dup, ans = build_bank_indices(bank)
print(f"Applying {len(FIXES)} economics fixes...\n")

results = {"applied": [], "failed": []}
for fix in FIXES:
    idx = fix["idx"]
    q_new = dict(bank[idx])
    for k, v in fix["patch"].items():
        q_new[k] = v
    r = validate_rewrite("economics", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q_new
        results["applied"].append((idx, fix["reason"], r["verdict"]))
        dup, ans = build_bank_indices(bank)
    else:
        results["failed"].append((idx, [f"{g}: {reason[:200]}" for g, reason in r["hard_fails"]]))

print(f"Applied: {len(results['applied'])}")
print(f"Failed: {len(results['failed'])}")

if results["failed"]:
    print("\n=== FAILED (first 10) ===")
    for idx, reasons in results["failed"][:10]:
        print(f"  #{idx}: {reasons}")

if results["applied"]:
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {BANK_PATH}")
