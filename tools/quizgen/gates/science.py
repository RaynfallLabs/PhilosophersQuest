"""Science bank structural gates.

The science bank has its own distinctive voice — see
`proposals/v2_audit/SCIENCE_FRAMEWORK.md` (the Discovery Pattern) and
`docs/quiz/subjects/science.md` (the canonical stance reference). This
module exposes the per-question gates that enforce the framework.

Reuses subject-agnostic gates from `tools.quizgen.gates.philosophy`
(schema, choice_shape_parity, context_no_meta_references). Adds six
science-specific gates:

  - no_pseudoscience          (HARD) — fabricated/woo claims (orgone,
                                     free energy machines, etc.) blocked
                                     in *answer* position. Historical
                                     pseudoscience (phlogiston, humors)
                                     allowed as wrong answers/context.
  - no_trust_the_science      (SOFT) — "settled science", "scientists
                                     agree", "consensus has determined"
                                     bare framings on contested topics
                                     flagged
  - no_fabricated_studies     (HARD) — invented journal names, fake
                                     publication dates, etc. blocked
  - no_anthropomorphizing_nature (SOFT) — "evolution wants/decides",
                                     "the universe wants", "atoms
                                     prefer" without scare quotes
                                     flagged
  - no_above_grade10_science  (HARD) — upper-undergraduate vocabulary
                                     (PDEs, Hilbert spaces, gauge
                                     theory, etc.) blocked at T5
  - no_anti_dissent_slurs     (HARD) — "denier", "anti-vaxxer",
                                     "conspiracy theorist" bare framings
                                     blocked as choice/stem text
"""
from __future__ import annotations

import re
from typing import Callable, Optional

from tools.quizgen.gates.philosophy import (
    gate_choice_shape_parity,
    gate_context_no_meta_references,
)


# Per-tier total budgets (stem + 4 choices) — informational
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
# Gate: no_pseudoscience (HARD)
# --------------------------------------------------------------------------

# Modern pseudoscience claims that should not appear as the CORRECT answer.
# Historical pseudoscience (phlogiston, four humors, phrenology) is allowed
# as wrong-answer / context content because covering the historical reversal
# IS one of the bank's purposes. The gate specifically catches modern
# pseudoscience appearing as if it were established science.
PSEUDOSCIENCE_AS_ANSWER_PATTERNS = re.compile(
    r"\b(?:"
    r"orgone\s+energy|"
    r"free[- ]?energy\s+(?:machine|device|generator)|"
    r"perpetual\s+motion(?:\s+machine)?|"
    r"homeopathy\s+(?:works?|cures?|treats?)|"
    r"crystals?\s+(?:heal|cure|emit\s+healing)|"
    r"water\s+memory|"
    r"chemtrails?\s+(?:are|exist|spray)|"
    r"flat[- ]?earth|"
    r"vaccines?\s+cause\s+autism|"  # Wakefield was retracted
    r"5G\s+(?:causes?|spreads?)\s+(?:covid|coronavirus|disease)|"
    r"reiki\s+(?:heals?|works?)|"
    r"chakras?\s+(?:emit|control|govern)\s+(?:physical|biological)|"
    r"astrology\s+(?:predicts?|determines?|controls?)"
    r")\b",
    re.IGNORECASE,
)


