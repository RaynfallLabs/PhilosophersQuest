"""Trivia bank structural gates.

The trivia bank is the geek-dad canon — see
`proposals/v2_audit/TRIVIA_FRAMEWORK.md` (the Easter Egg Pattern with
cultural-osmosis carve-out + 10 spoiler-allowed franchises) and
`docs/quiz/subjects/trivia.md` (canonical stance, 2026-05-14).

Reuses subject-agnostic gates from `tools.quizgen.gates.philosophy`
(schema, choice_shape_parity, context_no_meta_references). Adds
trivia-specific gates:

  - no_spoilers              (HARD) — flags spoiler patterns OUTSIDE
                                     the 10 allowed franchises
  - no_modern_multiverse     (HARD) — flags Disney+ MCU shows, post-
                                     Endgame films, modern X-Men runs
  - no_disney_star_wars      (HARD) — Star Wars sequels (VII/VIII/IX)
                                     + Disney+ shows
  - no_post_attitude_era     (HARD) — WWE content after WM18 March 17,
                                     2002
  - no_post_legends_mtg      (HARD) — MtG expansions after Legends
                                     (June 1994)
  - no_modern_dnd_errata     (HARD) — modern 5e errata, ancestry
                                     rewrites, sensitivity reads
  - no_credulous_cryptid     (SOFT) — flags "Bigfoot IS real" /
                                     "Atlantis DID exist" framing
"""
from __future__ import annotations

import re
from typing import Callable, Optional

from tools.quizgen.gates.philosophy import (
    gate_choice_shape_parity,
    gate_context_no_meta_references,
)


TIER_CAPS = {1: 280, 2: 480, 3: 680, 4: 900, 5: 1100}


