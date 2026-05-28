"""Phase E philosophy fixes: 5 critical T5 parity + name-as-framing + wonder-bias + stance."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/philosophy.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))

FIXES = []

# === CRITICAL: 5 T5 aesthetics parity fixes — extend correct answer to balance ===

# #84: original answer was 188 chars; targets ~220
FIXES.append({
    "idx": 84,
    "patch": {
        "answer": "Cluster theory — Gaut holds art has no single defining feature; an object counts as art when it exhibits enough of a cluster of typical art-properties, with no individual property either necessary or sufficient.",
        "choices": [
            "Cluster theory — Gaut holds art has no single defining feature; an object counts as art when it exhibits enough of a cluster of typical art-properties, with no individual property either necessary or sufficient.",
            "Institutional theory — Dickie holds art is what the artworld confers status upon; candidacy for appreciation is conferred through institutional roles rather than any intrinsic property.",
            "Intentionalism — Wollheim and Levinson make the maker's intention partly constitutive; on this view intention is necessary, whereas the cluster theory requires no specific feature at all.",
            "Aesthetic functionalism — Beardsley and the early Gaut hold art is defined by the capacity to afford aesthetic experience; the function unifies what counts and excludes what does not.",
        ],
    },
    "reason": "Balance #84 T5 length-parity by extending the correct answer.",
})

FIXES.append({
    "idx": 85,
    "patch": {
        "answer": "Historical-functional theory — Levinson defines art recursively: a thing is art if intended to be regarded in ways previous artworks were regarded, anchoring novelty to a tradition of regard-relations rather than to any timeless property.",
        "choices": [
            "Historical-functional theory — Levinson defines art recursively: a thing is art if intended to be regarded in ways previous artworks were regarded, anchoring novelty to a tradition of regard-relations rather than to any timeless property.",
            "Institutional theory — Dickie holds art is what the artworld confers status upon; the historical view replaces institutional conferral with a chain of regard-relations stretching across time.",
            "Intentionalism — Wollheim's broader intentionalism makes intention partly constitutive, but does not require the backward-looking historical chain that Levinson's recursive definition imposes.",
            "Aesthetic empiricism — Beardsley holds the work's perceptible features constitute its aesthetic object; both historical tradition and maker's intention are external to what makes it art.",
        ],
    },
    "reason": "Balance #85 T5 length-parity.",
})

FIXES.append({
    "idx": 86,
    "patch": {
        "answer": "Humean response-dependent standard — Hume grounds objectivity in the converging verdicts of qualified judges (delicate, practiced, unprejudiced), not in a property of the object alone but not in mere individual feeling either.",
        "choices": [
            "Humean response-dependent standard — Hume grounds objectivity in the converging verdicts of qualified judges (delicate, practiced, unprejudiced), not in a property of the object alone but not in mere individual feeling either.",
            "Aesthetic realism — beauty is a real property of the object, independent of any response; trained judges approximate the truth about it but do not constitute that truth by their convergence.",
            "Pure subjectivism — beauty is whatever pleases the individual; no judges are more qualified than any others, and the convergence of trained judges has no special epistemic status of any kind.",
            "Kantian disinterested pleasure — beauty is what is judged with universal validity in disinterested pleasure; the standard lies in the structure of the judgment itself rather than convergence.",
        ],
    },
    "reason": "Balance #86 T5 length-parity.",
})

FIXES.append({
    "idx": 93,
    "patch": {
        "answer": "Anti-cognitivism / autonomism — Lamarque and Olsen hold art's aesthetic value is autonomous from cognitive yield; any incidental truth-content is not part of what makes the work art and is irrelevant to its standing as art.",
        "choices": [
            "Anti-cognitivism / autonomism — Lamarque and Olsen hold art's aesthetic value is autonomous from cognitive yield; any incidental truth-content is not part of what makes the work art and is irrelevant to its standing as art.",
            "Cognitivism — Carroll and Currie hold art is a genuine source of knowledge and the cognitive yield is partly constitutive of artistic value; an artwork's truths are essential to what makes it art.",
            "Aesthetic empiricism — Beardsley holds only the work's perceptible features constitute its aesthetic object; though this overlaps the conclusion, it gets there through a different route entirely.",
            "Formalism — Bell holds significant form is the property that makes a work art and aesthetically valuable; the formalist agrees content is irrelevant but stakes everything on the form alone.",
        ],
    },
    "reason": "Balance #93 T5 length-parity.",
})

FIXES.append({
    "idx": 98,
    "patch": {
        "answer": "Conceptualism — LeWitt holds the idea or concept is the most important aspect of an artwork; perceptual features are mere documentation, and the audience's engagement is with the conceptual proposition the artist puts forward.",
        "choices": [
            "Conceptualism — LeWitt holds the idea or concept is the most important aspect of an artwork; perceptual features are mere documentation, and the audience's engagement is with the conceptual proposition the artist puts forward.",
            "Aesthetic empiricism — Beardsley holds the work's perceptible features alone constitute its aesthetic object; a certificate has whatever perceptual properties it has, and no conceptual layer counts.",
            "Formalism — Bell holds significant form is the property in virtue of which art is valuable; the formalist must deny the certificate is art at all because it lacks any significant form to speak of.",
            "Intentionalism — Wollheim and Levinson make the maker's intention partly constitutive; intention is needed but not every intentional act is art-making, so the certificate may or may not qualify.",
        ],
    },
    "reason": "Balance #98 T5 length-parity.",
})


# === LENGTH-CAP VIOLATIONS ===
# #92 answer 240 over 230
q92 = bank[92]
new_ans_92 = q92["answer"]
if len(new_ans_92) > 230:
    # Trim trailing clause
    new_ans_92 = new_ans_92[:225].rsplit(' ', 1)[0] + '.'
FIXES.append({
    "idx": 92,
    "patch": {"answer": new_ans_92, "choices": [new_ans_92 if c == q92["answer"] else c for c in q92["choices"]]},
    "reason": "Trim #92 answer to under T5 cap.",
})

# #620 answer 196 over 190
q620 = bank[620]
new_ans_620 = q620["answer"]
if len(new_ans_620) > 190:
    new_ans_620 = new_ans_620[:185].rsplit(' ', 1)[0] + '.'
FIXES.append({
    "idx": 620,
    "patch": {"answer": new_ans_620, "choices": [new_ans_620 if c == q620["answer"] else c for c in q620["choices"]]},
    "reason": "Trim #620 answer to under T4 cap.",
})


# === NAME-AS-FRAMING (move name from stem to context) ===

NAME_FRAMING_FIXES = {
    279: ("Peter Singer", "A philosopher"),
    280: ("Sommers", "A virtue ethicist"),
    304: ("Alasdair MacIntyre", "A virtue ethicist"),
    305: ("Joan Tronto", "A care theorist"),
    485: ("Parfit", "A philosopher"),
    526: ("A philosophy class reads Parfit. One student summarizes his view:", "A philosophy class summarizes a key view in personal identity:"),
    552: ("Nozick's experience machine", "An experience machine"),
    612: ("John Searle's 'Chinese Room'", "The 'Chinese Room' thought experiment"),
    613: ("John Locke's 'inverted spectrum'", "The 'inverted spectrum' thought experiment"),
    627: ("A philosophy class discusses Hilary Putnam.", "A philosophy class discusses a view about mental states."),
}

for idx, (old_text, new_text) in NAME_FRAMING_FIXES.items():
    q = bank[idx]
    new_q = q["question"].replace(old_text, new_text)
    if new_q != q["question"]:
        FIXES.append({
            "idx": idx,
            "patch": {"question": new_q},
            "reason": f"Move name '{old_text[:30]}' from framing to neutral.",
        })


# === STANCE FIXES (3 critical) ===

# #410 vaccine-COI fallacy — reframe
q410 = bank[410]
new_q_410 = q410["question"].replace(
    "vaccine schedule",
    "drug-trial safety claim"
).replace(
    "vaccines",
    "drug-trial safety claim"
)
if new_q_410 != q410["question"]:
    FIXES.append({
        "idx": 410,
        "patch": {"question": new_q_410},
        "reason": "Re-frame stance: vaccine-COI example replaced with neutral drug-trial framing.",
    })

# #443 MMT framing — replace with currency-issuer-neutral phrasing
q443 = bank[443]
new_q_443 = q443["question"].replace(
    "sovereign currency-issuing entities",
    "national monetary authorities"
)
if new_q_443 != q443["question"]:
    FIXES.append({
        "idx": 443,
        "patch": {"question": new_q_443},
        "reason": "Re-frame stance: MMT-tinged language replaced with neutral phrasing.",
    })


# === WONDER-BIAS scenery substitutions (script-based) ===

SCENE_SUBSTITUTIONS = [
    # (pattern, replacement) — order matters; longer specific first
    (r"\ba YouTuber\b", "a wandering minstrel"),
    (r"\bYouTubers?\b", "court poets"),
    (r"\ba TikToker?\b", "a town crier"),
    (r"\bTikTok\b", "the broadsheets"),
    (r"\bgroup chat\b", "guild meeting"),
    (r"\ba podcaster\b", "a salon orator"),
    (r"\b(?:a |the )?podcast\b", "a symposium"),
    (r"\bschool newspaper\b", "monastery chronicle"),
    (r"\barts podcast\b", "salon debate"),
    (r"\bvideo essay\b", "scholastic disputation"),
    (r"\bsocial media\b", "the public square"),
    (r"\bTwitter\b", "the printed pamphlet"),
    (r"\binfluencer\b", "court favorite"),
    (r"\bonline forum\b", "scholar's hall"),
    (r"\bblogger\b", "pamphleteer"),
    (r"\bblog\b", "pamphlet"),
    (r"\bsubreddit\b", "guild meeting"),
    (r"\bReddit\b", "the merchants' coffeehouse"),
    (r"\bInstagram\b", "the portrait gallery"),
    (r"\bSpotify\b", "the concert hall"),
    (r"\bcat with a laser\b", "knight with a falcon"),
    (r"\ba cat-with-laser", "a knight-with-falcon"),
]


WONDER_BIAS_IDX = [
    20, 40, 43, 48, 50, 53, 56, 60, 65, 77, 128, 142, 145, 151,
    155, 159, 163, 165, 170, 175, 184, 187, 192, 200, 205, 210, 215,
    220, 225, 235, 240, 245, 250, 255, 260, 265, 270, 275, 285, 290,
    295, 308, 315, 320, 325, 330, 335, 340, 345, 350, 355, 360, 365,
    368, 380, 390, 395, 400, 415, 420, 430, 440, 450, 460, 470,
    480, 490, 495, 500, 510, 520, 530, 540, 560, 580, 590, 592, 593, 595, 600, 606, 610,
]


def apply_scenery_substitutions(text: str) -> str:
    new = text
    for pat, rep in SCENE_SUBSTITUTIONS:
        new = re.sub(pat, rep, new, flags=re.IGNORECASE)
    return new


# Actually use the audit's flagged indices — only ones flagged for wonder-bias
data = json.loads(Path("_audit_phase_b_philosophy.json").read_text(encoding="utf-8"))
wonder_actual_idx = []
for f in data.get("flags", []):
    if "A" in f.get("dimensions", []) and f.get("severity") in ("WARN", "MINOR"):
        wonder_actual_idx.append(f["idx"])

for idx in wonder_actual_idx:
    q = bank[idx]
    new_question = apply_scenery_substitutions(q["question"])
    new_choices = [apply_scenery_substitutions(c) for c in q["choices"]]
    new_answer = apply_scenery_substitutions(q["answer"])
    if new_question != q["question"] or new_choices != q["choices"]:
        FIXES.append({
            "idx": idx,
            "patch": {"question": new_question, "choices": new_choices, "answer": new_answer},
            "reason": "Wonder-bias scenery substitution (modern→canonical setting).",
        })


# === APPLY ===
dup, ans = build_bank_indices(bank)
print(f"Applying {len(FIXES)} philosophy fixes...\n")

# Dedup by idx (later wins)
seen = {}
for fix in FIXES:
    seen[fix["idx"]] = fix
FIXES = list(seen.values())
print(f"Deduped to {len(FIXES)} unique-idx fixes.")

results = {"applied": [], "failed": []}
for fix in FIXES:
    idx = fix["idx"]
    q_new = dict(bank[idx])
    for k, v in fix["patch"].items():
        q_new[k] = v
    r = validate_rewrite("philosophy", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q_new
        results["applied"].append((idx, fix["reason"], r["verdict"]))
        dup, ans = build_bank_indices(bank)
    else:
        results["failed"].append((idx, [f"{g}: {reason[:200]}" for g, reason in r["hard_fails"]]))

print(f"Applied: {len(results['applied'])}")
print(f"Failed: {len(results['failed'])}")

if results["failed"]:
    print("\n=== FAILED (first 15) ===")
    for idx, reasons in results["failed"][:15]:
        print(f"  #{idx}: {reasons}")

if results["applied"]:
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {BANK_PATH}")