def gate_no_pseudoscience(q: dict) -> Optional[str]:
    """Hard-reject when modern pseudoscience appears as the correct answer.
    Historical pseudoscience as wrong-answer or in context is fine — covering
    those reversals is part of the bank's pedagogical purpose.
    """
    answer = q.get("answer", "") or ""
    m = PSEUDOSCIENCE_AS_ANSWER_PATTERNS.search(answer)
    if m:
        return (
            f"no_pseudoscience: correct answer contains modern pseudoscience "
            f"claim {m.group(0)!r} — historical pseudoscience belongs in "
            f"wrong-answer or context, not the correct answer"
        )
    # Also catch in stem when phrased as established fact (not as the claim
    # being examined). The marker is "is/are" without scare quotes or "claims"/
    # "argues"/"says".
    stem = q.get("question", "") or ""
    m = PSEUDOSCIENCE_AS_ANSWER_PATTERNS.search(stem)
    if m:
        # Allow if stem clearly frames the claim as something being examined
        # rather than stated as fact.
        framing_markers = [
            "claims", "claim that", "argues", "argued",
            "says", "said", "asserts", "asserted",
            "believes", "believed", "alleges", "alleged",
            "the idea that", "the theory that", "the notion that",
            "proponents", "supporters", "advocates",
            "discredited", "rejected", "fringe",
            "scare quote", "in quotes",
        ]
        stem_l = stem.lower()
        if not any(marker in stem_l for marker in framing_markers):
            # Also accept if the match is inside quotes
            idx = m.start()
            before = stem[:idx]
            if before.count("'") % 2 == 0 and before.count('"') % 2 == 0:
                return (
                    f"no_pseudoscience: stem states {m.group(0)!r} as "
                    f"established fact — frame as claim/idea being examined "
                    f"or put in quotes"
                )
    return None


# --------------------------------------------------------------------------
# Gate: no_trust_the_science (SOFT-WARN)
# --------------------------------------------------------------------------

TRUST_THE_SCIENCE_PATTERNS = re.compile(
    r"\b(?:"
    r"settled\s+science|"
    r"the\s+science\s+(?:is|has)\s+settled|"
    r"trust\s+the\s+science|"
    r"scientists?\s+(?:all\s+)?agree(?:\s+that)?|"
    r"consensus\s+(?:has\s+)?determined|"
    r"undisputed\s+scientific\s+fact|"
    r"there'?s?\s+no\s+(?:scientific|legitimate)\s+(?:debate|dispute|controversy)|"
    r"the\s+science\s+(?:tells\s+us|shows\s+us|proves)"
    r")\b",
    re.IGNORECASE,
)


def gate_no_trust_the_science(q: dict) -> Optional[str]:
    """SOFT-warn when 'settled science' / 'scientists agree' / 'trust the
    science' framings appear as bare assertion. The bank takes positions
    where evidence + history justify them and rejects the establishment-
    default voice these phrases encode.

    Allowed:
      - In quotes (citing someone using the phrase)
      - When followed by a critique ("'trust the science' became a slogan")
      - In context discussing the slogan as a phenomenon
    """
    stem = q.get("question", "") or ""
    answer = q.get("answer", "") or ""
    choices = q.get("choices", []) or []
    for label, text in [("stem", stem), ("answer", answer)] + \
                       [(f"choice-{i}", c) for i, c in enumerate(choices) if isinstance(c, str)]:
        m = TRUST_THE_SCIENCE_PATTERNS.search(text)
        if not m:
            continue
        # Exempt if inside quotes
        idx = m.start()
        before = text[:idx]
        if before.count("'") % 2 == 1 or before.count('"') % 2 == 1:
            continue
        # Exempt if surrounding context critiques the phrase
        text_l = text.lower()
        if any(k in text_l for k in [
            "slogan", "propaganda", "became a", "as if", "in fact",
            "in reality", "actually", "however", "but the",
            "until", "later turned out", "was wrong", "was overturned",
        ]):
            continue
        return (
            f"soft-warn: no_trust_the_science: {label} uses establishment-"
            f"default framing {m.group(0)!r} — bank takes positions, doesn't "
            f"defer to 'consensus' on contested topics"
        )
    return None


# --------------------------------------------------------------------------
# Gate: no_fabricated_studies (HARD)
# --------------------------------------------------------------------------

