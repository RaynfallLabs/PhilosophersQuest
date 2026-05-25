"""AI bank structural gates.

The AI bank has its own distinctive voice — see
`proposals/v2_audit/AI_FRAMEWORK.md` (the Recognition Pattern). This
module exposes the per-question gates that enforce the framework.

Reuses subject-agnostic gates from `tools.quizgen.gates.philosophy`
(schema, choice_shape_parity, context_no_meta_references). Adds five
AI-specific gates:

  - no_fabricated_models     (HARD) — invented model names blocked
  - no_anthropomorphizing    (SOFT) — "AI wants/feels/knows X" without
                                     scare quotes flagged
  - no_doomer_optimist_falsebalance (SOFT) — "AI optimists say X,
                                     doomers say Y — who's right?"
                                     false-balance framing flagged
  - no_slurs                 (HARD) — "doomer"/"techno-bro" pejoratives
                                     blocked as choice text
  - no_above_grade10_ai      (HARD) — academic research-paper-level
                                     terminology blocked at T5+ analog
                                     to grammar's grade-10 ceiling

Skipped (with reason — not "conveniently forgetting"):
  - vocab_teaching_at_t13 (grammar-specific)
  - tier_concept_appropriate (grammar-specific concept terms)
  - no_fake_etymology (grammar-specific)
  - wonder_bias_check / drama_available / history_named_anchor /
    place_anchor_check (history/geography/etc. voice rules)
  - no_verdict_on_contested (philosophy — AI is substantive on
                            contested topics by design)
"""
from __future__ import annotations

import re
from typing import Callable, Optional

# Reuse subject-agnostic gates from philosophy's module
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
# Gate: no_fabricated_models
# --------------------------------------------------------------------------

# Whitelist of known-real AI model names that we know exist (2026 cutoff).
# Patterns that LOOK like model names but aren't on this list trip the gate.
# We're conservative: this catches the most obvious fabrications like
# "Claude-7" or "GPT-8-Plus" without false-positive on legitimate models.
KNOWN_REAL_MODELS = {
    # GPT family
    "gpt-2", "gpt-3", "gpt-3.5", "gpt-4", "gpt-4o", "gpt-4 turbo",
    "gpt-4.1", "gpt-4.5", "gpt-5",
    # Claude family
    "claude 1", "claude 2", "claude 2.1", "claude 3", "claude 3 haiku",
    "claude 3 sonnet", "claude 3 opus", "claude 3.5 sonnet",
    "claude 3.5 haiku", "claude 3.7 sonnet", "claude 4", "claude 4 opus",
    "claude 4 sonnet", "claude opus 4", "claude opus 4.5",
    "claude sonnet 4", "claude sonnet 4.5",
    # Gemini family
    "gemini", "gemini 1", "gemini 1.5", "gemini 1.5 pro", "gemini 1.5 flash",
    "gemini 2", "gemini 2.0", "gemini 2.5", "gemini ultra",
    # Llama family
    "llama", "llama 1", "llama 2", "llama 3", "llama 3.1", "llama 3.2", "llama 3.3",
    # Other major models
    "mistral", "mistral 7b", "mistral large", "mixtral",
    "deepseek", "deepseek v2", "deepseek v3", "deepseek-r1", "deepseek r1",
    "grok", "grok 1", "grok 2", "grok 3", "grok 4",
    "falcon", "qwen", "qwen 2", "qwen 2.5", "command", "command r", "command r+",
    "phi", "phi-2", "phi-3", "phi-4",
    "alphago", "alphazero", "alphafold", "alphafold 2", "alphafold 3",
    "lambda", "lamda", "palm", "palm 2", "bard",
    "stable diffusion", "stable diffusion xl", "sdxl",
    "dall-e", "dall-e 2", "dall-e 3",
    "midjourney", "imagen", "flux",
    "whisper", "sora",
    "bert", "gpt", "t5", "lstm",
    "eliza", "shrdlu", "watson", "deep blue",
    "chatgpt", "copilot", "github copilot", "cursor",
    "o1", "o3", "o4",
}

