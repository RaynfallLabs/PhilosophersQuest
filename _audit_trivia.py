"""Trivia Phase 5 audit.

Scans the 1386-question trivia bank for:
1. Spoiler residues (banned spoiler patterns OUTSIDE the 10 allowed franchises)
2. Stance violations (post-Endgame MCU, Disney SW, post-Attitude, post-Legends, modern D&D)
3. Pillar coverage gaps
"""
import json
import re
import sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

bank = json.loads(Path("data/questions/trivia.json").read_text(encoding="utf-8"))
print(f"Auditing {len(bank)} trivia questions\n")

# Spoiler-allowed franchises (must match gates/trivia.py)
SPOILER_ALLOWED = re.compile(
    r"\b(?:"
    r"My Hero Academia|MHA|Boku no Hero|All Might|Deku|Bakugo|Todoroki|Shigaraki|One For All|"
    r"Hajime no Ippo|Ippo|Dempsey Roll|Kamogawa|Takamura|"
    r"Harry Potter|Hogwarts|Voldemort|Dumbledore|Sirius|Hermione|Hagrid|Snape|Horcrux|Mary Sue|"
    r"Star Wars\s*(?:Episode\s*[IV-VI]|original trilogy|A New Hope|Empire Strikes Back|Return of the Jedi|1977|1980|1983)|"
    r"Marvel Cinematic Universe|MCU|Avengers|Endgame|Infinity War|Iron Man|Thanos|Tony Stark|Captain America|Civil War|Stuttgart|Wakanda|"
    r"Toilet[- ]?Bound Hanako[- ]?kun|Hanako[- ]?kun|Nene Yashiro|Amane Yugi|"
    r"Dragon Ball(?:\s*Z)?|DBZ|Goku|Vegeta|Frieza|Cell|Buu|Saiyan|Namek|Kamehameha|"
    r"Scott Pilgrim|Ramona Flowers|Sex Bob-omb|Wallace Wells|Knives Chau|Gideon Graves|"
    r"Princess Bride|Westley|Inigo Montoya|Vizzini|Fezzik|Buttercup|"
    r"(?:Super )?Mario(?:\s*Bros\.?)?\s*Movie\s*(?:2023|\(2023\))?|"
    r"Illumination Mario|Chris Pratt Mario|Anya Taylor-Joy Peach"
    r")\b",
    re.IGNORECASE,
)

# Spoiler patterns (must match gates/trivia.py)
SPOILER_PATTERN = re.compile(
    r"(?:"
    r"\bWho (?:kills?|killed|murders?|murdered)\b|"
    r"\bWhat happens (?:to|at the end|in the climax|in the (?:final|last))\b|"
    r"\b(?:secretly|turns out|revealed to be) (?:a |the )?(?:traitor|murderer|killer|villain|spy|ally|hero)\b|"
    r"\bdies at the (?:end|hands of|final)\b|"
    r"\bWho is the (?:true|real|secret) (?:villain|killer|murderer|traitor|father|mother)\b|"
    r"\bSephiroth\s+(?:kills?|killed|murders?|murdered)\b|"
    r"\bAerith\s+(?:dies?|killed?|murdered?)\b"
    r")",
    re.IGNORECASE,
)

