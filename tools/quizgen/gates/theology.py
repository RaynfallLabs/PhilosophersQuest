"""Theology bank structural gates.

The theology bank tells the stories of Western mythological + legendary
heritage — see `proposals/v2_audit/THEOLOGY_FRAMEWORK.md` (the Wonder
Pattern adapted for theology) and `docs/quiz/subjects/theology.md` (older
canonical, partially superseded by the broader cultural-heritage framing).

Reuses subject-agnostic gates from `tools.quizgen.gates.philosophy`
(schema, choice_shape_parity, context_no_meta_references). Adds five
theology-specific gates:

  - no_doctrine_quizzing     (HARD) — flags "Define X" / "What is the
                                      doctrine of X?" stems without
                                      named-figure/event grounding
  - no_author_attribution    (HARD) — flags "Who wrote X?" / "Who said
                                      Y?" stems that should be rewritten
                                      to the STORY
  - no_above_grade10_theology (HARD) — research-paper theology jargon
                                       blocked at any tier
  - no_smug_voice            (SOFT) — flags either smug-atheist
                                      ("ancient peoples ignorantly
                                      believed...") or smug-believer
                                      ("the false gods of...") framing
  - no_modern_cult_content   (HARD) — flags Jonestown, Heaven's Gate,
                                      Aum Shinrikyo etc. (out of scope)
"""
from __future__ import annotations

import re
from typing import Callable, Optional

from tools.quizgen.gates.philosophy import (
    gate_choice_shape_parity,
    gate_context_no_meta_references,
)


TIER_CAPS = {1: 280, 2: 480, 3: 680, 4: 900, 5: 1100}


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
# Gate: no_doctrine_quizzing (HARD)
# --------------------------------------------------------------------------

# Doctrine-quiz stems that don't tie the doctrine to a named figure or
# event. "What is the doctrine of X?" / "Define hypostatic union" /
# "Which heresy denied Y?" — banned unless grounded in story.
DOCTRINE_QUIZ_PATTERN = re.compile(
    r"(?:"
    r"\bWhat\s+is\s+the\s+doctrine\s+of\s+\w+|"
    r"\bDefine\s+(?:the\s+)?(?:doctrine|principle|concept)\s+of\s+\w+|"
    r"\bWhich\s+(?:doctrine|heresy)\s+(?:teaches|holds|claims|denies|denied)|"
    r"\bWhat\s+does\s+the\s+(?:doctrine|principle|concept)\s+of\s+\w+\s+(?:teach|hold|claim|argue|mean)\??|"
    r"\bWhat\s+is\s+meant\s+by\s+(?:the\s+doctrine\s+of\s+)?[A-Z]\w+(?:ianism|ology|ism)\??$"
    r")",
    re.IGNORECASE,
)

# Allow if the stem grounds the doctrine in a named figure/event/year
DOCTRINE_GROUNDED_HINTS = re.compile(
    r"\b(?:"
    # Named historical events / councils
    r"Nicaea|Chalcedon|Trent|Vatican|Worms|Augsburg|Constantinople|"
    # Named figures (sampling — common ones)
    r"Athanasius|Arius|Augustine|Aquinas|Luther|Calvin|Wesley|Knox|"
    r"Polycarp|Sebastian|Lawrence|Joan|Francis|Becket|Patrick|George|"
    r"Tetzel|Erasmus|More|Cranmer|Latimer|Ridley|"
    # Year + AD/CE/BC
    r"\b\d{3,4}\s*(?:AD|CE|BC|BCE)?\b|"
    # Specific dramatic moments
    r"95\s+theses|Diet\s+of|stake|burned\s+alive|martyr"
    r")",
    re.IGNORECASE,
)


def gate_no_doctrine_quizzing(q: dict) -> Optional[str]:
    """Hard-reject doctrine-recall stems with no named-figure/event
    grounding. Doctrine is allowed only when tied to a specific dramatic
    moment with named participants.
    """
    stem = q.get("question", "") or ""
    m = DOCTRINE_QUIZ_PATTERN.search(stem)
    if not m:
        return None
    # Grounded by named figure or event in stem/answer/context
    full = stem + " " + (q.get("answer", "") or "") + " " + (q.get("context", "") or "")
    if DOCTRINE_GROUNDED_HINTS.search(full):
        return None
    return (
        f"no_doctrine_quizzing: stem reads as doctrine-quiz with no named "
        f"figure/event grounding: {m.group(0)!r} — rewrite to STORY"
    )


# --------------------------------------------------------------------------
# Gate: no_author_attribution (HARD)
# --------------------------------------------------------------------------