# Regex pattern matching plausibly-fabricated model names. Looks for
# "<known-prefix>-<number>" combos that aren't in the whitelist.
# Suffix only matches known model-suffix tokens via hyphen ("GPT-4-turbo")
# so a space-separated next word (e.g., "GPT-4 passing") doesn't get
# absorbed into the match.
_MODEL_SUFFIX = r"(?:-(?:o|turbo|plus|pro|max|mini|sonnet|opus|haiku|instruct|flash|ultra|nano|r1|r2|v2|v3))?"
SUSPICIOUS_MODEL_PATTERN = re.compile(
    r"\b("
    rf"GPT[- ]?\d+(?:\.\d+)?{_MODEL_SUFFIX}|"
    rf"Claude[- ]?\d+(?:\.\d+)?{_MODEL_SUFFIX}|"
    rf"Gemini[- ]?\d+(?:\.\d+)?{_MODEL_SUFFIX}|"
    rf"Llama[- ]?\d+(?:\.\d+)?{_MODEL_SUFFIX}|"
    rf"Grok[- ]?\d+(?:\.\d+)?{_MODEL_SUFFIX}|"
    rf"Mistral[- ]?\d+(?:\.\d+)?{_MODEL_SUFFIX}"
    r")\b",
    re.IGNORECASE,
)


def gate_no_fabricated_models(q: dict) -> Optional[str]:
    """Block invented model names. Catches obvious fabrications like
    'GPT-8-Plus' or 'Claude-7' that don't exist."""
    stem = q.get("question", "") or ""
    answer = q.get("answer", "") or ""
    choices = q.get("choices", []) or []
    context = q.get("context", "") or ""
    haystacks = [
        ("stem", stem),
        ("answer", answer),
        ("context", context),
    ] + [(f"choice-{i}", c) for i, c in enumerate(choices) if isinstance(c, str)]
    for label, h in haystacks:
        for match in SUSPICIOUS_MODEL_PATTERN.finditer(h):
            candidate = match.group(0).lower().replace("-", " ").replace("  ", " ").strip()
            # Normalize spaces
            candidate_clean = re.sub(r"\s+", " ", candidate)
            if candidate_clean not in KNOWN_REAL_MODELS:
                # Try a looser match — sometimes "GPT-4" stripped becomes "gpt 4"
                # and we have "gpt-4" in whitelist. Build a relaxed form.
                relaxed = candidate_clean.replace(" ", "-")
                if relaxed not in KNOWN_REAL_MODELS:
                    relaxed2 = candidate_clean.replace(" ", "")
                    if not any(known.replace(" ", "").replace("-", "") == relaxed2.replace("-", "") for known in KNOWN_REAL_MODELS):
                        return (
                            f"no_fabricated_models: {label} contains a model "
                            f"name {match.group(0)!r} that doesn't match any "
                            f"known real model"
                        )
    return None


# --------------------------------------------------------------------------
# Gate: no_anthropomorphizing (SOFT-WARN)
# --------------------------------------------------------------------------

# Patterns where AI is treated as having mental states without scare quotes.
# We allow these when they're in quotes (the AI's output itself) or when the
# context explicitly frames them as scare-quoted (e.g., AI "wants" or
# anthropomorphizing as a phenomenon being discussed).
ANTHROPOMORPHIZE_PATTERN = re.compile(
    r"\b(?:"
    r"the (?:AI|model|chatbot|LLM|algorithm)\s+(?:wants?|feels?|knows?|thinks?|believes?|understands?|cares?|hates?|loves?|fears?)|"
    r"(?:AI|chatbot|LLM)\s+(?:doesn't want|wants? to|feels? like|thinks? that)|"
    r"(?:GPT|Claude|Gemini|Llama)\s+(?:wants?|feels?|knows?|thinks?|believes?)"
    r")\b",
    re.IGNORECASE,
)