# Stance bans
STANCE_PATTERNS = {
    "post-Endgame MCU": re.compile(
        r"\b(?:WandaVision|Falcon and Winter Soldier|Loki\s+series|Hawkeye\s+series|Moon Knight|"
        r"Ms\.?\s*Marvel|She[- ]?Hulk|Secret Invasion\s+series|Echo\s+series|Agatha All Along|"
        r"Spider[- ]?Man:?\s*No Way Home|Black Widow\s+\(?2021|Eternals|Shang[- ]?Chi|"
        r"Multiverse of Madness|Love and Thunder|Wakanda Forever|Quantumania|"
        r"Guardians.*Vol\.?\s*3|The Marvels\s+\(?2023|Deadpool.*Wolverine|"
        r"Phase 4|Phase 5|Phase 6|TVA|Time Variance Authority)\b", re.IGNORECASE),
    "Disney SW": re.compile(
        r"\b(?:Force Awakens|Last Jedi|Rise of Skywalker|Episode VII|Episode VIII|Episode IX|"
        r"Rey Skywalker|Kylo Ren|Snoke|Finn FN-2187|Poe Dameron|Mandalorian|Grogu|Baby Yoda|"
        r"Boba Fett\s+(?:series|show|Book of)|Obi[- ]?Wan Kenobi\s+series|Andor|Ahsoka|Acolyte|"
        r"Skeleton Crew|Rogue One|Solo:?\s*A Star Wars)\b", re.IGNORECASE),
    "post-Attitude wrestling": re.compile(
        r"\b(?:Ruthless Aggression Era|PG Era|Reality Era|John Cena|Randy Orton|Batista|"
        r"CM Punk|Daniel Bryan|Sheamus|Roman Reigns|Seth Rollins|Dean Ambrose|The Shield WWE|"
        r"Becky Lynch|Sasha Banks|AJ Styles WWE|Nakamura WWE|Finn Bálor|NXT|AEW|All Elite|MJF)\b",
        re.IGNORECASE),
    "post-Legends MtG": re.compile(
        # Tighter regex requiring MtG context (the gate's regex over-fires)
        r"\b(?:MTG\s+|Magic\s+the\s+Gathering\s+(?:set|expansion|block)\s+)(?:Ice Age|Alliances|Mirage|"
        r"Tempest|Urza|Mercadian|Invasion|Odyssey|Onslaught|Mirrodin|Kamigawa|Ravnica|Lorwyn|"
        r"Zendikar|Innistrad|Theros)\b", re.IGNORECASE),
    "modern D&D": re.compile(
        r"\b(?:ancestry (?:instead of|replacing) race|5\.?e\s+errata|Tasha'?s Cauldron|"
        r"OneD&D|Players? Handbook 2024|D&D Beyond)\b", re.IGNORECASE),
    "credulous cryptid": re.compile(
        r"\b(?:Bigfoot (?:is|are) (?:definitely|undoubtedly|proven|real)|"
        r"Atlantis (?:was|did) (?:real|exist|exist for real)|"
        r"ancient aliens (?:built|created) (?:the )?(?:pyramids|Stonehenge|Easter Island))\b",
        re.IGNORECASE),
}

# Run audit
spoiler_hits = []
stance_hits: dict = {k: [] for k in STANCE_PATTERNS}

for i, q in enumerate(bank):
    text_full = (q.get("question", "") + " " + q.get("answer", "") + " "
                 + q.get("context", "") + " "
                 + " ".join(c if isinstance(c, str) else "" for c in q.get("choices", [])))
    # Spoiler audit (must be OUTSIDE allowed franchises)
    m = SPOILER_PATTERN.search(text_full)
    if m and not SPOILER_ALLOWED.search(text_full):
        spoiler_hits.append({
            "bank_idx": i,
            "tier": q["tier"],
            "stem_preview": q["question"][:100],
            "matched_phrase": m.group(0),
        })
    # Stance audits
    for stance, pat in STANCE_PATTERNS.items():
        if pat.search(text_full):
            stance_hits[stance].append({
                "bank_idx": i,
                "tier": q["tier"],
                "stem_preview": q["question"][:100],
                "matched_phrase": pat.search(text_full).group(0),
            })

# Reports
print("=== SPOILER AUDIT ===")
print(f"  Spoiler-pattern hits OUTSIDE allowed franchises: {len(spoiler_hits)}")
for h in spoiler_hits[:10]:
    print(f"    #{h['bank_idx']} T{h['tier']} {h['matched_phrase']!r}: {h['stem_preview']}...")

print()
print("=== STANCE AUDIT ===")
for stance, hits in stance_hits.items():
    print(f"  {stance}: {len(hits)} hits")
    for h in hits[:3]:
        print(f"    #{h['bank_idx']} T{h['tier']} {h['matched_phrase']!r}: {h['stem_preview']}...")

# Tier distribution check
print()
print("=== TIER DISTRIBUTION ===")
tc = Counter(q["tier"] for q in bank)
for t in (1, 2, 3, 4, 5):
    print(f"  T{t}: {tc.get(t, 0)}")

# Save full audit
out = {
    "bank_size": len(bank),
    "spoiler_hits": spoiler_hits,
    "stance_hits": stance_hits,
    "tier_dist": dict(tc),
}
Path("_trivia_audit.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print()
print(f"Wrote _trivia_audit.json")