# Heuristic: if the text cites a journal name, the journal name should be
# real. This is a conservative gate — it catches obvious fabrications like
# "Journal of Quantum Biology Research" while letting real journals pass.
KNOWN_REAL_JOURNALS = {
    "nature", "science", "cell", "the lancet", "lancet", "nejm",
    "new england journal of medicine", "jama", "bmj", "plos one",
    "plos medicine", "plos biology", "pnas", "proceedings of the national",
    "physical review", "physical review letters", "physical review d",
    "prl", "prd", "prb", "astrophysical journal", "monthly notices",
    "icarus", "astronomy and astrophysics", "annalen der physik",
    "philosophical transactions", "scientific american", "current biology",
    "molecular biology and evolution", "genetics", "genome research",
    "nucleic acids research", "annual review", "trends in",
    "advances in", "journal of climate", "geophysical research letters",
    "journal of geophysical research", "atmospheric chemistry and physics",
    "energy and environment", "epidemiology", "international journal of epidemiology",
    "cochrane database", "cochrane review", "vaccine", "clinical infectious diseases",
    "lancet planetary health", "lancet infectious diseases",
    "nejm catalyst", "annals of internal medicine",
    "neuron", "brain", "lancet psychiatry", "psychological science",
    "journal of personality and social psychology", "child development",
    "pediatrics", "jama pediatrics", "european journal of",
    "british journal of", "american journal of", "review of",
    "annual reviews", "reviews of modern physics", "annals of physics",
    "physical biology", "chaos", "complexity",
    "plos medicine",
}

JOURNAL_CITATION_PATTERN = re.compile(
    # Catches phrases like "published in the Journal of X" where the journal
    # name is multi-word Title Case. Case-sensitive on the journal-name
    # capture so generic phrases like "in a top journal" don't false-match.
    r"(?:[Pp]ublished\s+in|[Pp]aper\s+in|[Ss]tudy\s+in|[Aa]ppeared\s+in)\s+(?:the\s+)?"
    r"(?:Journal\s+of\s+|Annals?\s+of\s+|Review\s+of\s+|Proceedings\s+of\s+|"
    r"Bulletin\s+of\s+|Archives\s+of\s+|Transactions\s+of\s+)?"
    r"((?:[A-Z][\w&]*\s+){1,5}[A-Z][\w&]*)",
)


def gate_no_fabricated_studies(q: dict) -> Optional[str]:
    """Hard-reject obvious fabricated journal citations. Conservative — only
    flags when the cited journal is clearly not real (e.g., 'Journal of
    Quantum Biology Research'). Real journals + common journals pass.

    Does NOT try to validate specific paper/date pairings — that's the
    LLM fact-check gate's job (which the bank already has in pipeline).
    """
    text = (
        (q.get("question", "") or "") + " " +
        (q.get("answer", "") or "") + " " +
        " ".join(c for c in (q.get("choices", []) or []) if isinstance(c, str)) + " " +
        (q.get("context", "") or "")
    )
    for m in JOURNAL_CITATION_PATTERN.finditer(text):
        candidate = m.group(1).lower().strip()
        # Trim trailing words after the journal name (publishers, dates, etc.)
        candidate_head = " ".join(candidate.split()[:6])
        if any(known in candidate_head or candidate_head in known
               for known in KNOWN_REAL_JOURNALS):
            continue
        # Allow common patterns that aren't journal names
        if any(kw in candidate_head for kw in [
            "the new york times", "wall street journal", "washington post",
            "the times", "the guardian", "the telegraph", "atlantic",
            "scientific american", "new scientist", "discover magazine",
            "ars technica", "the verge", "techcrunch", "wired",
            "associated press", "reuters", "bbc", "npr",
        ]):
            continue
        # If it's a tail of a multi-word match, allow
        if len(candidate_head.split()) <= 2:
            continue
        return (
            f"no_fabricated_studies: cites apparently-unknown journal "
            f"{m.group(1)!r} — use real journals only"
        )
    return None


# --------------------------------------------------------------------------
# Gate: no_anthropomorphizing_nature (SOFT-WARN)
# --------------------------------------------------------------------------

ANTHROPOMORPHIZE_NATURE_PATTERN = re.compile(
    r"\b(?:"
    r"(?:evolution|nature|the universe|natural selection)\s+(?:wants?|decides?|chose|chooses|prefers?|believes?|knows?|thinks?|hates?|loves?|fears?)|"
    r"atoms?\s+(?:want|decide|choose|prefer|know)|"
    r"electrons?\s+(?:want|decide|choose|know)|"
    r"genes?\s+(?:want|try|decide)|"
    r"species\s+(?:want|decide|chose|tries?|trying)|"
    r"(?:DNA|RNA)\s+(?:wants?|decides?|knows?)"
    r")\b",
    re.IGNORECASE,
)


