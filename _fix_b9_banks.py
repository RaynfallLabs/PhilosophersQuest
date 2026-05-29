"""Bug-bash B9: trivia stem-leaks + history generic-labels + AI/econ weasel closers.

17 substantive rewrites across 3 banks. Each one's answer becomes a
named-thing (per the Wonder/Easter-Egg Pattern); each weasel closer
becomes a pointed concrete question.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite


def replace_closer(stem: str, new_closer: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', stem.rstrip())
    for i in range(len(sentences) - 1, -1, -1):
        if sentences[i].rstrip().endswith('?'):
            sentences[i] = new_closer
            break
    return ' '.join(sentences)


# === TRIVIA FIXES ===
TRIVIA = Path("data/questions/trivia.json")
trivia = json.loads(TRIVIA.read_text(encoding="utf-8"))

TRIVIA_FIXES = [
    # #168 Urusei Yatsura: stem lists 3 titles incl. the answer
    (168, {
        "question": (
            "Rumiko Takahashi is one of the most successful mangaka in history. "
            "Her first major hit, serialized 1978-1987 and adapted into a "
            "long-running anime, starred an alien princess in a tiger-stripe "
            "bikini who electrocutes her loser-fiancé Ataru every time he "
            "cheats. What's the series called?"
        ),
        "answer": "Urusei Yatsura",
        "choices": ["Urusei Yatsura", "Maison Ikkoku", "Ranma 1/2", "Inuyasha"],
    }),
    # #274 Fullmetal Alchemist nickname: stem says "Fullmetal Alchemist"
    (274, {
        "question": (
            "In Hiromu Arakawa's manga, two brothers attempt forbidden human "
            "transmutation to bring their dead mother back. It costs the "
            "older brother his right arm and left leg; the younger loses his "
            "entire body, his soul bound to a suit of armor. The State gives "
            "the older brother a silver pocket watch and a nickname for his "
            "metal limbs. What's his nickname?"
        ),
        "answer": "The Fullmetal Alchemist",
        "choices": [
            "The Fullmetal Alchemist",
            "The Flame Alchemist",
            "The Strong-Arm Alchemist",
            "The Crimson Alchemist",
        ],
    }),
    # #300 One Piece treasure: stem says "One Piece"
    (300, {
        "question": (
            "Eiichiro Oda's pirate manga began serialization in Weekly Shonen "
            "Jump in July 1997. It became the bestselling manga in history. "
            "The story follows Monkey D. Luffy hunting the legendary treasure "
            "Gol D. Roger left at the end of the Grand Line. What is this "
            "treasure called?"
        ),
        "answer": "The One Piece",
        "choices": ["The One Piece", "The Grand Treasure", "The Pirate's Bounty", "The Devil's Hoard"],
    }),
    # #608 Mumm-Ra: stem leaks "Mumm-Ra the Ever-Living"
    (608, {
        "question": (
            "In the 1985 Thundercats cartoon, the villain dwells in a black "
            "pyramid on Third Earth. Most of the time he's a shrivelled mummy. "
            "When he calls on the Ancient Spirits of Evil, he transforms into "
            "a hulking blue-skinned demigod with the catchphrase 'Ancient "
            "Spirits of Evil, transform this decayed form into…' WHAT?"
        ),
        "answer": "Mumm-Ra the Ever-Living",
        "choices": [
            "Mumm-Ra the Ever-Living",
            "Mumm-Ra the Immortal",
            "Mumm-Ra the Dark Lord",
            "Mumm-Ra the Vile",
        ],
    }),
    # #686 Donkey Kong: stem names the ape
    (686, {
        "question": (
            "In Nintendo's 1981 arcade hit, a giant ape kidnaps a girlfriend "
            "and climbs to the top of a construction site, hurling barrels at "
            "the carpenter who tries to rescue her. The carpenter is named "
            "Jumpman. What's the famous name of the carpenter today?"
        ),
        "answer": "Mario",
        "choices": ["Mario", "Luigi", "Stanley", "Pauline"],
    }),
]

dup_t, ans_t = build_bank_indices(trivia)
trivia_applied = 0
for idx, patch in TRIVIA_FIXES:
    q = dict(trivia[idx])
    for k, v in patch.items():
        q[k] = v
    r = validate_rewrite("trivia", q, bank=trivia, dup_index=dup_t, answer_index=ans_t, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        trivia[idx] = q
        trivia_applied += 1
        dup_t, ans_t = build_bank_indices(trivia)
        print(f"  trivia #{idx}: PASS")
    else:
        print(f"  trivia #{idx}: FAIL")
        for g, reason in r["hard_fails"][:2]: print(f"    {g}: {reason[:130]}")


# === HISTORY FIXES (generic-label rewrites) ===
HISTORY = Path("data/questions/history.json")
history = json.loads(HISTORY.read_text(encoding="utf-8"))

HISTORY_FIXES = [
    # #101 Sobieski winged hussars
    (101, {
        "question": (
            "On September 12, 1683, Polish king Jan III Sobieski charged "
            "down from the Kahlenberg heights with his cavalry — the largest "
            "such charge in history — to save Vienna from the Ottoman siege. "
            "His horsemen were instantly recognizable by huge feathered "
            "wing-frames mounted on their back armor that hissed in the wind. "
            "What were they called?"
        ),
        "answer": "The Winged Hussars",
        "choices": [
            "The Winged Hussars",
            "The Towarzysz Knights",
            "The Polish Lancers",
            "The Kraków Cataphracts",
        ],
    }),
    # #198 Origin of Species - 1,250 copies / John Murray
    (198, {
        "question": (
            "On November 24, 1859, Charles Darwin's On the Origin of Species "
            "was published by John Murray in London. The first printing met "
            "a striking fate the very same day: every copy was bought by "
            "booksellers before the public could see one. What was the size "
            "of that first printing?"
        ),
        "answer": "1,250 copies",
        "choices": ["1,250 copies", "500 copies", "3,000 copies", "10,000 copies"],
    }),
    # #737 Kursk -> Prokhorovka
    (737, {
        "question": (
            "Between July 5 and August 23, 1943, around the Russian railway "
            "town of Kursk, German Tigers and Panthers met massed Soviet T-34s "
            "in the largest tank battle in history. The decisive single-day "
            "clash on July 12 happened at a small village whose name became "
            "shorthand for the engagement. What's the village called?"
        ),
        "answer": "Prokhorovka",
        "choices": ["Prokhorovka", "Oboyan", "Belgorod", "Ponyri"],
    }),
    # #829 Guernica - the painting's name IS the cool fact
    (829, {
        "question": (
            "On April 26, 1937, during the Spanish Civil War, the German "
            "Luftwaffe's Condor Legion bombed a small Basque town to test "
            "saturation-bombing tactics. Pablo Picasso, then living in Paris, "
            "spent the next month painting an enormous black-white-grey "
            "canvas of screaming horses, broken swords, and dismembered "
            "figures. What did he title the painting?"
        ),
        "answer": "Guernica",
        "choices": ["Guernica", "April 1937", "The Bombing", "Black Light"],
    }),
    # #32 Thermopylae -> Hot Gates / Dienekes line
    (32, {
        "question": (
            "In 480 BC the Persian king Xerxes invaded Greece with a vast army. "
            "King Leonidas of Sparta met him at a narrow mountain pass with "
            "300 Spartans. Told the Persian arrows would blot out the sun, the "
            "Spartan Dienekes replied: 'So much the better — we shall fight "
            "in the shade.' What was the pass called?"
        ),
        "answer": "Thermopylae",
        "choices": ["Thermopylae", "Salamis", "Marathon", "Platea"],
    }),
    # #98 Antietam Special Order 191
    (98, {
        "question": (
            "On the eve of Antietam in September 1862, Union soldiers found "
            "a piece of paper wrapped around three cigars in a Maryland "
            "field. The paper was Robert E. Lee's complete battle plan, "
            "accidentally dropped by a Confederate officer. By the document's "
            "official designation, what was it?"
        ),
        "answer": "Special Order 191",
        "choices": [
            "Special Order 191",
            "General Order 86",
            "Field Dispatch 22",
            "Marching Plan 14",
        ],
    }),
]

dup_h, ans_h = build_bank_indices(history)
history_applied = 0
for idx, patch in HISTORY_FIXES:
    q = dict(history[idx])
    for k, v in patch.items():
        q[k] = v
    r = validate_rewrite("history", q, bank=history, dup_index=dup_h, answer_index=ans_h, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        history[idx] = q
        history_applied += 1
        dup_h, ans_h = build_bank_indices(history)
        print(f"  history #{idx}: PASS")
    else:
        print(f"  history #{idx}: FAIL")
        for g, reason in r["hard_fails"][:2]: print(f"    {g}: {reason[:130]}")


# === AI WEASEL CLOSERS ===
AI = Path("data/questions/ai.json")
ai = json.loads(AI.read_text(encoding="utf-8"))
AI_CLOSERS = [
    (146, "What single check should you make before sending any money?"),
    (372, "What single check should you run on the chatbot's claim?"),
    (415, "What single category of personal data does psychographic targeting build on?"),
    (602, "What single thing does collaborative filtering compare across users?"),
]
dup_a, ans_a = build_bank_indices(ai)
ai_applied = 0
for idx, new_closer in AI_CLOSERS:
    q = dict(ai[idx])
    q["question"] = replace_closer(q["question"], new_closer)
    r = validate_rewrite("ai", q, bank=ai, dup_index=dup_a, answer_index=ans_a, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        ai[idx] = q
        ai_applied += 1
        dup_a, ans_a = build_bank_indices(ai)
        print(f"  ai #{idx}: PASS  ({new_closer[:50]}...)")
    else:
        print(f"  ai #{idx}: FAIL")
        for g, reason in r["hard_fails"][:2]: print(f"    {g}: {reason[:130]}")


# === ECONOMICS WEASEL CLOSERS ===
ECON = Path("data/questions/economics.json")
econ = json.loads(ECON.read_text(encoding="utf-8"))
ECON_CLOSERS = [
    (100, "What single thing does the puzzle prove about the block's miner?"),
    (430, "Whose prediction was wrong by how much in the June 2022 print?"),
]
dup_e, ans_e = build_bank_indices(econ)
econ_applied = 0
for idx, new_closer in ECON_CLOSERS:
    q = dict(econ[idx])
    q["question"] = replace_closer(q["question"], new_closer)
    r = validate_rewrite("economics", q, bank=econ, dup_index=dup_e, answer_index=ans_e, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        econ[idx] = q
        econ_applied += 1
        dup_e, ans_e = build_bank_indices(econ)
        print(f"  econ #{idx}: PASS  ({new_closer[:50]}...)")
    else:
        print(f"  econ #{idx}: FAIL")
        for g, reason in r["hard_fails"][:2]: print(f"    {g}: {reason[:130]}")


# Save banks
if trivia_applied:
    TRIVIA.write_text(json.dumps(trivia, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
if history_applied:
    HISTORY.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
if ai_applied:
    AI.write_text(json.dumps(ai, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
if econ_applied:
    ECON.write_text(json.dumps(econ, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

total = trivia_applied + history_applied + ai_applied + econ_applied
print(f"\n=== Applied: trivia={trivia_applied}/5 history={history_applied}/6 ai={ai_applied}/4 econ={econ_applied}/2 (total {total}/17) ===")
