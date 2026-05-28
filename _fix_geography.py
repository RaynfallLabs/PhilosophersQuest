"""Phase E geography fixes: 8 critical + 48 parens-strips + 17 weasel closers."""
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


FIXES = []

# === CRITICAL #1015: GPS year wrong (1962 → 1973) ===
FIXES.append({
    "idx": 1015,
    "patch": {
        "question": bank[1015]["question"].replace(
            "1962 US-built GPS network grew out of Cold War-era American military positioning needs",
            "GPS network, authorized in 1973 and built by the US to meet Cold War military positioning needs,"
        ),
    },
    "reason": "Fix factual: GPS authorized 1973 (first launches 1978; full constellation 1995), not 1962.",
})

# === CRITICAL #745: Dup of #590. Rewrite to Tupaia of Raiatea (1769 Cook map) ===
FIXES.append({
    "idx": 745,
    "patch": {
        "question": "In 1769 Captain Cook's HMS Endeavour took aboard a Polynesian priest-navigator from the island of Raiatea, who proceeded to draw a chart of the Pacific from memory: ~74 islands across 4,800 km, with bearings and sailing times Cook later confirmed by sextant. The man's name was the same as that of an ancestor of three later Tahitian royal lines. Who was the navigator whose chart proved the wayfinding tradition was a real working technology?",
        "answer": "Tupaia of Raiatea, who joined Cook in 1769 and mapped some 74 islands from memory",
        "choices": [
            "Tupaia of Raiatea, who joined Cook in 1769 and mapped some 74 islands from memory",
            "Hipour of Polowat, who later sailed with David Lewis aboard the Isbjorn in 1970",
            "Mau Piailug of Satawal, who later navigated the Hokule'a from Hawaii to Tahiti in 1976",
            "Kupe of Hawaiki, the semi-legendary discoverer of Aotearoa around the year 950 AD",
        ],
        "context": "Tupaia (~1725-1770) of Raiatea was a high-ranking arioi priest and master navigator who came aboard Endeavour at Tahiti in July 1769. His chart, copied by Cook's officers, named about 74 islands across the central and western Pacific by traditional name, with bearings and approximate sailing times. Cook later verified several by independent observation. Tupaia died of dysentery at Batavia in December 1770. His chart is the strongest single piece of evidence that pre-contact Polynesian wayfinding was a working long-distance navigation technology — not the lucky drift Andrew Sharp hypothesized in 1956.",
    },
    "reason": "Resolve dup with #590 (both Hokule'a) by switching to Tupaia of Raiatea (Cook 1769).",
})

# === CRITICAL #1097: Fix 2 factually-impossible distractors ===
FIXES.append({
    "idx": 1097,
    "patch": {
        "choices": [
            "Grain requisitioning at Moscow-set quotas above harvest reality, combined with internal-passport restrictions on travel",
            "Forced relocation of all Ukrainian peasants to Siberian camps the year before the 1932 harvest could be brought in",
            "Stalin's deliberate diversion of Volga and Dnieper river irrigation away from Ukrainian wheat fields in 1932-33",
            "Mass conscription of Ukrainian peasant men into the Red Army in 1932, leaving collective-farm fields unworked",
        ],
    },
    "reason": "Fix 2 distractors that were factually impossible (cloud-seeding 1932; German invasion of Ukraine 1932).",
})

# === WEASEL CLOSERS — replace with pointed concrete ===
WEASEL_REWRITES = [
    (70, "What single ancient supercontinent does this Lystrosaurus scatter prove?"),
    (81, "What process does the symmetric magnetic striping across mid-ocean ridges prove?"),
    (138, "What kind of trigger does Anak Krakatau's 2018 collapse-tsunami expose at island volcanoes?"),
    (179, "What kind of climate did the Sahara have between ~9000 and 5000 BC?"),
    (373, "What kind of refuge saved the Lord Howe stick insect from extinction?"),
    (379, "By what mode of growth does a single Australian seagrass clone reach 100,000 years old?"),
    (628, "What kind of global public good does US-built free-to-the-world GPS exemplify?"),
    (840, "Where does the chief temple sit in the Roman colonial grid, and what does that placement say about religion?"),
    (857, "What network did England join by ruling for Rome at Whitby in 664 AD?"),
    (861, "Which two coastal networks did French Huguenot 'places of surety' cluster on?"),
    (870, "What two factors kept the Druze religion alive in Mt Lebanon, the Galilee, and Jabal al-Druze?"),
    (903, "Which two American sub-cultures did the 1925 Scopes trial set against each other in Dayton, Tennessee?"),
    (910, "What religious-ethnic identity did the 1991-2001 Yugoslav wars track most closely?"),
    (911, "What did the Belfast peace walls fuse — religious identity, political identity, or urban geography?"),
    (984, "Which four treaties built the peaceful US-Canada border west of the Great Lakes?"),
    (1053, "What Soviet institution did the Solovetsky monastery become in 1923?"),
    (1056, "What aspects of daily Roman life did Vesuvius preserve under Pompeii's ash in 79 AD?"),
]

for idx, new_closer in WEASEL_REWRITES:
    old_stem = bank[idx]["question"]
    new_stem = replace_closer(old_stem, new_closer)
    FIXES.append({
        "idx": idx,
        "patch": {"question": new_stem},
        "reason": f"Replace §15 weasel: {new_closer[:70]}...",
    })


# === PARENS-DECORATION — strip parens from answer when only-on-answer ===
PARENS_IDX = [218, 261, 270, 290, 328, 363, 487, 494, 496, 497, 608, 613, 712, 722, 725, 732, 735, 741, 751, 798, 826, 853, 855, 859, 868, 869, 870, 874, 875, 878, 880, 881, 882, 884, 885, 892, 897, 900, 902, 908, 911, 914, 921, 1026, 1049, 1071, 1076, 1080]


def strip_parens_skimtell(idx, bank):
    q = bank[idx]
    if "(" not in q["answer"]:
        return None
    n_parens = sum(1 for c in q["choices"] if "(" in c)
    if n_parens != 1:
        return None
    new_answer = re.sub(r"\s*\([^)]+\)", "", q["answer"]).strip()
    if not new_answer:
        return None
    new_choices = [new_answer if c == q["answer"] else c for c in q["choices"]]
    return {"answer": new_answer, "choices": new_choices}


for idx in PARENS_IDX:
    patch = strip_parens_skimtell(idx, bank)
    if patch:
        FIXES.append({
            "idx": idx,
            "patch": patch,
            "reason": "Strip parens-decoration skim-tell from answer.",
        })


# === APPLY ===
dup, ans = build_bank_indices(bank)
print(f"Applying {len(FIXES)} geography fixes...\n")

results = {"applied": [], "failed": []}
for fix in FIXES:
    idx = fix["idx"]
    q_new = dict(bank[idx])
    for k, v in fix["patch"].items():
        q_new[k] = v
    r = validate_rewrite("geography", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q_new
        results["applied"].append((idx, fix["reason"], r["verdict"]))
        dup, ans = build_bank_indices(bank)
    else:
        results["failed"].append((idx, [f"{g}: {reason[:200]}" for g, reason in r["hard_fails"]]))

print(f"Applied: {len(results['applied'])}")
print(f"Failed: {len(results['failed'])}")

if results["failed"]:
    print("\n=== FAILED (first 20) ===")
    for idx, reasons in results["failed"][:20]:
        print(f"  #{idx}: {reasons}")

if results["applied"]:
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {BANK_PATH}")