# Spoiler-allowed franchises (kids have seen them — internal plot OK)
SPOILER_ALLOWED = re.compile(
    r"\b(?:"
    r"My Hero Academia|MHA|Boku no Hero|"
    r"Hajime no Ippo|Ippo (?:Makunouchi|the Fighting)?|"
    r"Harry Potter|Hogwarts|Voldemort|Dumbledore|Sirius (?:Black)?|Hermione|"
    r"Star Wars\s*(?:Episode\s*[IV-VI]|original trilogy|A New Hope|Empire Strikes Back|Return of the Jedi|1977|1980|1983)|"
    r"Marvel Cinematic Universe|MCU|Avengers|Endgame|Infinity War|Iron Man|Thanos|Tony Stark|Captain America|Civil War|"
    r"Toilet[- ]?Bound Hanako[- ]?kun|Hanako[- ]?kun|"
    r"Dragon Ball(?:\s*Z)?|DBZ|Goku|Vegeta|Frieza|Cell|Buu|Saiyan|Namek|"
    r"Scott Pilgrim|Ramona Flowers|"
    r"Princess Bride|Westley|Inigo Montoya|Vizzini|"
    r"(?:Super )?Mario(?:\s*Bros\.?)?\s*Movie\s*(?:2023|\(2023\))?|"
    r"Illumination Mario"
    r")\b",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------
# Schema gate
# --------------------------------------------------------------------------

def gate_schema(q: dict) -> Optional[str]:
    for field in ("tier", "question", "answer", "choices", "context"):
        if field not in q:
            return f"schema: missing field {field}"
    if q.get("tier") not in (1, 2, 3, 4, 5):
        return f"schema: invalid tier {q.get('tier')}"
    chs = q.get("choices", [])
    if len(chs) != 4:
        return f"schema: choices length {len(chs)}"
    if q.get("answer") not in chs:
        return "schema: answer not in choices"
    return None


# --------------------------------------------------------------------------
# Gate: no_spoilers (HARD with 10-franchise carve-out)
# --------------------------------------------------------------------------

# Common-knowledge / cultural-osmosis patterns that are FINE even though
# they look like spoilers (Vader is Luke's father, Bruce Wayne = Batman,
# Spider-bite origin, etc.) — kept simple; the agent / human reviewer
# decides edge cases. These are general patterns the gate should NOT flag.
CULTURAL_OSMOSIS_PATTERNS = re.compile(
    r"\b(?:"
    # Secret identities (common-knowledge)
    r"Bruce Wayne is Batman|Clark Kent is Superman|Peter Parker is Spider[- ]?Man|"
    r"Diana (?:Prince )?is Wonder Woman|Tony Stark is Iron Man|"
    # Iconic memed lines
    r"Luke,? I am your father|May the Force be with you|These aren't the droids|"
    r"Inconceivable|I'?ll be back|Hasta la vista|I'?m your huckleberry|"
    r"As you wish|"
    # Foundational origin tropes that are common knowledge
    r"radioactive spider|gamma bomb|super[- ]?soldier serum|Krypton(?:ian)?\s+explod"
    r")\b",
    re.IGNORECASE,
)

# Spoiler-signal patterns — common question forms that often reveal
# story endings, character deaths, twist identities.
SPOILER_PATTERN = re.compile(
    r"(?:"
    r"\bWho (?:kills?|killed|murders?|murdered|defeats?|defeated|dies?|dead in)\b|"
    r"\bWhat happens (?:to|at the end|in the climax|in the (?:final|last) (?:scene|chapter|episode|act))\b|"
    r"\b(?:final|last) (?:scene|moments?|chapter|episode|act) reveals?\b|"
    r"\bThe (?:twist|surprise|reveal) (?:is|was|at the end)\b|"
    r"\b(?:secretly|turns out|revealed to be) (?:a |the )?(?:traitor|murderer|killer|villain|spy|ally|hero)\b|"
    r"\bdies at the (?:end|hands of|final)\b|"
    r"\bWho is the (?:true|real|secret) (?:villain|killer|murderer|traitor|father|mother)\b|"
    r"\bWhat is (?:Keyser Söze|the secret of|the truth behind)\b|"
    r"\bShyamalan twist\b|"
    # Specific famous spoilers
    r"\bSephiroth\s+(?:kills?|killed|murders?|murdered)\b|"
    r"\bAerith\s+(?:dies?|killed?|murdered?)\b|"
    r"\bSnape\s+kills?\s+Dumbledore\b|"  # this one IS allowed (Harry Potter) but flag for review
    r"\bSoylent Green is\b"
    r")",
    re.IGNORECASE,
)


def gate_no_spoilers(q: dict) -> Optional[str]:
    """Hard-reject spoiler-pattern stems/answers, EXCEPT when the spoiler
    target is one of the 10 spoiler-allowed franchises.

    Pass:
    - Cultural-osmosis common knowledge ("Luke, I am your father")
    - Anything tagged to the 10 allowed franchises
    Fail:
    - Generic plot-reveal patterns ("Who kills X in [non-allowed]")
    """
    text_full = (
        (q.get("question", "") or "")
        + " "
        + (q.get("answer", "") or "")
        + " "
        + " ".join(c if isinstance(c, str) else "" for c in q.get("choices", []) or [])
    )
    # Cultural-osmosis content always passes
    if CULTURAL_OSMOSIS_PATTERNS.search(text_full):
        return None
    # Spoiler-pattern hit?
    m = SPOILER_PATTERN.search(text_full)
    if not m:
        return None
    # Is the matched spoiler target inside an allowed-franchise context?
    if SPOILER_ALLOWED.search(text_full):
        return None
    return (
        f"no_spoilers: matched spoiler pattern {m.group(0)!r} outside the "
        f"10 allowed franchises — see TRIVIA_FRAMEWORK §1 cultural-osmosis "
        f"carve-out + spoiler-allowed list"
    )


# --------------------------------------------------------------------------
# Gate: no_modern_multiverse (HARD)
# --------------------------------------------------------------------------

# Post-Endgame MCU + Disney+ shows + modern multiverse comics
MODERN_MULTIVERSE_PATTERN = re.compile(
    r"\b(?:"
    # Disney+ MCU shows
    r"WandaVision|Falcon and (?:the )?Winter Soldier|Loki(?:\s+(?:series|show|season))|"
    r"Hawkeye(?:\s+(?:series|show))|Moon Knight|Ms\.?\s*Marvel|"
    r"She[- ]?Hulk(?:\s+(?:Attorney|series|show))|Secret Invasion(?:\s+(?:series|show))|"
    r"Echo(?:\s+(?:series|show))|Agatha All Along|Daredevil:\s*Born Again|"
    # Post-Endgame MCU films
    r"Spider[- ]?Man:?\s*(?:Far From Home|No Way Home)|"
    r"Black Widow\s+\(?2021\)?|"
    r"Eternals(?:\s+\(?2021\)?)|"
    r"Shang[- ]?Chi|"
    r"Doctor Strange (?:in the )?Multiverse of Madness|"
    r"Thor:?\s*Love and Thunder|"
    r"Black Panther:?\s*Wakanda Forever|"
    r"Ant[- ]?Man (?:and the Wasp:?\s*)?Quantumania|"
    r"Guardians of the Galaxy Vol\.?\s*3|"
    r"The Marvels\s+\(?2023\)?|"
    r"Deadpool (?:&|and) Wolverine|"
    # Multiverse / post-2020 terminology
    r"Phase 4|Phase 5|Phase 6|"
    r"sacred timeline|TVA(?:\s+(?:agents|agent))|Time Variance Authority|"
    r"variant Loki|variant She[- ]?Hulk|"
    # Modern X-Men runs (post-2003)
    r"House of X|Powers of X|HoX|PoX|Krakoan (?:Age|era)|Quiet Council"
    r")\b",
    re.IGNORECASE,
)


def gate_no_modern_multiverse(q: dict) -> Optional[str]:
    """Hard-reject post-2003 multiverse capeshit + post-Endgame MCU
    content."""
    haystacks = [
        q.get("question", "") or "",
        q.get("answer", "") or "",
        q.get("context", "") or "",
    ] + [c if isinstance(c, str) else "" for c in q.get("choices", []) or []]
    for h in haystacks:
        m = MODERN_MULTIVERSE_PATTERN.search(h)
        if m:
            return (
                f"no_modern_multiverse: contains modern-multiverse content "
                f"{m.group(0)!r} — out of scope per TRIVIA_FRAMEWORK §6"
            )
    return None


# --------------------------------------------------------------------------
# Gate: no_disney_star_wars (HARD)
# --------------------------------------------------------------------------

DISNEY_STAR_WARS_PATTERN = re.compile(
    r"\b(?:"
    # Sequel trilogy
    r"(?:Star Wars:?\s*)?(?:The )?Force Awakens|"
    r"(?:Star Wars:?\s*)?(?:The )?Last Jedi|"
    r"(?:Star Wars:?\s*)?(?:The )?Rise of Skywalker|"
    r"Episode VII|Episode VIII|Episode IX|"
    r"Rey Skywalker|Kylo Ren|Snoke|Finn FN-2187|Poe Dameron|"
    # Disney+ shows
    r"(?:The )?Mandalorian|Grogu|Baby Yoda|"
    r"(?:The )?Book of Boba Fett|"
    r"Obi[- ]?Wan Kenobi\s+(?:series|show)|"
    r"Andor(?:\s+(?:series|show))|Cassian Andor\s+(?:series|show)|"
    r"Ahsoka(?:\s+(?:series|show))|"
    r"(?:The )?Acolyte|"
    r"Skeleton Crew|"
    # Disney-era films
    r"Rogue One:?\s*A Star Wars Story|"
    r"Solo:?\s*A Star Wars Story"
    r")\b",
    re.IGNORECASE,
)


def gate_no_disney_star_wars(q: dict) -> Optional[str]:
    """Hard-reject Disney-era Star Wars (sequel trilogy + Disney+ shows
    + Rogue One/Solo)."""
    haystacks = [
        q.get("question", "") or "",
        q.get("answer", "") or "",
        q.get("context", "") or "",
    ] + [c if isinstance(c, str) else "" for c in q.get("choices", []) or []]
    for h in haystacks:
        m = DISNEY_STAR_WARS_PATTERN.search(h)
        if m:
            return (
                f"no_disney_star_wars: contains Disney-era Star Wars "
                f"{m.group(0)!r} — out of scope (original trilogy + prequels "
                f"OK; everything Disney-era out per TRIVIA_FRAMEWORK §6)"
            )
    return None


# --------------------------------------------------------------------------
# Gate: no_post_attitude_era (HARD)
# --------------------------------------------------------------------------

# Wrestlers + events specifically from post-Attitude-Era WWE
POST_ATTITUDE_PATTERN = re.compile(
    r"\b(?:"
    # Modern WWE eras
    r"Ruthless Aggression Era|PG Era|Reality Era|New Era|Smackdown Live brand split|"
    # Wrestlers who debuted post-March 2002 or peaked post-attitude
    r"John Cena|Randy Orton|Batista|Dave Bautista wrestler|"
    r"CM Punk|Daniel Bryan|Sheamus|Ryback|"
    r"Roman Reigns|Seth Rollins|Dean Ambrose|The Shield(?:\s+(?:WWE|debut))|"
    r"Becky Lynch|Charlotte Flair|Sasha Banks|Bayley|"
    r"AJ Styles\s+WWE|Shinsuke Nakamura\s+WWE|Finn Bálor|"
    r"NXT brand|NXT TakeOver|"
    r"Money in the Bank ladder match|MITB briefcase|"
    r"WrestleMania (?:1[9-9]|2[0-9]|3[0-9]|4[0-9])|"  # WM19+ (post-WM18 2002)
    r"WrestleMania XIX|WrestleMania XX|"
    # Pro-wrestling promotions that emerged post-2002
    r"AEW|All Elite Wrestling|MJF|Cody Rhodes\s+AEW|Kenny Omega"
    r")\b",
    re.IGNORECASE,
)


def gate_no_post_attitude_era(q: dict) -> Optional[str]:
    """Hard-reject WWE content after WM18 (March 17, 2002).

    Note: heuristic — some pre-2002 wrestlers (e.g., Triple H, Undertaker)
    continued well past 2002 and references to them in their pre-2002
    work are FINE; the gate targets specific post-2002 events / debuts /
    matches.
    """
    haystacks = [
        q.get("question", "") or "",
        q.get("answer", "") or "",
        q.get("context", "") or "",
    ] + [c if isinstance(c, str) else "" for c in q.get("choices", []) or []]
    for h in haystacks:
        m = POST_ATTITUDE_PATTERN.search(h)
        if m:
            return (
                f"no_post_attitude_era: contains post-Attitude-Era WWE "
                f"{m.group(0)!r} — boundary is Hogan-Rock WM18 March 17, "
                f"2002 per TRIVIA_FRAMEWORK §6"
            )
    return None


# --------------------------------------------------------------------------
# Gate: no_post_legends_mtg (HARD)
# --------------------------------------------------------------------------

POST_LEGENDS_MTG_PATTERN = re.compile(
    r"\b(?:"
    # MtG sets after Legends (June 1994)
    r"(?:MTG\s+)?The Dark\s+(?:expansion|1994)|"
    r"(?:MTG\s+)?Fallen Empires|"
    r"(?:MTG\s+)?Ice Age|(?:MTG\s+)?Alliances|(?:MTG\s+)?Coldsnap|"
    r"(?:MTG\s+)?Mirage|(?:MTG\s+)?Visions|(?:MTG\s+)?Weatherlight|"
    r"(?:MTG\s+)?Tempest|(?:MTG\s+)?Stronghold|(?:MTG\s+)?Exodus|"
    r"(?:MTG\s+)?Urza'?s Saga|(?:MTG\s+)?Urza'?s Legacy|(?:MTG\s+)?Urza'?s Destiny|"
    r"(?:MTG\s+)?Mercadian Masques|(?:MTG\s+)?Nemesis|(?:MTG\s+)?Prophecy|"
    r"(?:MTG\s+)?Invasion|(?:MTG\s+)?Planeshift|(?:MTG\s+)?Apocalypse|"
    r"(?:MTG\s+)?Odyssey|(?:MTG\s+)?Torment|(?:MTG\s+)?Judgment|"
    r"(?:MTG\s+)?Onslaught|(?:MTG\s+)?Legions|(?:MTG\s+)?Scourge|"
    r"(?:MTG\s+)?Mirrodin|(?:MTG\s+)?Darksteel|(?:MTG\s+)?Fifth Dawn|"
    r"(?:MTG\s+)?Kamigawa|(?:MTG\s+)?Champions of Kamigawa|"
    r"(?:MTG\s+)?Ravnica|(?:MTG\s+)?Lorwyn|(?:MTG\s+)?Shadowmoor|"
    r"(?:MTG\s+)?Zendikar|(?:MTG\s+)?Worldwake|(?:MTG\s+)?Innistrad|"
    r"(?:MTG\s+)?Theros|(?:MTG\s+)?Khans of Tarkir|"
    r"(?:MTG\s+)?Battle for Zendikar|(?:MTG\s+)?Modern Horizons|"
    r"(?:MTG\s+)?Commander\s+(?:2011|201[2-9]|202[0-9])|"
    r"(?:MTG\s+)?planeswalker (?:card type|character)\b|"
    r"Jace Beleren|Liliana Vess|Chandra Nalaar|Nicol Bolas card|"
    # Modern MtG concepts
    r"Standard format|Modern format|Pioneer format|Legacy format|Vintage format|"
    r"Commander \(MTG\)|EDH|Brawl|"
    r"MTG Arena|MTG Online"
    r")\b",
    re.IGNORECASE,
)


def gate_no_post_legends_mtg(q: dict) -> Optional[str]:
    """Hard-reject MtG expansions / concepts after Legends (June 1994).

    Allowed: Alpha (1993), Beta (1993), Unlimited (1993), Arabian Nights
    (1993), Antiquities (1994), Revised (1994), Legends (June 1994), Power
    Nine, all Garfield / Adkison origin lore.
    """
    haystacks = [
        q.get("question", "") or "",
        q.get("answer", "") or "",
        q.get("context", "") or "",
    ] + [c if isinstance(c, str) else "" for c in q.get("choices", []) or []]
    for h in haystacks:
        m = POST_LEGENDS_MTG_PATTERN.search(h)
        if m:
            return (
                f"no_post_legends_mtg: contains post-Legends MtG content "
                f"{m.group(0)!r} — only Alpha through Legends (June 1994) "
                f"in scope per TRIVIA_FRAMEWORK §6"
            )
    return None


# --------------------------------------------------------------------------
# Gate: no_modern_dnd_errata (HARD)
# --------------------------------------------------------------------------

MODERN_DND_ERRATA_PATTERN = re.compile(
    r"\b(?:"
    # Modern terminology replacements
    r"ancestry (?:instead of|replacing|over) race|"
    r"race-?to-?ancestry|"
    r"alignment removal|removed alignment|"
    r"D&D (?:5\.?e|5th edition)\s+errata|"
    r"sensitivity (?:read|review|consultant) for (?:D&?D|Drow|Orcs)|"
    r"Drow (?:retcon|rewrite|sensitivity)|"
    r"Orcs not (?:evil|monstrous)|"
    r"(?:Wizards|WotC) (?:apology|apologized) for (?:racist|problematic)|"
    r"Tasha'?s Cauldron of Everything|"
    r"Mordenkainen Presents:?\s*Monsters of the Multiverse|"
    r"Spelljammer Adventures in Space (?:2022|new)|"
    r"Dragonlance Shadow of the Dragon Queen|"
    r"Phandelver and Below|"
    r"OneD&D|One D&D|D&D One|"
    r"Players? Handbook 2024|DMG 2024|PHB 2024"
    r")\b",
    re.IGNORECASE,
)


def gate_no_modern_dnd_errata(q: dict) -> Optional[str]:
    """Hard-reject modern D&D errata, ancestry rewrites, sensitivity
    reads. Classic Gygax-era through 3.5e is the scope."""
    haystacks = [
        q.get("question", "") or "",
        q.get("answer", "") or "",
        q.get("context", "") or "",
    ] + [c if isinstance(c, str) else "" for c in q.get("choices", []) or []]
    for h in haystacks:
        m = MODERN_DND_ERRATA_PATTERN.search(h)
        if m:
            return (
                f"no_modern_dnd_errata: contains modern D&D errata "
                f"{m.group(0)!r} — classic Gygax-era TSR-era is the scope "
                f"per TRIVIA_FRAMEWORK §6"
            )
    return None


# --------------------------------------------------------------------------
# Gate: no_credulous_cryptid (SOFT-WARN)
# --------------------------------------------------------------------------

CREDULOUS_CRYPTID_PATTERN = re.compile(
    r"(?:"
    r"\bBigfoot (?:is|are) (?:real|definitely|undoubtedly|proven)\b|"
    r"\bSasquatch (?:is|are) (?:real|definitely|undoubtedly|proven)\b|"
    r"\b(?:the )?Loch Ness Monster (?:is|exists) (?:real|definitely)\b|"
    r"\bAtlantis (?:was|did) (?:real|exist|exist for real)\b|"
    r"\b(?:proven|confirmed|verified) (?:to be|that) Mothman\b|"
    r"\b(?:proven|confirmed) (?:ghost|alien|UFO) sighting\b|"
    r"\b(?:Bigfoot|Nessie|Mothman) (?:species|biological evidence)\b|"
    r"\bAncient aliens (?:built|created) the (?:pyramids|Stonehenge|Easter Island)\b|"
    r"\bproof of alien (?:visitation|contact|encounter)\b"
    r")",
    re.IGNORECASE,
)


def gate_no_credulous_cryptid(q: dict) -> Optional[str]:
    """SOFT-warn for credulous cryptid framing. Story-led only per
    TRIVIA_FRAMEWORK §5 — historical artifact + the lore, never 'this
    is definitely real.'"""
    haystacks = [
        ("stem", q.get("question", "") or ""),
        ("answer", q.get("answer", "") or ""),
        ("context", q.get("context", "") or ""),
    ] + [(f"choice-{i}", c) for i, c in enumerate(q.get("choices", []) or []) if isinstance(c, str)]
    for label, text in haystacks:
        m = CREDULOUS_CRYPTID_PATTERN.search(text)
        if m:
            return (
                f"soft-warn: no_credulous_cryptid: {label} contains "
                f"credulous cryptid framing: {m.group(0)!r} — story-led, "
                f"not credulous"
            )
    return None


# --------------------------------------------------------------------------
# Gate registry
# --------------------------------------------------------------------------

SOFT_WARN_GATES: frozenset[str] = frozenset({
    "no_credulous_cryptid",
})


PER_QUESTION_GATES: list[tuple[str, Callable[[dict], Optional[str]]]] = [
    ("schema", gate_schema),
    ("choice_shape_parity", gate_choice_shape_parity),
    ("context_no_meta_references", gate_context_no_meta_references),
    ("no_spoilers", gate_no_spoilers),
    ("no_modern_multiverse", gate_no_modern_multiverse),
    ("no_disney_star_wars", gate_no_disney_star_wars),
    ("no_post_attitude_era", gate_no_post_attitude_era),
    ("no_post_legends_mtg", gate_no_post_legends_mtg),
    ("no_modern_dnd_errata", gate_no_modern_dnd_errata),
    # Soft-warn
    ("no_credulous_cryptid", gate_no_credulous_cryptid),
]


def run_gates(q: dict) -> dict[str, Optional[str]]:
    return {name: fn(q) for name, fn in PER_QUESTION_GATES}


__all__ = [
    "PER_QUESTION_GATES",
    "SOFT_WARN_GATES",
    "run_gates",
    "gate_schema",
    "gate_no_spoilers",
    "gate_no_modern_multiverse",
    "gate_no_disney_star_wars",
    "gate_no_post_attitude_era",
    "gate_no_post_legends_mtg",
    "gate_no_modern_dnd_errata",
    "gate_no_credulous_cryptid",
    "TIER_CAPS",
    "SPOILER_ALLOWED",
]