def gate_no_anthropomorphizing_nature(q: dict) -> Optional[str]:
    """SOFT-warn when natural processes are described with intentional verbs
    (wants, decides, prefers) without scare quotes or framing. Distinct from
    the AI bank's anthropomorphizing gate.

    Exempt if inside quotes, or surrounding context names the framing
    ('as if', 'we say', 'metaphorically').
    """
    stem = q.get("question", "") or ""
    answer = q.get("answer", "") or ""
    choices = q.get("choices", []) or []
    context = q.get("context", "") or ""
    for label, text in [("stem", stem), ("answer", answer), ("context", context)] + \
                       [(f"choice-{i}", c) for i, c in enumerate(choices) if isinstance(c, str)]:
        m = ANTHROPOMORPHIZE_NATURE_PATTERN.search(text)
        if not m:
            continue
        idx = m.start()
        before = text[:idx]
        if before.count("'") % 2 == 1 or before.count('"') % 2 == 1:
            continue
        text_l = text.lower()
        if any(k in text_l for k in [
            "as if", "we say", "loosely speaking", "metaphor",
            "anthropomorph", "in shorthand", "scare quote",
            "not actually", "doesn't really", "isn't really",
            "shorthand for",
        ]):
            continue
        return (
            f"soft-warn: no_anthropomorphizing_nature: {label} attributes "
            f"intent to nature: {m.group(0)!r}"
        )
    return None


# --------------------------------------------------------------------------
# Gate: no_above_grade10_science (HARD)
# --------------------------------------------------------------------------

ABOVE_GRADE_10_SCIENCE_TOKENS = re.compile(
    r"\b(?:"
    # Math machinery above grade 10
    r"partial\s+differential\s+equation|PDE|"
    r"ordinary\s+differential\s+equation|"
    r"Hilbert\s+space|"
    r"Banach\s+space|"
    r"Lagrangian\s+(?:mechanics|formulation|density)|"
    r"Hamiltonian\s+(?:mechanics|formalism)|"
    r"path\s+integral\s+formulation|"
    r"gauge\s+theory|"
    r"gauge\s+invariance|"
    r"non[- ]?abelian\s+gauge|"
    r"Yang[- ]?Mills|"
    r"tensor\s+(?:calculus|field)|"
    r"Riemannian\s+(?:manifold|geometry)|"
    r"variational\s+(?:calculus|principle)|"
    r"Fourier\s+(?:transform|series)|"
    # Stat/probability above grade 10
    r"Bayesian\s+(?:inference|posterior|prior\s+distribution)|"
    r"Kullback[- ]?Leibler\s+divergence|KL\s+divergence|"
    r"Markov\s+chain\s+Monte\s+Carlo|MCMC|"
    r"Hamiltonian\s+Monte\s+Carlo|"
    r"Bonferroni\s+correction|"
    r"hierarchical\s+linear\s+model(?:ling|ing)?|"
    # Chemistry above grade 10
    r"Hartree[- ]?Fock|"
    r"density\s+functional\s+theory|DFT|"
    r"molecular\s+orbital\s+theory|"
    r"Schrodinger\s+equation\s+for(?:\s+the\s+molecule)?|"
    r"basis\s+set|"
    # Biology above grade 10
    r"Hamilton[''']?s\s+rule|inclusive\s+fitness\s+coefficient|"
    r"Wright[- ]?Fisher\s+model|"
    r"coalescent\s+theory|"
    # Other research-level terms
    r"renormalization\s+group|"
    r"spontaneous\s+symmetry\s+breaking|"
    r"effective\s+field\s+theory|"
    r"asymptotic\s+freedom|"
    r"conformal\s+field\s+theory|"
    r"supersymmetry|SUSY"
    r")\b",
    re.IGNORECASE,
)


def gate_no_above_grade10_science(q: dict) -> Optional[str]:
    """Hard-reject content using upper-undergraduate / research-level
    terminology. T5 stays at grade 9-10 — mechanism explanations a
    paragraph can convey, real-world cases, named figures.
    """
    haystacks = [
        q.get("question", "") or "",
        q.get("answer", "") or "",
        q.get("context", "") or "",
    ] + [c if isinstance(c, str) else "" for c in q.get("choices", []) or []]
    for h in haystacks:
        m = ABOVE_GRADE_10_SCIENCE_TOKENS.search(h)
        if m:
            return (
                f"no_above_grade10_science: contains above-grade-10 token "
                f"{m.group(0)!r} — see SCIENCE_FRAMEWORK §2 grade-10 ceiling"
            )
    return None


