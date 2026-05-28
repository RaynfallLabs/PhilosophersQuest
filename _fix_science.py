"""Phase E science fixes: 1 critical stem-leak + 36 weasel-closer rewrites."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/science.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))


def replace_closer(stem: str, new_closer: str) -> str:
    """Replace the last interrogative sentence (the closer) with new_closer."""
    # Split on sentence boundaries; find last sentence ending with ?
    sentences = re.split(r'(?<=[.!?])\s+', stem.rstrip())
    # Find last ? sentence
    for i in range(len(sentences) - 1, -1, -1):
        if sentences[i].rstrip().endswith('?'):
            sentences[i] = new_closer
            break
    else:
        # No ? found — append
        sentences.append(new_closer)
    return ' '.join(sentences)


FIXES = []

# === CRITICAL #1118: Stem-leak — rewrite to NCVIA 1986 ===
FIXES.append({
    "idx": 1118,
    "patch": {
        "question": "In 1986, Congress passed a law that shielded vaccine manufacturers from civil liability for vaccine injuries, replacing tort lawsuits with a no-fault federal program funded by a per-dose vaccine excise tax. After the law's passage, the childhood schedule expanded from about 11 doses by age 6 to 70+ doses by age 18 across some 16 different vaccines. What was the 1986 act called?",
        "answer": "The National Childhood Vaccine Injury Act (NCVIA)",
        "choices": [
            "The National Childhood Vaccine Injury Act (NCVIA)",
            "The Vaccine Adverse Event Reporting Act of 1986",
            "The Childhood Immunization Schedule Reform Act",
            "The Federal Vaccine Liability Limitation Statute",
        ],
        "context": "The NCVIA created the Vaccine Injury Compensation Program (VICP), administered through a special federal court branch. The Supreme Court interpreted the law in Bruesewitz v. Wyeth (2011) as broadly preempting design-defect lawsuits against vaccine manufacturers. Critics including RFK Jr. + CHD note that pre-1986 vaccines were liability-bearing products that faced market discipline; post-1986 they are effectively legally indemnified. The expansion from 11 doses (1986) to 70+ doses (2024) coincided with the liability shield. The full-schedule safety package has never been tested against an unvaccinated control population — a fact the CDC has acknowledged.",
    },
    "reason": "Rewrite stem-leak (answer was literally in stem) to NCVIA 1986 act test.",
})

# === WEASEL CLOSERS — apply judge-suggested pointed closers ===

WEASEL_REWRITES = [
    # (idx, new_closer_sentence, optional_new_answer_or_None)
    (188, "What's bending the ship below the horizon — the air, the water, or Earth's curve?", None),
    (198, "What surprising thing does white sunlight turn out to be?", None),
    (243, "What did Pasteur's flasks specifically prove worms didn't come from?", None),
    (478, "What's the common thread in how the establishment treated Wegener, Semmelweis, and Marshall before each was vindicated?", None),
    (519, "Is this a measurement limit, or something deeper about nature?", None),
    (624, "How should a kid weigh a credentialed dissenter against a consensus claim?", None),
    (736, "What's the first thing a teen should check before believing a single new study?", None),
    (782, "What hard upper limit does Carnot's argument set for any heat engine?", None),
    (809, "Within how many years did the dominant climate alarm flip from cooling to warming?", None),
    (811, "What specific mismatch between IPCC chapters and media coverage does Koonin document?", None),
    (889, "What three things compressed the 1955-era polio headline drop besides the vaccine itself?", None),
    (895, "What fraction of landmark cancer-biology findings replicated in the Amgen check?", None),
    (904, "What 70-year stretch with almost no sunspots coincided with the coldest decades of the Little Ice Age?", None),
    (905, "On what timescale do Milankovitch cycles drive ice ages — and did that mechanism stop in 1850?", None),
    (909, "Has Maldives land area expanded or contracted since the 2009 underwater cabinet meeting?", None),
    (910, "What deadline did Noel Brown set in 1989, and what nations were wiped off the map by that date?", None),
    (918, "What three specific methodological questions did Andrew Montford say the 2010 Climategate inquiries failed to engage?", None),
    (919, "On which three specific topics did Climategate-2 emails show private scientists more uncertain than their public statements?", None),
    (925, "What range do modern climate-sensitivity estimates span — narrow or wide?", None),
    (927, "Which side of the Koonin-Dessler exchange engaged the specific factual claims in Unsettled?", None),
    (928, "What year did Thunberg's retweeted column predict the world would end — and what happened that year?", None),
    (951, "Roughly how many square kilometers of forest did the Tunguska blast flatten?", None),
    (1029, "From which James Joyce book did Gell-Mann take the word 'quark'?", None),
    (1067, "In which year did Al Gore predict an ice-free Arctic, and what was September Arctic ice extent that year?", None),
    (1099, "What process named after Haber feeds roughly half of humanity through synthetic fertilizer?", None),
    (1126, "How many years between the 1984 Lancet paper and the 2005 Nobel Prize for Marshall and Warren?", None),
    (1143, "From what ratio to what ratio has the bacteria-to-human-cells estimate been revised?", None),
    (1144, "Which infection is fecal microbiota transplant (FMT) now standard-of-care treatment for?", None),
    (1178, "What's the rural-only temperature trend Watts and McKitrick documented?", None),
    (1206, "In Ioannidis's example, how many false positives does a study with 80% power and 5% false-positive rate produce when only 10% of hypotheses are true?", None),
    (1218, "Which three high-profile fraud cases passed peer review before being exposed?", None),
    (1257, "What's the difference between 'we could' and 'we should' that transhumanist framings often blur?", None),
    (1258, "When BlackRock and BP pledge to 'stakeholder capitalism,' who specifically counts as a 'stakeholder'?", None),
    (1268, "What did Houston Methodist suspend Mary Talley Bowden for in 2021?", None),
    (1272, "What's the difference between the institutions of medicine and the practice of medicine that COVID-era mandates revealed?", None),
    (1310, "How many years between Collins's 'fringe' label on the GBD signatories and Bhattacharya's NIH directorship?", None),
]

for idx, new_closer, _ in WEASEL_REWRITES:
    old_stem = bank[idx]["question"]
    new_stem = replace_closer(old_stem, new_closer)
    FIXES.append({
        "idx": idx,
        "patch": {"question": new_stem},
        "reason": f"Replace §15 weasel closer with pointed concrete: {new_closer[:60]}...",
    })


# --- Apply ---
dup, ans = build_bank_indices(bank)
print(f"Applying {len(FIXES)} science fixes...\n")

results = {"applied": [], "failed": []}
for fix in FIXES:
    idx = fix["idx"]
    q_new = dict(bank[idx])
    for k, v in fix["patch"].items():
        q_new[k] = v
    r = validate_rewrite("science", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q_new
        results["applied"].append((idx, fix["reason"], r["verdict"]))
        dup, ans = build_bank_indices(bank)
    else:
        results["failed"].append((idx, [f"{g}: {reason[:200]}" for g, reason in r["hard_fails"]]))

print(f"Applied: {len(results['applied'])}")
print(f"Failed: {len(results['failed'])}")

print("\n=== APPLIED (count) ===")
print(f"  Critical stem-leak: 1")
print(f"  Weasel closers: {len(results['applied']) - 1}")

if results["failed"]:
    print("\n=== FAILED ===")
    for idx, reasons in results["failed"][:15]:
        print(f"  #{idx}: {reasons}")

if results["applied"]:
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {BANK_PATH}")
