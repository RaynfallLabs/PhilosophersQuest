"""Fix 8 trivia questions with generic-label answers — version 2 with
budget-aware stems and a Roanoke pivot to Virginia Dare (CROATOAN
collides with existing #1143).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite

BANK_PATH = Path("data/questions/trivia.json")
bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))


FIXES = [
    # #1159 T1: Mary Celeste
    {
        "idx": 1159,
        "patch": {
            "question": (
                "December 1872, Atlantic: a ship is found drifting — sails "
                "set, cargo intact, lifeboat missing, and not a soul on "
                "board. Captain, wife, daughter, and seven crew all gone. "
                "What's the famous ghost ship?"
            ),
            "answer": "The Mary Celeste",
            "choices": [
                "The Mary Celeste",
                "The Flying Dutchman",
                "The Bellerophon",
                "The Octavius",
            ],
            "context": (
                "The American brigantine Mary Celeste was found by the "
                "British ship Dei Gratia east of the Azores on December 4, "
                "1872. Captain Briggs, his wife Sarah, daughter Sophia, and "
                "all seven crew were never seen again. The cargo of 1,701 "
                "alcohol barrels was intact; the lifeboat was missing. "
                "Modern theory: Briggs feared a hold-fire from leaking "
                "alcohol vapor and ordered evacuation; the ship sailed "
                "away from them. The archetypal ghost ship, referenced "
                "by Conan Doyle, Doctor Who, and countless others."
            ),
        },
    },
    # #1150 T1: Surgeon's Photograph
    {
        "idx": 1150,
        "patch": {
            "question": (
                "The most famous Loch Ness Monster photo, taken in 1934, "
                "made Nessie a worldwide sensation. In 1994 it was "
                "revealed as a hoax — a toy submarine with a sculpted "
                "neck. What's the photo called?"
            ),
            "answer": "The Surgeon's Photograph",
            "choices": [
                "The Surgeon's Photograph",
                "The Wilson Photograph",
                "The Nessie Plate",
                "The Loch Image",
            ],
            "context": (
                "Published April 21, 1934 by Dr. Robert Kenneth Wilson — a "
                "London gynaecologist — who claimed to have taken it while "
                "driving along the loch. The 'Surgeon' nickname came from "
                "his refusal to publicly attach his name. In 1994 Christian "
                "Spurling confessed on his deathbed that he, his stepfather "
                "Marmaduke Wetherell, and Wilson staged the photo with a "
                "toy submarine and a sculpted neck. Wetherell had been "
                "humiliated by the Daily Mail over a 'Nessie footprint' "
                "hoax and orchestrated the photo as revenge."
            ),
        },
    },
    # #1178 T2: Roanoke (CROATOAN already at #1143, so pivot to Virginia Dare)
    {
        "idx": 1178,
        "patch": {
            "question": (
                "Among the 115 colonists who vanished from Roanoke between "
                "1587 and 1590 was a girl who became famous as the first "
                "English child born in what's now the United States. Her "
                "grandfather was the colony's governor, John White, who "
                "returned from England to find everyone gone. What was "
                "her name?"
            ),
            "answer": "Virginia Dare",
            "choices": [
                "Virginia Dare",
                "Eleanor Dare",
                "Margery Harvie",
                "Agnes Wood",
            ],
            "context": (
                "Virginia Dare was born August 18, 1587 — nine days after "
                "the colony's arrival. She was the daughter of Ananias and "
                "Eleanor Dare and granddaughter of Governor John White. "
                "When White returned to England for supplies, the Spanish "
                "Armada delayed him three years; he returned in August "
                "1590 to find the colony abandoned, fortifications "
                "dismantled, no bodies, and the word CROATOAN carved on a "
                "fence post. A storm prevented his search of nearby "
                "Croatoan Island. Virginia Dare's name remains an American "
                "mystery icon."
            ),
        },
    },
    # #1200 T3: Voynich Manuscript (already passed in v1)
    {
        "idx": 1200,
        "patch": {
            "question": (
                "The most famous undeciphered book in the world is a "
                "240-page illustrated codex written in a unique script no "
                "linguist has ever cracked. It contains strange botanical "
                "drawings, naked women in green pools, and astronomical "
                "charts. Polish-American antique dealer Wilfrid Voynich "
                "bought it in 1912 from a Jesuit college near Rome. What's "
                "the manuscript called?"
            ),
            "answer": "The Voynich Manuscript",
            "choices": [
                "The Voynich Manuscript",
                "The Codex Seraphinianus",
                "The Rohonc Codex",
                "The Liber Linteus",
            ],
            "context": (
                "Carbon-dated to 1404-1438. ~240 pages of vellum. Its "
                "'script' has consistent statistical properties suggesting "
                "a real language or constructed cipher, but cryptographers "
                "from WWII codebreakers to modern AI researchers have all "
                "failed to crack it. Some plants depicted may match New "
                "World species — predating Columbus impossibly. Currently "
                "held at Yale's Beinecke Library as MS 408. Theories: "
                "medieval cipher, hoax, lost language, even alchemical "
                "code. The Codex Seraphinianus (1981, Luigi Serafini) is a "
                "modern art-book cousin."
            ),
        },
    },
    # #1156 T1: Slender Man
    {
        "idx": 1156,
        "patch": {
            "question": (
                "On the Something Awful forum in 2009, a Photoshop contest "
                "introduced a tall, suit-wearing, faceless figure stalking "
                "children. The character spawned games, comics, and a "
                "2018 horror movie. What's it called?"
            ),
            "answer": "Slender Man",
            "choices": [
                "Slender Man",
                "The Tall Man",
                "The Operator",
                "The Hat Man",
            ],
            "context": (
                "Created by Eric Knudsen (handle 'Victor Surge') for a "
                "Something Awful Photoshop contest about supernatural "
                "images. Entrants were asked to alter photos to look like "
                "real paranormal documents. Slender Man's documents were "
                "photoshopped to look like archive shots of children with "
                "a faceless tall figure in the background. The character "
                "became a viral creepypasta, then the 2012 indie game "
                "Slender: The Eight Pages, then a 2018 movie. A tragic "
                "Wisconsin case in May 2014 brought the character to "
                "national news and a documentary, Beware the Slenderman."
            ),
        },
    },
    # #426 T1: Conan — pivot to the iconic Thulsa Doom actor
    {
        "idx": 426,
        "patch": {
            "question": (
                "In John Milius's 1982 Conan the Barbarian, a snake-cult "
                "wizard kills young Conan's parents and is hunted across "
                "the steppes for revenge. The villain is played by an "
                "actor whose iconic voice also belonged to Darth Vader. "
                "Who played Thulsa Doom?"
            ),
            "answer": "James Earl Jones",
            "choices": [
                "James Earl Jones",
                "Max von Sydow",
                "Christopher Lee",
                "Ben Kingsley",
            ],
            "context": (
                "James Earl Jones brings his deep theatrical training (he "
                "studied with Lee Strasberg) and famous voice to Thulsa "
                "Doom. The same year — 1982 — he was also voicing Darth "
                "Vader in Empire-era Star Wars production. The Atlantean "
                "sword, the Riddle of Steel, Mako Iwamatsu's opening "
                "narration ('Crom!'), and Basil Poledouris's anvil-chorus "
                "score are the other iconic elements of the film. The "
                "famous line 'What is best in life? To crush your "
                "enemies...' is borrowed from a Mongol-warlord saying."
            ),
        },
    },
    # #427 T1: Princess Leia hiding plans in R2-D2
    {
        "idx": 427,
        "patch": {
            "question": (
                "In 1977's Star Wars, Leia hides something inside R2-D2 "
                "before her capture by Darth Vader — the McGuffin the "
                "heroes risk everything to deliver. What is it?"
            ),
            "answer": "Plans for the Death Star",
            "choices": [
                "Plans for the Death Star",
                "Rebel base coordinates",
                "Her foster parents' location",
                "Imperial fleet positions",
            ],
            "context": (
                "The technical readout of the Death Star — stolen by Rebel "
                "spies on Toprawa in events later expanded by Rogue One "
                "(2016) — is hidden in R2's memory along with Leia's "
                "hologram message: 'Help me, Obi-Wan Kenobi. You're my "
                "only hope.' R2 escapes the captured Tantive IV, lands on "
                "Tatooine, and the rest is the plot of A New Hope. The "
                "Death Star plans reveal the vulnerable exhaust port "
                "Luke later exploits."
            ),
        },
    },
    # #885 T1: Harry's Patronus (with Prongs connection)
    {
        "idx": 885,
        "patch": {
            "question": (
                "Harry Potter's Patronus matches his father James's "
                "animagus form — a connection that moves Harry to tears "
                "the first time he sees it. What animal is Harry's "
                "Patronus?"
            ),
            "answer": "A stag, like his father 'Prongs'",
            "choices": [
                "A stag, like his father 'Prongs'",
                "A wolf, like his mentor Lupin",
                "A doe, like his mother Lily",
                "An owl, like his pet Hedwig",
            ],
            "context": (
                "James Potter was an unregistered Animagus at Hogwarts, "
                "transforming into a stag — earning him the Marauder "
                "nickname 'Prongs'. His three best friends were Sirius "
                "Black (Padfoot, a dog), Remus Lupin (Moony, a werewolf), "
                "and Peter Pettigrew (Wormtail, a rat). Harry's Patronus "
                "inheriting the stag form ties him to his father even "
                "though James died when Harry was a baby. Lily's Patronus "
                "was a doe; Snape's was also a doe, in memory of her."
            ),
        },
    },
]


# === APPLY ===
dup, ans = build_bank_indices(bank)
print(f"Applying {len(FIXES)} trivia fixes...\n")

results = {"applied": [], "failed": []}
for fix in FIXES:
    idx = fix["idx"]
    q_new = dict(bank[idx])
    for k, v in fix["patch"].items():
        q_new[k] = v
    # Quick size hint
    total = len(q_new["question"]) + sum(len(c) for c in q_new["choices"])
    r = validate_rewrite("trivia", q_new, bank=bank, dup_index=dup, answer_index=ans, replace_idx=idx)
    if r["verdict"] in ("PASS", "SOFT_WARN"):
        bank[idx] = q_new
        results["applied"].append(idx)
        dup, ans = build_bank_indices(bank)
        print(f"  #{idx} T{q_new['tier']}: {r['verdict']}  ({total}c)  -> {q_new['answer'][:50]}")
    else:
        results["failed"].append((idx, r["hard_fails"], total))
        print(f"  #{idx} T{q_new['tier']}: FAIL  ({total}c)")
        for g, reason in r["hard_fails"][:2]:
            print(f"    {g}: {reason[:140]}")

print(f"\nApplied: {len(results['applied'])} / Failed: {len(results['failed'])}")

if results["applied"]:
    BANK_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {BANK_PATH}")