def gate_no_anthropomorphizing(q: dict) -> Optional[str]:
    """SOFT-warn when AI is described as having mental states without
    scare-quotes / framing. We exempt cases inside quotes (the AI's
    own output) and cases where the surrounding context clearly frames
    anthropomorphization as a phenomenon being discussed."""
    stem = q.get("question", "") or ""
    answer = q.get("answer", "") or ""
    choices = q.get("choices", []) or []
    context = q.get("context", "") or ""
    for label, text in [("stem", stem), ("answer", answer), ("context", context)] + \
                       [(f"choice-{i}", c) for i, c in enumerate(choices) if isinstance(c, str)]:
        m = ANTHROPOMORPHIZE_PATTERN.search(text)
        if not m:
            continue
        # Exempt if the match is inside quotes (showing AI output)
        idx = m.start()
        before = text[:idx]
        # Count unbalanced quotes before the match
        if before.count("'") % 2 == 1 or before.count('"') % 2 == 1:
            continue
        # Exempt if context discusses anthropomorphizing AS A PHENOMENON
        if any(k in text.lower() for k in [
            "anthropomorph", "scare quote", "appear to", "as if",
            "treat as if", "is not actually", "doesn't really",
            "isn't really", "we say", "loosely speaking",
        ]):
            continue
        return (
            f"soft-warn: no_anthropomorphizing: {label} attributes mental "
            f"states to AI without scare quotes / framing: {m.group(0)!r}"
        )
    return None


# --------------------------------------------------------------------------
# Gate: no_doomer_optimist_falsebalance (SOFT-WARN)
# --------------------------------------------------------------------------

FALSEBALANCE_PATTERN = re.compile(
    r"\b(?:"
    r"doomers?\s+(?:say|believe|argue|claim)\s+.{0,80}\bwhile\s+(?:optimists?|accelerationists?)\s+(?:say|believe|argue|claim)|"
    r"(?:AI optimists?|accelerationists?)\s+(?:say|believe).{0,80}\bdoomers?\s+(?:say|believe)|"
    r"who'?s\s+right.{0,40}(?:doomer|optimist|accelerationist)|"
    r"(?:doomer|optimist|accelerationist).{0,40}who'?s\s+right"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)


def gate_no_doomer_optimist_falsebalance(q: dict) -> Optional[str]:
    """SOFT-warn for 'doomer vs optimist — who's right?' false-balance
    framings. Per the framework, both are ideologies and the bank
    treats them as such, not as competing answers to a settled
    question."""
    text = (
        q.get("question", "") + " " +
        q.get("answer", "") + " " +
        " ".join(q.get("choices", []) or []) + " " +
        q.get("context", "")
    )
    if FALSEBALANCE_PATTERN.search(text):
        return (
            "soft-warn: no_doomer_optimist_falsebalance: question frames AI "
            "doomerism vs optimism as a question with a balanced answer — "
            "framework treats both as ideologies, name them as such"
        )
    return None


# --------------------------------------------------------------------------
# Gate: no_slurs (HARD)
# --------------------------------------------------------------------------

# Pejorative shortcuts banned as choice text or stem text (allowed in context
# only when discussing the term itself).
SLUR_PATTERN = re.compile(
    r"\b(?:doomers?|techno[- ]?bro|AI bro|luddite|booster bro)\b",
    re.IGNORECASE,
)


def gate_no_slurs(q: dict) -> Optional[str]:
    """Hard-reject pejorative shortcuts in stem/answer/choices. Allowed in
    context when discussing the term itself ('opponents call them
    doomers')."""
    stem = q.get("question", "") or ""
    answer = q.get("answer", "") or ""
    choices = q.get("choices", []) or []
    for label, text in [("stem", stem), ("answer", answer)] + \
                       [(f"choice-{i}", c) for i, c in enumerate(choices) if isinstance(c, str)]:
        m = SLUR_PATTERN.search(text)
        if m:
            return (
                f"no_slurs: {label} contains pejorative shortcut "
                f"{m.group(0)!r} — use substantive description instead"
            )
    return None