# "Who wrote the Iliad?" / "Who said 'Here I stand'?" / "Who composed
# the Edda?" — banned. The kid should learn the STORY behind the moment,
# not be tested on citation/authorship.
AUTHOR_ATTRIBUTION_PATTERN = re.compile(
    r"(?:"
    r"\bWho\s+(?:wrote|authored|composed|penned)\s+(?:the\s+)?[A-Z]?\w+|"
    r"\bWho\s+said\s+[\"'][^\"']+[\"']|"
    r"\bWho\s+is\s+the\s+author\s+of\b|"
    r"\bWhose\s+(?:book|gospel|letter|epistle|essay|treatise|work|saga|edda)\s+(?:contains|describes|tells)|"
    r"\bWhich\s+(?:apostle|gospel|prophet|saint)\s+wrote\b|"
    r"\bWhich\s+(?:author|writer|poet|scribe)\s+(?:wrote|composed|recorded)\b"
    r")",
    re.IGNORECASE,
)


def gate_no_author_attribution(q: dict) -> Optional[str]:
    """Hard-reject author-attribution stems. The bank teaches STORIES,
    not citation/authorship recall.

    Edge cases allowed (don't trigger):
    - "Who killed Goliath?" — STORY question (not author)
    - "Who was the giant Hercules wrestled?" — STORY question
    - "Who was Polycarp?" — biographical, not author-attribution
    The regex targets WROTE/SAID/COMPOSED specifically.
    """
    stem = q.get("question", "") or ""
    m = AUTHOR_ATTRIBUTION_PATTERN.search(stem)
    if not m:
        return None
    return (
        f"no_author_attribution: stem asks for authorship/citation: "
        f"{m.group(0)!r} — rewrite to STORY (what happened, what was said, "
        f"what was done) rather than WHO WROTE/COMPOSED/CITED"
    )


# --------------------------------------------------------------------------
# Gate: no_above_grade10_theology (HARD)
# --------------------------------------------------------------------------

# Research-paper theology jargon. T5 stays grade 9-10 — story-anchored
# vocabulary is fine (Eucharist, baptism, communion, the cross,
# transubstantiation when tied to a named council are OK in context).
# These tokens are college / graduate seminary level and have no
# story-grounded use in this bank.
ABOVE_GRADE_10_THEOLOGY_TOKENS = re.compile(
    r"\b(?:"
    r"supralapsarianism|sublapsarianism|infralapsarianism|"
    r"perichoresis|"
    r"filioque(?:\s+clause)?|"
    r"kenosis|kenotic\s+theology|"
    r"theosis(?:\s+as\s+(?:theological\s+)?(?:term|doctrine|process))|"
    r"hypostatic\s+union\s+as\s+(?:doctrine|academic|theological\s+problem)|"
    r"homoousios|homoiousios|"
    r"monothelitism|dyothelitism|"
    r"monophysitism|dyophysitism|"
    r"Nestorianism\s+as\s+(?:abstract\s+)?(?:doctrine|theology)|"
    r"apollinarianism|"
    r"Pelagianism\s+(?:as\s+abstract|in\s+the\s+abstract)|"
    r"semi[- ]?Pelagianism|"
    r"Molinism|"
    r"impassibility(?:\s+of\s+God)?|"
    r"aseity|"
    r"divine\s+simplicity\s+as\s+doctrine|"
    r"actus\s+purus|"
    r"esse[- ]?essentia\s+distinction|"
    r"hermeneutical\s+circle|"
    r"sitz[- ]?im[- ]?leben|"
    r"redaction\s+criticism\s+method|"
    r"form\s+criticism\s+as\s+method"
    r")\b",
    re.IGNORECASE,
)


def gate_no_above_grade10_theology(q: dict) -> Optional[str]:
    """Hard-reject content using upper-undergraduate / seminary theology
    terminology. T5 stays grade 9-10 — story-grounded vocabulary only.
    """
    haystacks = [
        q.get("question", "") or "",
        q.get("answer", "") or "",
        q.get("context", "") or "",
    ] + [c if isinstance(c, str) else "" for c in q.get("choices", []) or []]
    for h in haystacks:
        m = ABOVE_GRADE_10_THEOLOGY_TOKENS.search(h)
        if m:
            return (
                f"no_above_grade10_theology: contains above-grade-10 token "
                f"{m.group(0)!r} — see THEOLOGY_FRAMEWORK §3 grade-10 ceiling"
            )
    return None


# --------------------------------------------------------------------------
# Gate: no_smug_voice (SOFT-WARN)
# --------------------------------------------------------------------------

