"""Grammar bank structural gates.

Grammar is fundamentally different from the wonder subjects (history,
philosophy, cooking, animal, geography) — see
`proposals/v2_audit/GRAMMAR_FRAMEWORK.md` for the voice rules. This
module exposes the per-question gates that enforce the framework.

Two layers, same shape as the other subjects:

  - Reuse subject-agnostic gates from `tools.quizgen.gates.philosophy`
    where they apply (schema, choice_shape_parity).

  - Add grammar-specific gates:
      * vocab_teaching_at_t13     (HARD) — T1–T3 stems naming a category
                                          must show by example or define
                                          in context
      * tier_concept_appropriate  (HARD) — concepts at-or-below the grade
                                          band for the tier
      * no_above_grade10          (HARD) — Chomsky/Saussure/etc. banned
                                          per the 2026-05-19 audit
      * no_fake_etymology         (HARD) — known-false folk etymologies
                                          banned
      * example_sentence_quoted   (SOFT) — "this sentence" references
                                          should be in quotes

Per GRAMMAR_FRAMEWORK.md §7 — grammar SKIPS: anti_rote (exempt per
moral_vision.md), answer_collision (exempt per answer_collision.py),
wonder_bias_check, drama_available, no_verdict_on_contested,
scenario_anchored_correct, history_named_anchor, place_anchor_check,
forcing_constraint, subject_named.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable, Optional

# Reuse the subject-agnostic gates from philosophy's module.
from tools.quizgen.gates.philosophy import (
    gate_choice_shape_parity,
    gate_context_no_meta_references,
    _content_tokens,
)


# Per-tier total budgets (stem + 4 choices) — informational; the
# pipeline-level validate_length_budget enforces them via
# SUBJECT_TIER_BUDGETS["grammar"] in deterministic/length_budget.py.
TIER_CAPS = {1: 600, 2: 700, 3: 750, 4: 950, 5: 1000}


# --------------------------------------------------------------------------
# Schema (re-defined here so the gate set is self-contained at the call site)
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
# Gate: above-grade-10 ban
# --------------------------------------------------------------------------

ABOVE_GRADE_10_TOKENS = re.compile(
    r"\b(?:"
    r"Chomsky|Chomskyan|"
    r"Saussure|Saussurean|"
    r"Sapir(?:-?Whorf)?|Whorf(?:ian)?|"
    r"Bloomfield(?:ian)?|"
    r"P[aā]nini(?:'?s)?|A[sś][tṭ][aā]dhy[aā]y[iī]|"
    r"transformational[\s-]?grammar|generative[\s-]?(?:syntax|grammar)|"
    r"deep[\s-]?structure|surface[\s-]?structure|"
    r"morphosyntax|morphosyntactic|"
    r"phonological[\s-]?theory|"
    r"evidentiality[\s-]?(?:typology|marker)|"
    r"verb[\s-]?valency|avalent|monovalent|divalent|trivalent|"
    r"critical[\s-]?period[\s-]?hypothesis|"
    r"universal[\s-]?grammar|"
    r"government[\s-]?and[\s-]?binding|"
    r"X[\s-]?bar[\s-]?theory|"
    r"minimalist[\s-]?program"
    r")\b",
    re.IGNORECASE,
)


def gate_no_above_grade10(q: dict) -> Optional[str]:
    """Hard-reject content that's above the grade-10 ceiling per the
    2026-05-19 audit. These tokens are in stem, answer, choices, OR context.
    """
    stem = q.get("question", "") or ""
    answer = q.get("answer", "") or ""
    choices = q.get("choices", []) or []
    context = q.get("context", "") or ""
    haystacks = [stem, answer, context] + [c if isinstance(c, str) else "" for c in choices]
    for h in haystacks:
        m = ABOVE_GRADE_10_TOKENS.search(h)
        if m:
            return (
                f"no_above_grade10: contains above-grade-10 linguistics term "
                f"{m.group(0)!r} — see GRAMMAR_FRAMEWORK §2"
            )
    return None


# --------------------------------------------------------------------------
# Gate: fake-etymology ban
# --------------------------------------------------------------------------

# Known folk-etymology myths (the FALSE explanation). If the question's
# CORRECT answer or context endorses one of these, it's a hard fail.
# These don't appear in stems often — they appear in answers/context that
# claim the false origin as the truth. We match on the false-origin
# phrasing.
FAKE_ETYMOLOGY_PATTERNS = re.compile(
    r"\b(?:"
    r"rule of thumb.{0,80}wife.?beat|"      # "rule of thumb" wife-beating myth
    r"wife.?beat.{0,40}rule of thumb|"
    r"OK.{0,40}(?:all\s+correct|oll?\s+korrect)|"  # OK = "all correct" backronym
    r"\bSOS.{0,40}save\s+our\s+souls|"       # SOS as "save our souls" origin
    r"tip.{0,60}to\s+insure\s+prompt|"       # TIP = "to insure promptness"
    r"to\s+insure\s+prompt.{0,40}tip\b|"
    r"posh.{0,60}port\s+out\s+starboard\s+home|"  # POSH backronym
    r"port\s+out\s+starboard\s+home.{0,40}posh|"
    r"sincere.{0,60}(?:sine\s+cera|without\s+wax)|"  # sincere = "without wax"
    r"without\s+wax.{0,40}sincere|"
    r"golf.{0,80}gentlemen\s+only.{0,40}ladies\s+forbidden|"
    r"news.{0,60}north\s+east\s+west\s+south"  # NEWS backronym
    r")\b",
    re.IGNORECASE | re.DOTALL,
)


def gate_no_fake_etymology(q: dict) -> Optional[str]:
    """Hard-reject if the correct answer or context endorses a known
    folk-etymology myth. Doesn't fire if a fake etymology appears as a
    DISTRACTOR (testing for awareness of the myth is valid)."""
    answer = q.get("answer", "") or ""
    context = q.get("context", "") or ""
    for text, label in ((answer, "answer"), (context, "context")):
        m = FAKE_ETYMOLOGY_PATTERNS.search(text)
        if m:
            return (
                f"no_fake_etymology: {label} appears to endorse a known "
                f"folk-etymology myth: {m.group(0)[:60]!r}"
            )
    return None


# --------------------------------------------------------------------------
# Gate: vocab-teaching invariant at T1–T3
# --------------------------------------------------------------------------

# Grammatical category nouns. If a stem mentions one of these AND the tier
# is 1–3, the question must include an example sentence (quoted) OR define
# the term in the context field.
GRAMMATICAL_CATEGORY_TERMS = re.compile(
    r"\b(?:"
    r"noun(?:s|al)?|verb(?:s|al)?|adjective(?:s|al)?|adverb(?:s|ial)?|"
    r"pronoun(?:s|al)?|preposition(?:s|al)?|conjunction(?:s|al)?|interjection(?:s)?|"
    r"article(?:s)?|determiner(?:s)?|"
    r"subject(?:s)?|predicate(?:s)?|object(?:s)?|complement(?:s)?|modifier(?:s)?|"
    r"clause(?:s)?|phrase(?:s)?|"
    r"tense(?:s)?|aspect(?:s)?|mood(?:s)?|voice(?:s)?|"
    r"participle(?:s)?|gerund(?:s)?|infinitive(?:s)?|"
    r"appositive(?:s)?|relative\s+clause|"
    r"dependent\s+clause|independent\s+clause|subordinate\s+clause|"
    r"subjunctive|imperative|indicative|"
    r"transitive|intransitive|"
    r"possessive|reflexive|demonstrative|interrogative|"
    r"comparative|superlative|"
    r"metaphor|simile|personification|hyperbole|alliteration|onomatopoeia|"
    r"metonymy|synecdoche|oxymoron|paradox|"
    r"morpheme|phoneme|syntax|semantics|pragmatics|etymology|lexicon"
    r")\b",
    re.IGNORECASE,
)

# Quoted-text detection — single OR double quotes around any non-empty
# content (catches single quoted words like 'freeze' as legitimate
# examples too).
QUOTED_TEXT_RE = re.compile(
    r"(?:['\"‘“])[^'\"’”\s][^'\"’”]*(?:['\"’”])"
)


def _has_example_in(text: str) -> bool:
    """A text counts as 'showing by example' if it has any quoted token —
    a quoted sentence ('The cat sat on the mat'), a quoted word
    ('freeze'), or a quoted phrase ('Salt of the earth')."""
    return bool(QUOTED_TEXT_RE.search(text or ""))


def _looks_like_example_phrase(text: str) -> bool:
    """Heuristic: text 'is itself an example' when it's multi-word AND has
    one of: comma, apostrophe, em-dash, em/en dash, exclamation, question
    mark, semicolon, or 4+ words. Catches answers like 'Madam, I'm Adam',
    'Kick the bucket', 'By the skin of my teeth'."""
    if not text:
        return False
    if QUOTED_TEXT_RE.search(text):
        return True
    word_count = len(text.split())
    if word_count >= 4:
        return True
    if word_count >= 2 and re.search(r"[,!?;'’—–\-]", text):
        return True
    return False


def gate_vocab_teaching_at_t13(q: dict) -> Optional[str]:
    """At T1–T3, if a stem names a grammatical category, the question must
    teach the category somewhere — by example OR by definition.

    Acceptable teaching paths (ANY one passes):
      A. Quoted text in stem ("In 'The cat sat on the mat,' ...")
      B. Quoted text in any choice
      C. Answer is a multi-word/phrase example (e.g., "Madam, I'm Adam";
         "Kick the bucket"; "By the skin of my teeth")
      D. Any choice looks like an example phrase (multi-word with
         comma/apostrophe/em-dash, or 4+ words)
      E. Context is present and ≥30 chars (any substantive teaching)

    Fires ONLY when the question is bare category-recall: no example
    anywhere AND essentially no context.

    Per GRAMMAR_FRAMEWORK.md §3.
    """
    tier = q.get("tier", 0)
    if tier not in (1, 2, 3):
        return None
    stem = q.get("question", "") or ""
    cat_match = GRAMMATICAL_CATEGORY_TERMS.search(stem)
    if not cat_match:
        return None

    # Path A: quoted text in stem
    if QUOTED_TEXT_RE.search(stem):
        return None

    # Path B: quoted text in any choice
    choices = q.get("choices", []) or []
    if any(isinstance(c, str) and QUOTED_TEXT_RE.search(c) for c in choices):
        return None

    # Path C: answer looks like an example phrase
    answer = q.get("answer", "") or ""
    if _looks_like_example_phrase(answer):
        return None

    # Path D: choices look like example phrases (3+ qualifying)
    example_like_choices = sum(
        1 for c in choices if isinstance(c, str) and _looks_like_example_phrase(c)
    )
    if example_like_choices >= 3:
        return None

    # Path E: substantive context (≥30 chars; this is the floor that
    # distinguishes a teaching question from a bare-recall question)
    context = q.get("context", "") or ""
    if context and len(context.strip()) >= 30:
        return None

    return (
        f"vocab_teaching_at_t13: T{tier} stem names {cat_match.group(0)!r} but "
        f"has no example (stem/answer/choices) AND no substantive context "
        f"(≥30 chars) — pure category-recall without teaching scaffold"
    )


# --------------------------------------------------------------------------
# Gate: tier-concept-appropriate
# --------------------------------------------------------------------------

# Terms that are FINE at T4–T5 but should NOT appear in T1–T3 stems/answers/choices
# (they signal above-grade-band conceptual complexity).
T45_ONLY_TERMS = re.compile(
    r"\b(?:"
    r"subjunctive|epistemic|deontic|polysyndeton|asyndeton|chiasmus|anaphora|"
    r"epistrophe|litotes|antithesis|hyperbaton|isocolon|tricolon|parataxis|"
    r"hypotaxis|zeugma|allusion|"
    r"hypothetical\s+conditional|counterfactual|mandative|"
    r"restrictive\s+(?:clause|modifier)|non-restrictive|"
    r"cleft\s+sentence|"
    r"reported\s+speech|backshifting|"
    r"agentless\s+passive|"
    r"absolute\s+(?:phrase|construction)"
    r")\b",
    re.IGNORECASE,
)

# Terms that are PROHIBITIVE at T5 — too elementary even for context.
T5_TOO_ELEMENTARY = re.compile(
    r"^(?:"
    r"What is a (?:noun|verb|adjective|adverb)\?|"
    r"Which is the (?:noun|verb|adjective|adverb)\b|"
    r"Pick the (?:noun|verb|adjective|adverb)\b"
    r")",
    re.IGNORECASE,
)


def gate_tier_concept_appropriate(q: dict) -> Optional[str]:
    """Flag concepts that don't match the tier's grade band.

    T1–T3 stems should not name T4+ concepts (subjunctive, polysyndeton, etc.).
    T5 stems should not ask elementary parts-of-speech recall.
    """
    tier = q.get("tier", 0)
    stem = q.get("question", "") or ""
    answer = q.get("answer", "") or ""

    if tier in (1, 2, 3):
        for text, label in ((stem, "stem"), (answer, "answer")):
            m = T45_ONLY_TERMS.search(text)
            if m:
                return (
                    f"tier_concept_appropriate: T{tier} {label} names "
                    f"{m.group(0)!r} — an above-grade-band concept; should "
                    f"be at T4 or T5"
                )

    if tier == 5:
        if T5_TOO_ELEMENTARY.match(stem.strip()):
            return (
                f"tier_concept_appropriate: T5 stem is elementary "
                f"parts-of-speech recall — should be at T1 or T2"
            )

    return None


# --------------------------------------------------------------------------
# Gate: example sentence quoted (SOFT-WARN)
# --------------------------------------------------------------------------

# Phrases that strongly imply a specific sentence is being referenced.
SENTENCE_REFERENCE_RE = re.compile(
    r"\b(?:"
    r"(?:this|the\s+following|the\s+given)\s+sentence|"
    r"in\s+the\s+sentence|"
    r"identify.{0,20}\bsentence|"
    r"the\s+underlined\s+word|"
    r"the\s+bold(?:ed)?\s+word"
    r")\b",
    re.IGNORECASE,
)


def gate_example_sentence_quoted(q: dict) -> Optional[str]:
    """SOFT-warn if the stem references a sentence ("in this sentence",
    "the following sentence", "the underlined word") but no quoted text
    is present in the stem.

    The "this sentence" reference pattern requires quoted example text so
    the kid can identify exactly what's being parsed. The gate is soft
    because some stems legitimately reference the choices themselves as
    sentences.
    """
    stem = q.get("question", "") or ""
    if not SENTENCE_REFERENCE_RE.search(stem):
        return None
    # Stem mentions "this sentence" — check for quoted text in the stem
    if QUOTED_TEXT_RE.search(stem):
        return None
    # Check if choices ARE sentences (one being quoted is enough)
    choices = q.get("choices", []) or []
    quoted_choice_count = sum(
        1 for c in choices if isinstance(c, str) and QUOTED_TEXT_RE.search(c)
    )
    # If choices ARE the candidate sentences (the test is "pick the right one"),
    # they don't need to be quoted. Heuristic: if at least 3 of 4 choices are
    # long enough to be sentences (>15 chars with a space), skip the warning.
    sentence_like_choices = sum(
        1 for c in choices if isinstance(c, str) and len(c) > 15 and " " in c
    )
    if sentence_like_choices >= 3:
        return None
    return (
        f"soft-warn: example_sentence_quoted: stem refers to 'this sentence' "
        f"but no quoted example text is present (and choices are not "
        f"sentence-like alternatives)"
    )


# --------------------------------------------------------------------------
# Gate registry
# --------------------------------------------------------------------------

SOFT_WARN_GATES: frozenset[str] = frozenset({
    "example_sentence_quoted",
})

PER_QUESTION_GATES: list[tuple[str, Callable[[dict], Optional[str]]]] = [
    # Hard-reject gates
    ("schema", gate_schema),
    ("choice_shape_parity", gate_choice_shape_parity),
    ("context_no_meta_references", gate_context_no_meta_references),
    ("no_above_grade10", gate_no_above_grade10),
    ("no_fake_etymology", gate_no_fake_etymology),
    ("vocab_teaching_at_t13", gate_vocab_teaching_at_t13),
    ("tier_concept_appropriate", gate_tier_concept_appropriate),
    # Soft-warn gates
    ("example_sentence_quoted", gate_example_sentence_quoted),
]


def run_gates(q: dict) -> dict[str, Optional[str]]:
    return {name: fn(q) for name, fn in PER_QUESTION_GATES}


__all__ = [
    "PER_QUESTION_GATES",
    "SOFT_WARN_GATES",
    "run_gates",
    "gate_schema",
    "gate_no_above_grade10",
    "gate_no_fake_etymology",
    "gate_vocab_teaching_at_t13",
    "gate_tier_concept_appropriate",
    "gate_example_sentence_quoted",
    "TIER_CAPS",
]
