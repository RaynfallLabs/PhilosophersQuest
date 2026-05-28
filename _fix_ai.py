"""Phase E AI fixes: 20 T1 joke distractors + 49 weasel closers + Sora correction."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/ai.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))


def replace_closer(stem: str, new_closer: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', stem.rstrip())
    for i in range(len(sentences) - 1, -1, -1):
        if sentences[i].rstrip().endswith('?'):
            sentences[i] = new_closer
            break
    return ' '.join(sentences)


FIXES = []

# === T1 JOKE-DISTRACTOR REPLACEMENTS — replace cartoon distractors with realistic plausibles ===

JOKE_FIXES = {
    2: {"choices": [
        "Neural network architecture",
        "Robot from a movie series",
        "A type of electrical device",
        "A famous brand of laptop",
    ]},
    50: {"choices": [
        "The Turing test",
        "The Wittgenstein test",
        "The Hilbert test",
        "The von Neumann test",
    ]},
    54: {"choices": [
        "Proteins",
        "Lipids",
        "Carbohydrates",
        "Nucleic acids",
    ]},
    58: {"choices": [
        "Google",
        "Meta",
        "Microsoft",
        "Amazon",
    ]},
    59: {"choices": [
        "Deep neural networks",
        "Symbolic expert systems",
        "Decision-tree learning",
        "Statistical machine translation",
    ]},
    64: {"choices": [
        "Dario Amodei",
        "Sam Altman",
        "Demis Hassabis",
        "Mustafa Suleyman",
    ]},
    70: {"choices": [
        "ELIZA",
        "PARRY",
        "SHRDLU",
        "BORIS",
    ]},
    72: {"choices": [
        "Watson",
        "Deep Blue",
        "BlueGene",
        "Project Debater",
    ]},
    75: {"choices": [
        "Llama",
        "Falcon",
        "Mistral",
        "BLOOM",
    ]},
    76: {
        "answer": "East Asia, where Go has the most players",
        "choices": [
            "East Asia, where Go has the most players",
            "Western Europe, where chess unions are largest",
            "South America, where checkers tournaments are big",
            "Northern Africa, where shogi is mainstream",
        ],
    },
    79: {"choices": [
        "Microsoft (its largest investor)",
        "Sequoia Capital (an early investor)",
        "SoftBank (a strategic investor)",
        "Andreessen Horowitz (an investor)",
    ]},
    80: {"choices": [
        "London",
        "Toronto",
        "Zurich",
        "Tel Aviv",
    ]},
    82: {"choices": [
        "University of Toronto",
        "McGill University",
        "University of British Columbia",
        "University of Waterloo",
    ]},
    83: {"choices": [
        "A neural network",
        "A rule-based grammar system",
        "A statistical phrase-table",
        "A bilingual dictionary lookup",
    ]},
    84: {"choices": [
        "Neural networks",
        "Larger statistical phrase tables",
        "Faster CPU dictionaries",
        "Crowd-sourced human edits",
    ]},
    85: {"choices": [
        "Itself, millions of times",
        "Older Go programs from the 1990s",
        "Top professional Go players",
        "Random move generators",
    ]},
    89: {"choices": [
        "Waymo",
        "Cruise",
        "Aurora",
        "Mobileye",
    ]},
    103: {"choices": [
        "Siri",
        "Bixby",
        "Cortana",
        "Sundar",
    ]},
    104: {"choices": [
        "Alexa",
        "Echo",
        "Aria",
        "Astra",
    ]},
    1213: {"choices": [
        "Take actions like browsing the web or sending email",
        "Speak in more languages than any chatbot can",
        "Run entirely on a phone with no internet access",
        "Generate audio replies instead of text replies",
    ]},
}

for idx, patch in JOKE_FIXES.items():
    full_patch = dict(patch)
    if "answer" not in full_patch:
        full_patch["answer"] = full_patch["choices"][0]
    FIXES.append({
        "idx": idx,
        "patch": full_patch,
        "reason": "Replace cartoon-joke distractors with realistic plausibles (T1 anti-pattern).",
    })


# === #105 SORA category error: replace Sora with an image-only model ===
# Original lists Sora among image AIs but Sora is video. Replace Sora reference.
q105 = bank[105]
new_q = q105["question"].replace("Sora", "Stable Diffusion")
new_ctx = q105.get("context", "").replace("Sora (OpenAI, video)", "Stable Diffusion (Stability AI, image)")
new_ctx = new_ctx.replace("Sora", "Stable Diffusion")
new_choices = [c.replace("Sora", "Stable Diffusion") for c in q105["choices"]]
new_ans = q105["answer"].replace("Sora", "Stable Diffusion")
FIXES.append({
    "idx": 105,
    "patch": {
        "question": new_q,
        "choices": new_choices,
        "answer": new_ans,
        "context": new_ctx,
    },
    "reason": "Fix category error: Sora is video, not image — replace with Stable Diffusion.",
})


# === #786 META-REFERENCE: 'the AI bank' → reword to neutral ===
q786 = bank[786]
new_q = q786["question"].replace("the AI bank insists on", "the distinction critics emphasize between")
new_q = new_q.replace("the AI bank", "this distinction")
FIXES.append({
    "idx": 786,
    "patch": {"question": new_q},
    "reason": "Remove self-reference 'the AI bank' from stem.",
})


# === WEASEL CLOSERS (49) ===
WEASEL_REWRITES = [
    (37, "What single feature of a chatbot does this fingerprint expose?"),
    (45, "What's the next concrete check this kid should run?"),
    (343, "What single feature of the bot's output betrays it?"),
    (587, "What concrete check does this teach the user to make next?"),
    (588, "What single thing changes about the doctor's leverage in the appointment?"),
    (589, "What single agricultural practice does this case mark as no-longer-optional?"),
    (594, "What's the single check this case teaches a student to do?"),
    (604, "What's the single concrete habit this teaches a buyer to adopt?"),
    (606, "What's the single specific thing the lawsuits do not actually fix?"),
    (642, "What single thing should the student do with the AI's first answer?"),
    (659, "What single concrete fact about server-side storage does this teach?"),
    (666, "What's the single rule about school accounts and chat content?"),
    (687, "What's the single specific risk a kid should weigh before using one?"),
    (696, "What's the single corporate-incentive pattern this case shows?"),
    (731, "What single new question about copyright do the lawsuits raise?"),
    (781, "What single fact about long-horizon AI predictions does the record support?"),
    (797, "What single thing changes for the dominant labs when open-weight rivals exist?"),
    (860, "What single check kills most overhyped AI-discovery papers?"),
    (889, "What single failure mode of LLMs does this episode expose?"),
    (891, "What single licensing-board response to AI use does this case set?"),
    (898, "What single fact about the AI advice makes a human professional necessary?"),
    (914, "What single defensive habit does this episode recommend?"),
    (929, "What single feature of biometric data sets it apart from passwords?"),
    (934, "What single thing do these tools all collect that the user can't see?"),
    (937, "What single design feature of these systems is worth naming?"),
    (940, "What single classroom skill is at risk beyond the grade itself?"),
    (941, "What single second-order effect on user behavior does mis-moderation cause?"),
    (947, "What single recurring data risk persists even when nothing goes wrong?"),
    (948, "What single rule about sensitive content and AI servers does this teach?"),
    (956, "What single neighborhood-scale data flow do home AI devices create?"),
    (970, "What single concentration-of-power risk does this consolidation show?"),
    (995, "What single feature of psychographic ads is worth recognizing?"),
    (1003, "What single design choice in engagement-AI is named here?"),
    (1004, "What single specific harm do the lawsuits name beyond mood?"),
    (1013, "What single classroom skill atrophies when students lean on AI?"),
    (1021, "What single hidden cost of 'free' AI services is named?"),
    (1027, "What single thing is missing from most 'open' AI offerings?"),
    (1031, "What single open-source-AI failure mode does this expose?"),
    (1038, "What single thing about who shapes answers changes in this shift?"),
    (1041, "What single rhetorical use of the term 'AGI' does this expose?"),
    (1060, "What single hard barrier do these proposals all run into?"),
    (1089, "What single problem with such a public commitment is named here?"),
    (1140, "What single design pattern protects the user in this case?"),
    (1143, "What single regulatory-capture signal does an incumbent-backed rule show?"),
    (1147, "What single condition has to hold before antitrust moves against an incumbent?"),
    (1148, "What single global effect on the open-AI ecosystem does this regulation have?"),
    (1152, "What single dependency does election-integrity moderation create?"),
    (1161, "What single local-political pattern of surveillance pushback does this show?"),
    (1179, "What single product-design effect does this constraint produce?"),
]

for idx, new_closer in WEASEL_REWRITES:
    old_stem = bank[idx]["question"]
    new_stem = replace_closer(old_stem, new_closer)
    FIXES.append({
        "idx": idx,
        "patch": {"question": new_stem},
        "reason": f"Replace §15 weasel: {new_closer[:60]}...",
    })


# === APPLY ===
dup, ans = build_bank_indices(bank)
print(f"Applying {len(FIXES)} AI fixes...\n")

results = {"applied": [], "failed": []}
for fix in FIXES:
    idx = fix["idx"]
    q_new = dict(bank[idx])
    for k, v in fix["patch"].items():
        q_new[k] = v
    r = validate_rewrite("ai", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
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
