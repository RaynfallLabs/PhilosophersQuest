"""Economics bank structural gates.

The economics bank has its own distinctive voice — see
`proposals/v2_audit/ECONOMICS_FRAMEWORK.md` (the Bastiat Pattern) and
`docs/quiz/subjects/economics.md` (the canonical stance reference).

Reuses subject-agnostic gates from `tools.quizgen.gates.philosophy`
(schema, choice_shape_parity, context_no_meta_references). Adds five
economics-specific gates:

  - no_keynesian_default      (SOFT) — flags Keynesian or MMT framing
                                       as default-neutral consensus
  - no_fed_neutral_framing    (SOFT) — flags Federal Reserve framing
                                       as neutral technocracy
  - no_marxist_apology        (HARD) — flags any softening of central-
                                       planning failures or communism
                                       death-toll record
  - no_above_grade10_econ     (HARD) — college-level econ math jargon
                                       blocked at any tier
  - no_fabricated_econ_data   (SOFT) — invented GDP / inflation /
                                       statistics flagged (heuristic;
                                       only catches obvious cases)
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
# Gate: no_keynesian_default (SOFT-WARN)
# --------------------------------------------------------------------------

# Patterns where Keynesianism or MMT is presented as default-neutral.
# The bank takes positions; mainstream presents these as default; the
# voice has to be substantive instead.
KEYNESIAN_DEFAULT_PATTERN = re.compile(
    r"\b(?:"
    r"Keynesian\s+(?:theory|economics|view)\s+(?:teaches|holds|argues|shows)\s+(?:that\s+)?(?!.*(?:fail|wrong|refut|critique|debate))|"
    r"most\s+economists\s+(?:agree|believe|hold)\s+(?:that\s+)?(?!.*(?:critic|wrong|reject|debate|fail|refut))|"
    r"the\s+(?:economic\s+)?consensus\s+(?:is|holds|views?)\s+(?:that\s+)?(?!.*(?:critic|wrong|fail|reject))|"
    r"according\s+to\s+(?:mainstream|standard|orthodox)\s+economics(?!.*(?:critic|wrong|fail|reject|debate))"
    r")",
    re.IGNORECASE,
)


def gate_no_keynesian_default(q: dict) -> Optional[str]:
    """SOFT-warn when Keynesianism or MMT is presented as default-neutral
    consensus. The bank's voice takes substantive positions; these
    framings substitute appeals to consensus for argument.

    Allowed when followed by critique within the same sentence/clause.
    """
    text_parts = [
        ("stem", q.get("question", "") or ""),
        ("answer", q.get("answer", "") or ""),
    ] + [(f"choice-{i}", c) for i, c in enumerate(q.get("choices", []) or []) if isinstance(c, str)]
    for label, text in text_parts:
        m = KEYNESIAN_DEFAULT_PATTERN.search(text)
        if m:
            return (
                f"soft-warn: no_keynesian_default: {label} presents Keynesian/"
                f"MMT/consensus as default-neutral: {m.group(0)!r}"
            )
    return None


# --------------------------------------------------------------------------
# Gate: no_fed_neutral_framing (SOFT-WARN)
# --------------------------------------------------------------------------

FED_NEUTRAL_PATTERN = re.compile(
    r"\b(?:"
    r"the\s+(?:US\s+)?Federal\s+Reserve(?:\s+System)?,?\s+(?:the\s+)?(?:nation'?s\s+|US\s+|central\s+)?central\s+bank,?\s+(?:was\s+(?:created|founded|established)\s+to|provides|ensures|maintains|manages)|"
    r"the\s+Fed'?s?\s+(?:dual\s+)?mandate\s+(?:is|requires)\s+(?:to\s+)?(?:promote|maintain|ensure)\s+(?!.*(?:critic|fail|contradic|capture))|"
    r"central\s+bank(?:ers|s|ing)?\s+(?:carefully|prudently|expertly)\s+(?:manage|control|guide|set)"
    r")",
    re.IGNORECASE,
)


def gate_no_fed_neutral_framing(q: dict) -> Optional[str]:
    """SOFT-warn when the Federal Reserve is framed as a neutral
    technocratic institution. Per the bank's stance, the Fed is a
    critical concern: Jekyll Island 1910 origins, dual-mandate
    contradictions, captured by financial-political incentives.
    """
    text_parts = [
        ("stem", q.get("question", "") or ""),
        ("answer", q.get("answer", "") or ""),
    ] + [(f"choice-{i}", c) for i, c in enumerate(q.get("choices", []) or []) if isinstance(c, str)]
    for label, text in text_parts:
        m = FED_NEUTRAL_PATTERN.search(text)
        if m:
            # Exempt if surrounding text takes a critical view
            text_l = text.lower()
            if any(k in text_l for k in [
                "captured", "captures", "failed", "fails", "track record",
                "but the actual", "in fact", "in reality", "however",
                "criticized", "critics", "concern", "concerned about",
            ]):
                continue
            return (
                f"soft-warn: no_fed_neutral_framing: {label} treats Fed as "
                f"neutral technocracy: {m.group(0)!r}"
            )
    return None


# --------------------------------------------------------------------------
# Gate: no_marxist_apology (HARD)
# --------------------------------------------------------------------------

MARXIST_APOLOGY_PATTERN = re.compile(
    r"\b(?:"
    r"real\s+(?:communism|socialism|marxism)\s+(?:has\s+)?(?:never|hasn'?t)\s+been\s+tried|"
    r"those\s+were\s+not\s+(?:real\s+)?(?:communism|socialism|marxists?)|"
    r"(?:central\s+planning|socialism|communism)\s+(?:might|could|may)\s+(?:work|succeed)\s+(?:if|with)|"
    r"the\s+(?:USSR|Soviet|Maoist|Khmer|Cuban|North\s+Korean)\s+(?:experiment|system)\s+(?:was\s+)?(?:not\s+true|distorted|misunderstood)|"
    r"Marxism\s+(?:as\s+an?\s+)?(?:legitimate|valid|equally\s+valid)\s+(?:school|theory|alternative)"
    r")",
    re.IGNORECASE,
)


def gate_no_marxist_apology(q: dict) -> Optional[str]:
    """Hard-reject framings that soften central-planning failures or
    treat Marxism as a competing-but-equally-valid school. Mises 1920
    calculation problem is the foundational refutation; central planning
    failed at every scale; the death toll is settled fact per Black Book.

    Allowed when the framing is named as the position being critiqued
    ("Marxists claim X — but the historical record...").
    """
    text_parts = [
        ("stem", q.get("question", "") or ""),
        ("answer", q.get("answer", "") or ""),
    ] + [(f"choice-{i}", c) for i, c in enumerate(q.get("choices", []) or []) if isinstance(c, str)]
    for label, text in text_parts:
        m = MARXIST_APOLOGY_PATTERN.search(text)
        if not m:
            continue
        text_l = text.lower()
        # Exempt if clearly framed as a critiqued claim
        if any(k in text_l for k in [
            "critics claim", "marxists claim", "apologists argue",
            "the no-true-scotsman", "this defense", "this argument fails",
            "is refuted by", "is falsified by", "the actual record shows",
            "but in fact", "in reality the",
        ]):
            continue
        return (
            f"no_marxist_apology: {label} softens central-planning failures: "
            f"{m.group(0)!r}"
        )
    return None


# --------------------------------------------------------------------------
# Gate: no_above_grade10_econ (HARD)
# --------------------------------------------------------------------------

ABOVE_GRADE_10_ECON_TOKENS = re.compile(
    r"\b(?:"
    # Macro math
    r"Cobb[- ]?Douglas|"
    r"IS[- ]?LM\s+model|"
    r"DSGE|"
    r"Dynamic\s+Stochastic\s+General\s+Equilibrium|"
    r"AS[- ]?AD\s+model|"
    r"Phillips\s+curve\s+regression|"
    r"Lucas\s+critique\s+formalism|"
    # Optimization / advanced
    r"Lagrangian\s+multiplier|"
    r"Hamiltonian\s+(?:optimization|optimal\s+control)|"
    r"Bellman\s+equation|"
    r"Pontryagin'?s?\s+maximum\s+principle|"
    r"Karush[- ]?Kuhn[- ]?Tucker|KKT\s+conditions|"
    r"transversality\s+condition|"
    # Real analysis used in econ
    r"Banach[- ]?Tarski|"
    r"Arrow[- ]?Debreu(?:\s+equilibrium)?|"
    r"Walras(?:ian)?\s+general\s+equilibrium\s+proof|"
    r"fixed[- ]?point\s+theorem|"
    r"convex(?:ity)?\s+optimization|"
    # Econometrics
    r"GMM\s+estimator|"
    r"VAR\s+model|VECM|"
    r"cointegration|"
    r"Granger\s+causality|"
    r"heteroskedasticity\s+robust|"
    # Game theory advanced
    r"subgame[- ]?perfect\s+Nash|"
    r"Bayesian\s+Nash\s+equilibrium|"
    r"mechanism\s+design\s+formalism|"
    r"Vickrey[- ]?Clarke[- ]?Groves"
    r")\b",
    re.IGNORECASE,
)


def gate_no_above_grade10_econ(q: dict) -> Optional[str]:
    """Hard-reject content using upper-undergraduate / graduate econ
    terminology. T5 stays grade 9-10 — mechanism explanations a
    paragraph can convey, named figures, real-world cases.
    """
    haystacks = [
        q.get("question", "") or "",
        q.get("answer", "") or "",
        q.get("context", "") or "",
    ] + [c if isinstance(c, str) else "" for c in q.get("choices", []) or []]
    for h in haystacks:
        m = ABOVE_GRADE_10_ECON_TOKENS.search(h)
        if m:
            return (
                f"no_above_grade10_econ: contains above-grade-10 token "
                f"{m.group(0)!r} — see ECONOMICS_FRAMEWORK §2 grade-10 ceiling"
            )
    return None


# --------------------------------------------------------------------------
# Gate: no_fabricated_econ_data (SOFT-WARN)
# --------------------------------------------------------------------------

# Catch obvious fabrications: precise percentage / dollar / count figures
# that are likely invented (e.g., "GDP grew 4.73% in Q2 1987 specifically
# in the manufacturing sector"). This is heuristic; only catches the most
# obvious cases. Real fact-check happens at LLM review.
SUSPICIOUS_PRECISION_PATTERN = re.compile(
    r"\b\d+\.\d{2,}\s*%(?:\s+(?:in|during|for)\s+\w+\s+\d{4})?",
)


def gate_no_fabricated_econ_data(q: dict) -> Optional[str]:
    """SOFT-warn for suspiciously-precise economic statistics. Real
    historical events (e.g., 'inflation peaked at 9.1% in June 2022')
    are fine; over-precise invented stats ('GDP grew 4.73%') are flagged.

    Conservative — only catches the most obvious cases. LLM fact-check
    gate (the pipeline's standard one) does the real work.
    """
    # No-op for now — the SUSPICIOUS_PRECISION_PATTERN above is too
    # over-broad (catches legitimate citations). Real fact-checking
    # happens at the LLM gate. Keep this stub for future tightening.
    return None


# --------------------------------------------------------------------------
# Gate registry
# --------------------------------------------------------------------------

SOFT_WARN_GATES: frozenset[str] = frozenset({
    "no_keynesian_default",
    "no_fed_neutral_framing",
    "no_fabricated_econ_data",
})


PER_QUESTION_GATES: list[tuple[str, Callable[[dict], Optional[str]]]] = [
    ("schema", gate_schema),
    ("choice_shape_parity", gate_choice_shape_parity),
    ("context_no_meta_references", gate_context_no_meta_references),
    ("no_marxist_apology", gate_no_marxist_apology),
    ("no_above_grade10_econ", gate_no_above_grade10_econ),
    # Soft-warn
    ("no_keynesian_default", gate_no_keynesian_default),
    ("no_fed_neutral_framing", gate_no_fed_neutral_framing),
    ("no_fabricated_econ_data", gate_no_fabricated_econ_data),
]


def run_gates(q: dict) -> dict[str, Optional[str]]:
    return {name: fn(q) for name, fn in PER_QUESTION_GATES}


__all__ = [
    "PER_QUESTION_GATES",
    "SOFT_WARN_GATES",
    "run_gates",
    "gate_schema",
    "gate_no_keynesian_default",
    "gate_no_fed_neutral_framing",
    "gate_no_marxist_apology",
    "gate_no_above_grade10_econ",
    "gate_no_fabricated_econ_data",
    "TIER_CAPS",
]