# Per moral_vision.md: no smug atheist voice + no smug believer voice.
# The bank presents all stories with respect.
SMUG_VOICE_PATTERN = re.compile(
    r"\b(?:"
    # Smug atheist
    r"ancient\s+peoples?\s+(?:ignorantly|naively|foolishly|superstitiously)\s+believed|"
    r"(?:primitive|backward|pre[- ]?scientific)\s+(?:peoples?|cultures?|minds?)\s+(?:imagined|invented|made\s+up)|"
    r"(?:silly|absurd|laughable|childish)\s+(?:myth|belief|superstition|tale)|"
    r"sky[- ]?(?:god|fairy|wizard)|"
    r"bronze\s+age\s+(?:myth|fairy[- ]?tale|nonsense)|"
    # Smug believer
    r"the\s+false\s+(?:gods?|idols?|religions?)\s+of\b|"
    r"(?:pagan|heathen)\s+(?:superstition|nonsense|error)|"
    r"(?:demonic|satanic)\s+(?:deception|origin)|"
    r"the\s+true\s+God\s+(?:alone\s+)?(?:as\s+opposed\s+to|unlike|versus)|"
    r"the\s+one\s+true\s+(?:faith|religion|God)\s+(?:as\s+opposed\s+to|alone|versus)"
    r")",
    re.IGNORECASE,
)


def gate_no_smug_voice(q: dict) -> Optional[str]:
    """SOFT-warn for either smug-atheist or smug-believer framing. Per
    moral_vision.md and THEOLOGY_FRAMEWORK §5: all stories told straight
    with full dramatic seriousness; no truth-claim hierarchy between
    traditions; no condescension toward any tradition.
    """
    text_parts = [
        ("stem", q.get("question", "") or ""),
        ("answer", q.get("answer", "") or ""),
        ("context", q.get("context", "") or ""),
    ] + [(f"choice-{i}", c) for i, c in enumerate(q.get("choices", []) or []) if isinstance(c, str)]
    for label, text in text_parts:
        m = SMUG_VOICE_PATTERN.search(text)
        if m:
            return (
                f"soft-warn: no_smug_voice: {label} contains smug "
                f"atheist/believer framing: {m.group(0)!r}"
            )
    return None


# --------------------------------------------------------------------------
# Gate: no_modern_cult_content (HARD)
# --------------------------------------------------------------------------

# Modern cult-abuse content belongs in history/current-events, not
# mythological-heritage storytelling.
MODERN_CULT_PATTERN = re.compile(
    r"\b(?:"
    r"Jim\s+Jones|Jonestown|People'?s\s+Temple|"
    r"Heaven'?s\s+Gate|Marshall\s+Applewhite|"
    r"Aum\s+Shinrikyo|Shoko\s+Asahara|"
    r"David\s+Koresh|Branch\s+Davidian|Waco\s+siege|"
    r"Order\s+of\s+the\s+Solar\s+Temple|"
    r"Scientology|L\.\s*Ron\s+Hubbard|"
    r"Children\s+of\s+God|Family\s+International|"
    r"NXIVM|Keith\s+Raniere|"
    r"Rajneesh(?:eepuram|i)?|Osho(?:'?s\s+cult)?"
    r")\b",
    re.IGNORECASE,
)


def gate_no_modern_cult_content(q: dict) -> Optional[str]:
    """Hard-reject modern-cult-abuse content. Out of scope for this bank.
    Per THEOLOGY_FRAMEWORK §6 (deliberate omissions).
    """
    haystacks = [
        q.get("question", "") or "",
        q.get("answer", "") or "",
        q.get("context", "") or "",
    ] + [c if isinstance(c, str) else "" for c in q.get("choices", []) or []]
    for h in haystacks:
        m = MODERN_CULT_PATTERN.search(h)
        if m:
            return (
                f"no_modern_cult_content: contains modern-cult reference "
                f"{m.group(0)!r} — out of scope for theology bank "
                f"(see THEOLOGY_FRAMEWORK §6)"
            )
    return None


# --------------------------------------------------------------------------
# Gate registry
# --------------------------------------------------------------------------

SOFT_WARN_GATES: frozenset[str] = frozenset({
    "no_smug_voice",
})


PER_QUESTION_GATES: list[tuple[str, Callable[[dict], Optional[str]]]] = [
    ("schema", gate_schema),
    ("choice_shape_parity", gate_choice_shape_parity),
    ("context_no_meta_references", gate_context_no_meta_references),
    ("no_doctrine_quizzing", gate_no_doctrine_quizzing),
    ("no_author_attribution", gate_no_author_attribution),
    ("no_above_grade10_theology", gate_no_above_grade10_theology),
    ("no_modern_cult_content", gate_no_modern_cult_content),
    # Soft-warn
    ("no_smug_voice", gate_no_smug_voice),
]


def run_gates(q: dict) -> dict[str, Optional[str]]:
    return {name: fn(q) for name, fn in PER_QUESTION_GATES}


__all__ = [
    "PER_QUESTION_GATES",
    "SOFT_WARN_GATES",
    "run_gates",
    "gate_schema",
    "gate_no_doctrine_quizzing",
    "gate_no_author_attribution",
    "gate_no_above_grade10_theology",
    "gate_no_smug_voice",
    "gate_no_modern_cult_content",
    "TIER_CAPS",
]