# --------------------------------------------------------------------------
# Gate: no_anti_dissent_slurs (HARD)
# --------------------------------------------------------------------------

# Slurs used to dismiss scientific dissent. Allowed in context ONLY when
# discussing the term itself (e.g., "Collins called them 'fringe'").
ANTI_DISSENT_SLURS = re.compile(
    r"\b(?:"
    r"climate\s+denier|"
    r"covid\s+denier|"
    r"vaccine\s+denier|"
    r"science\s+denier|"
    r"anti[- ]?vaxxer|"
    r"conspiracy\s+theorist|"
    r"flat[- ]?earther(?!s?\s+(?:claim|believe|say))|"  # allow context naming the label
    r"truther|"
    r"plandemic\s+(?:believer|theorist)"
    r")\b",
    re.IGNORECASE,
)


def gate_no_anti_dissent_slurs(q: dict) -> Optional[str]:
    """Hard-reject anti-dissent slurs in stem/answer/choices. These are
    propaganda terms used to dismiss scientific dissent rather than
    engage with it; the bank does not use them as bare framings.

    Allowed in context when naming the label as something OTHERS used:
    'Collins called the Great Barrington Declaration authors "fringe"'.
    """
    stem = q.get("question", "") or ""
    answer = q.get("answer", "") or ""
    choices = q.get("choices", []) or []
    context = q.get("context", "") or ""

    for label, text in [("stem", stem), ("answer", answer)] + \
                       [(f"choice-{i}", c) for i, c in enumerate(choices) if isinstance(c, str)]:
        m = ANTI_DISSENT_SLURS.search(text)
        if not m:
            continue
        idx = m.start()
        before = text[:idx]
        # Exempt if inside quotes
        if before.count("'") % 2 == 1 or before.count('"') % 2 == 1:
            continue
        # Exempt if context names who used the label
        if any(k in text.lower() for k in [
            "called them", "labeled them", "branded them", "dismissed as",
            "labeled as", "the slur", "the term", "the label", "smeared as",
        ]):
            continue
        return (
            f"no_anti_dissent_slurs: {label} uses propaganda slur "
            f"{m.group(0)!r} — substantive description instead, or name "
            f"who used the label"
        )
    # Context is allowed to use slurs when naming the labeling
    return None


# --------------------------------------------------------------------------
# Gate registry
# --------------------------------------------------------------------------

SOFT_WARN_GATES: frozenset[str] = frozenset({
    "no_trust_the_science",
    "no_anthropomorphizing_nature",
})


PER_QUESTION_GATES: list[tuple[str, Callable[[dict], Optional[str]]]] = [
    # Hard-reject
    ("schema", gate_schema),
    ("choice_shape_parity", gate_choice_shape_parity),
    ("context_no_meta_references", gate_context_no_meta_references),
    ("no_pseudoscience", gate_no_pseudoscience),
    ("no_fabricated_studies", gate_no_fabricated_studies),
    ("no_above_grade10_science", gate_no_above_grade10_science),
    ("no_anti_dissent_slurs", gate_no_anti_dissent_slurs),
    # Soft-warn
    ("no_trust_the_science", gate_no_trust_the_science),
    ("no_anthropomorphizing_nature", gate_no_anthropomorphizing_nature),
]


def run_gates(q: dict) -> dict[str, Optional[str]]:
    return {name: fn(q) for name, fn in PER_QUESTION_GATES}


__all__ = [
    "PER_QUESTION_GATES",
    "SOFT_WARN_GATES",
    "run_gates",
    "gate_schema",
    "gate_no_pseudoscience",
    "gate_no_trust_the_science",
    "gate_no_fabricated_studies",
    "gate_no_anthropomorphizing_nature",
    "gate_no_above_grade10_science",
    "gate_no_anti_dissent_slurs",
    "TIER_CAPS",
]