# --------------------------------------------------------------------------
# Gate: no_above_grade10_ai (HARD)
# --------------------------------------------------------------------------

# Academic / research-paper terminology that's above the grade-10 ceiling
# for AI. T5 stays at concrete grade-9-10-appropriate content.
# These are tokens that would only appear in college / research-level
# discussion, not kid-accessible AI literacy.
ABOVE_GRADE_10_AI_TOKENS = re.compile(
    r"\b(?:"
    r"variational autoencoder|variational inference|"
    r"kullback[- ]?leibler|KL divergence|"
    r"Bayesian network|posterior distribution|prior probability(?:\s+distribution)?|"
    r"stochastic gradient descent|"
    r"non[- ]?euclidean|"
    r"Markov decision process|MDP|"
    r"Hamiltonian Monte Carlo|"
    r"Lipschitz continuity|"
    r"convex optimization|"
    r"backward pass|forward pass|"  # too low-level
    r"Jacobian|Hessian|"
    r"manifold hypothesis|"
    r"information bottleneck|"
    r"VC dimension|PAC learning|"
    r"NeurIPS|ICML|ICLR|"  # academic venue names
    r"ablation study|"
    r"empirical risk minimization|"
    r"L[12] regularization|L[12] norm|"
    r"softmax temperature|"
    r"Adam optimizer|RMSprop|AdaGrad|"
    r"layer normalization|batch normalization"
    r")\b",
    re.IGNORECASE,
)


def gate_no_above_grade10_ai(q: dict) -> Optional[str]:
    """Hard-reject content using grade-10-and-above academic/research
    terminology. The AI bank stays at concrete kid-accessible content
    even at T5; if you'd need to read a research paper to understand
    the term, it's above ceiling.

    Allowed at T5: concrete event names, figure positions, mechanism
    explanations a paragraph can convey, real-world cases.
    """
    stem = q.get("question", "") or ""
    answer = q.get("answer", "") or ""
    choices = q.get("choices", []) or []
    context = q.get("context", "") or ""
    haystacks = [stem, answer, context] + [c if isinstance(c, str) else "" for c in choices]
    for h in haystacks:
        m = ABOVE_GRADE_10_AI_TOKENS.search(h)
        if m:
            return (
                f"no_above_grade10_ai: contains above-grade-10 token "
                f"{m.group(0)!r} — see AI_FRAMEWORK §2 grade-10 ceiling"
            )
    return None


# --------------------------------------------------------------------------
# Gate registry
# --------------------------------------------------------------------------

SOFT_WARN_GATES: frozenset[str] = frozenset({
    "no_anthropomorphizing",
    "no_doomer_optimist_falsebalance",
})


PER_QUESTION_GATES: list[tuple[str, Callable[[dict], Optional[str]]]] = [
    # Hard-reject
    ("schema", gate_schema),
    ("choice_shape_parity", gate_choice_shape_parity),
    ("context_no_meta_references", gate_context_no_meta_references),
    ("no_fabricated_models", gate_no_fabricated_models),
    ("no_slurs", gate_no_slurs),
    ("no_above_grade10_ai", gate_no_above_grade10_ai),
    # Soft-warn
    ("no_anthropomorphizing", gate_no_anthropomorphizing),
    ("no_doomer_optimist_falsebalance", gate_no_doomer_optimist_falsebalance),
]


def run_gates(q: dict) -> dict[str, Optional[str]]:
    return {name: fn(q) for name, fn in PER_QUESTION_GATES}


__all__ = [
    "PER_QUESTION_GATES",
    "SOFT_WARN_GATES",
    "run_gates",
    "gate_schema",
    "gate_no_fabricated_models",
    "gate_no_anthropomorphizing",
    "gate_no_doomer_optimist_falsebalance",
    "gate_no_slurs",
    "gate_no_above_grade10_ai",
    "TIER_CAPS",
]
