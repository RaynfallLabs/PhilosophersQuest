"""Math bank structural gates.

Math is one of two snappy-rote subjects (the other is grammar). See
`proposals/v2_audit/MATH_FRAMEWORK.md` for the voice rules. This module
exposes the per-question gates that enforce the framework.

Math is exempt at the pipeline level from:
  - anti_rote (math IS rote; that's the point)
  - answer_collision (many math answers are common numbers)
  - length_parity (numeric answers vary wildly in char length)

Math is NOT exempt from:
  - schema, length_budget (per-tier total cap, see SUBJECT_TIER_BUDGETS["math"])
  - duplicate (math has its own higher threshold of 0.97)
  - math_correctness (math-only gate — verifies the claimed answer is right)
  - trailing_tokens

Math-specific gates added here:
  - gate_no_placeholder_strings     (HARD) — bans "NA0", "NA1" generation
                                             artifacts that leaked in past
                                             bulk-gen runs
  - gate_trick_context_required     (HARD T2+) — context at T2+ must name a
                                                 trick or equation, not just
                                                 restate the answer
  - gate_stem_length_combat         (HARD) — per-tier stem-only length cap
                                             driven by 16s combat timer
  - gate_magnitude_leak             (HARD) — correct numerical answer must not
                                             be uniquely larger or uniquely
                                             smaller than all 3 distractors
  - gate_tier_concept_appropriate   (HARD) — above-grade-band concepts banned
                                             (logs, trig functions, calculus,
                                             matrices, complex numbers, etc.)
  - gate_named_equation_when_applicable (SOFT) — when a foundational equation
                                                 is used, the equation should
                                                 be NAMED in context
"""
from __future__ import annotations

import re
from typing import Callable, Optional


# Per-tier stem-only length caps (16s combat timer constraint).
# These are SEPARATE from the total-record length budget in
# tools/quizgen/deterministic/length_budget.py SUBJECT_TIER_BUDGETS["math"].
STEM_LENGTH_CAPS: dict[int, int] = {
    1: 50,    # numeric-only "7 × 8 = ?"
    2: 100,   # short setups OK
    3: 160,   # one-sentence setup
    4: 220,   # multi-clause word problems
    5: 280,   # polynomial expansions
}


# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------


def gate_schema(q: dict) -> Optional[str]:
    for field in ("tier", "question", "answer", "choices", "context"):
        if field not in q:
            return f"schema: missing field {field}"
    if q.get("tier") not in (1, 2, 3, 4, 5):
        return f"schema: invalid tier {q.get('tier')}"
    chs = q.get("choices", [])
    if not isinstance(chs, list) or len(chs) != 4:
        return f"schema: choices length {len(chs) if isinstance(chs, list) else 'not-list'}"
    if q.get("answer") not in chs:
        return "schema: answer not in choices"
    return None


# --------------------------------------------------------------------------
# Gate: placeholder-string ban (NA0/NA1 etc.)
# --------------------------------------------------------------------------

PLACEHOLDER_RE = re.compile(
    r"\b(?:NA[01]|N/A[01]?|PLACEHOLDER|TODO|FIXME|\?\?\?|XXX)\b",
    re.IGNORECASE,
)


def gate_no_placeholder_strings(q: dict) -> Optional[str]:
    """Hard-reject any choice or answer containing a literal placeholder
    artifact like 'NA0', 'NA1', 'PLACEHOLDER', 'TODO', etc. These are
    bulk-gen scaffold leaks — always broken records.
    """
    haystacks = [q.get("answer", "") or ""] + [
        c if isinstance(c, str) else "" for c in (q.get("choices", []) or [])
    ]
    for h in haystacks:
        m = PLACEHOLDER_RE.search(h)
        if m:
            return (
                f"no_placeholder_strings: contains generation artifact "
                f"{m.group(0)!r}"
            )
    return None


# --------------------------------------------------------------------------
# Gate: trick-context required at T2+
# --------------------------------------------------------------------------

# Named tricks + equations the bank teaches. The context at T2+ should
# include AT LEAST ONE of these named moves OR an explicit step-by-step
# computation (a chain like "= 100 + 100 = 200" or "= 9 + 16 = 25, so c = 5").
NAMED_MOVES_RE = re.compile(
    r"\b(?:"
    # Mental-math trick names
    r"times[\s-]?table|"
    r"make[\s-]?a[\s-]?ten|bridg(?:e|ing)[\s-]?(?:through[\s-]?)?ten|"
    r"counting[\s-]?on|skip[\s-]?count(?:ing)?|"
    r"number[\s-]?bond|fact[\s-]?famil|"
    r"doubl(?:e|es|ing)|halv(?:e|es|ing)|"
    r"complement[\s-]?to[\s-]?(?:10|100|1000|one[\s-]?hundred)|"
    r"add[\s-]?(?:by[\s-]?)?tens?[\s-]?(?:then[\s-]?ones?)?|"
    r"distributiv(?:e|ity)|"
    r"halving[\s-]?and[\s-]?doubling|halving[\s-]?(?:and|&)[\s-]?doubling|"
    r"decimal[\s-]?shift|move[\s-]?the[\s-]?decimal|shift[\s-]?the[\s-]?decimal|"
    r"square[\s-]?ending[\s-]?in[\s-]?5|squares?[\s-]?ending[\s-]?in[\s-]?five|"
    r"tens?[\s-]?times[\s-]?next|tens?[\s-]?digit[\s-]?times[\s-]?next|"
    r"trick|shortcut|"
    r"PEMDAS|order[\s-]?of[\s-]?operations|"
    r"GCF|greatest[\s-]?common[\s-]?factor|LCM|least[\s-]?common[\s-]?multiple|"
    r"divisibility[\s-]?rule|"
    r"divis(?:ible|ibility)|"
    r"prime[\s-]?factor(?:ization)?|"
    r"sign[\s-]?rule|negative[\s-]?times[\s-]?negative|"
    r"absolute[\s-]?value|distance[\s-]?from[\s-]?zero|"
    r"add[\s-]?(?:and[\s-]?)?subtract[\s-]?the[\s-]?same|"
    r"round[\s-]?to[\s-]?(?:100|one[\s-]?hundred)|round[\s-]?to[\s-]?estimate|"
    r"cross[\s-]?multipl(?:y|ication|ying)|"
    r"like[\s-]?term|combining[\s-]?like[\s-]?terms|"
    r"two[\s-]?step[\s-]?equation|two[\s-]?step[\s-]?inequalit|"
    r"inverse[\s-]?operation|"
    r"slope|rise[\s-]?over[\s-]?run|"
    r"y[\s-]?intercept|slope[\s-]?intercept|"
    r"FOIL|"
    r"difference[\s-]?of[\s-]?squares?|"
    r"perfect[\s-]?square|"
    r"trinomial|factor(?:ing|ization)|find[\s-]?two[\s-]?numbers?|"
    r"factor[\s-]?by[\s-]?grouping|"
    r"discriminant|"
    r"quadratic[\s-]?formula|"
    r"vertex[\s-]?form|"
    r"systems?[\s-]?of[\s-]?equations?|elimination|substitution[\s-]?method|"
    r"exponent[\s-]?rule|power[\s-]?rule|"
    r"scientific[\s-]?notation|"
    r"square[\s-]?root[\s-]?simplification|simplify[\s-]?the[\s-]?(?:radical|root)|"
    # Named foundational equations
    r"Pythagorean[\s-]?(?:theorem|triple)|"
    r"distance[\s-]?formula|midpoint[\s-]?formula|"
    r"3[\s-]?4[\s-]?5|5[\s-]?12[\s-]?13|8[\s-]?15[\s-]?17|7[\s-]?24[\s-]?25|"
    r"compound[\s-]?interest|simple[\s-]?interest|"
    r"arithmetic[\s-]?sequence|geometric[\s-]?sequence|"
    r"nth[\s-]?term|n[\s-]?th[\s-]?term|"
    # Percent + F/D/P language
    r"percent|per[\s-]?cent|"
    r"fraction|decimal|"
    # Common F/D/P + tip patterns
    r"tip[\s-]?trick|tip[\s-]?math|"
    r"10[%\s]?(?:then[\s-]?)?doubl|"
    # Geometry formulas (often written symbolically too, but accept named)
    r"area[\s-]?formula|perimeter[\s-]?formula|volume[\s-]?formula|"
    r"circle[\s-]?area|circumference|"
    r"cylinder|cone|sphere|"
    r"parallelogram|trapezoid|"
    # Probability / stats names
    r"probability|favorable[\s-]?(?:over|outcomes)|"
    r"compound[\s-]?probability|independent[\s-]?events?|"
    r"mean|median|mode|range|"
    # Function notation
    r"function[\s-]?notation|f\s*\(\s*x\s*\)"
    r")\b",
    re.IGNORECASE,
)

# A computation chain has multiple `=` signs separated by some content
# (e.g., "75 + 125 = 75 + 25 + 100 = 100 + 100 = 200"). This pattern
# accepts context that walks through the math even if it doesn't name
# a trick explicitly.
COMPUTATION_CHAIN_RE = re.compile(r"=[^=]+=[^=]+(?:=|\.|$)")

# Bare-answer context — context is just the answer restated.
def _is_bare_answer_context(answer: str, context: str) -> bool:
    """Detect contexts that are just 'The answer is X' or '200 is correct'
    with no teaching content."""
    ctx_lower = (context or "").strip().lower()
    ans_lower = (answer or "").strip().lower()
    if not ctx_lower or not ans_lower:
        return True if ctx_lower == "" else False
    # If context is very short and the answer appears in it, likely bare
    if len(ctx_lower) <= 60:
        # Strip the answer and common scaffolding words
        without = ctx_lower
        without = re.sub(re.escape(ans_lower), "", without)
        for filler in [
            "the answer is", "answer:", "is", "correct", "yes",
            "sum:", "product:", "result:", "equals", "=", ".", ",",
        ]:
            without = without.replace(filler, "")
        # Remove digits and whitespace
        without = re.sub(r"[\d\s]", "", without).strip()
        # If almost nothing left, context is bare
        if len(without) <= 4:
            return True
    return False


def gate_trick_context_required(q: dict) -> Optional[str]:
    """T2+ context must name a trick, name an equation, or walk through a
    computation chain. Bare 'the answer is X' contexts fail.

    T1 is exempt (pure rote).
    """
    tier = q.get("tier")
    if tier == 1:
        return None
    context = q.get("context", "") or ""
    answer = q.get("answer", "") or ""

    if not context.strip():
        return "trick_context_required: context is empty at T2+ — must teach the move"

    if _is_bare_answer_context(answer, context):
        return (
            "trick_context_required: context appears to be a bare answer "
            "restatement; T2+ must NAME a trick or equation, see MATH_FRAMEWORK §4"
        )

    if NAMED_MOVES_RE.search(context):
        return None
    if COMPUTATION_CHAIN_RE.search(context):
        return None

    return (
        "trick_context_required: context does not name a trick, an equation, "
        "or show a computation chain; T2+ must teach the move"
    )


# --------------------------------------------------------------------------
# Gate: stem-length cap for 16s combat
# --------------------------------------------------------------------------


def gate_stem_length_combat(q: dict) -> Optional[str]:
    tier = q.get("tier")
    if tier not in STEM_LENGTH_CAPS:
        return None
    cap = STEM_LENGTH_CAPS[tier]
    stem = q.get("question", "") or ""
    if len(stem) > cap:
        return (
            f"stem_length_combat: stem {len(stem)} chars > T{tier} cap {cap} "
            f"(16s combat timer constraint)"
        )
    return None


# --------------------------------------------------------------------------
# Gate: magnitude-leak — correct must not be uniquely big or uniquely small
# --------------------------------------------------------------------------

NUMERIC_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _extract_first_number(s: str) -> Optional[float]:
    """Extract the first numeric token from a choice string. Handles
    negatives and decimals. Fractions and π-form get special handling.
    """
    if not s:
        return None
    s_clean = s.strip()
    # Fraction shape "a/b"
    frac_m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*$", s_clean)
    if frac_m:
        try:
            return float(frac_m.group(1)) / float(frac_m.group(2))
        except (ValueError, ZeroDivisionError):
            return None
    # π-form "Nπ" or "πN"
    if "π" in s_clean or "pi" in s_clean.lower():
        n_m = NUMERIC_RE.search(s_clean)
        if n_m:
            try:
                return float(n_m.group(0)) * 3.14159265358979
            except ValueError:
                return None
        # Just π
        return 3.14159265358979
    # Plain number
    n_m = NUMERIC_RE.search(s_clean)
    if n_m:
        try:
            return float(n_m.group(0))
        except ValueError:
            return None
    return None


MAGNITUDE_LEAK_RATIO = 3.0  # answer must be within 3× of nearest distractor


def gate_magnitude_leak(q: dict) -> Optional[str]:
    """Reject when the numerical answer is uniquely huge or uniquely tiny
    compared to all three distractors — the 'biggest is always right'
    skim-tell.

    Applies only when all 4 choices are numeric. Skips when any choice
    doesn't parse to a number (algebraic / multi-part answers).
    """
    choices = q.get("choices", []) or []
    if len(choices) != 4:
        return None
    nums = [_extract_first_number(str(c)) for c in choices]
    if any(n is None for n in nums):
        return None
    answer = q.get("answer", "") or ""
    ans_num = _extract_first_number(str(answer))
    if ans_num is None:
        return None
    distractor_nums = [n for c, n in zip(choices, nums) if c != answer]
    if len(distractor_nums) != 3:
        return None
    # Magnitude leak: answer is > MAGNITUDE_LEAK_RATIO × every distractor
    # (uniquely huge) OR distractors all > MAGNITUDE_LEAK_RATIO × answer
    # (uniquely tiny). Zero handling: if answer == 0 or any distractor == 0,
    # skip ratio test.
    if ans_num == 0 or any(d == 0 for d in distractor_nums):
        return None
    abs_ans = abs(ans_num)
    abs_dists = [abs(d) for d in distractor_nums]
    if all(abs_ans > MAGNITUDE_LEAK_RATIO * d for d in abs_dists):
        return (
            f"magnitude_leak: correct {ans_num} is uniquely >{MAGNITUDE_LEAK_RATIO}× "
            f"all distractors {distractor_nums}; biggest-is-right skim-tell"
        )
    if all(d > MAGNITUDE_LEAK_RATIO * abs_ans for d in abs_dists):
        return (
            f"magnitude_leak: correct {ans_num} is uniquely <1/{MAGNITUDE_LEAK_RATIO}× "
            f"all distractors {distractor_nums}; smallest-is-right skim-tell"
        )
    return None


# --------------------------------------------------------------------------
# Gate: tier-appropriate concepts (no above-grade-band)
# --------------------------------------------------------------------------

# Above-9th-grade tokens — banned anywhere in the math bank.
ABOVE_GRADE9_TOKENS = re.compile(
    r"\b(?:"
    # Trig functions
    r"sin(?:e|h)?|cos(?:ine|h)?|tan(?:gent|h)?|"
    r"csc|sec(?:ant)?|cot(?:angent)?|"
    r"arcsin|arccos|arctan|"
    r"SOH[\s-]?CAH[\s-]?TOA|"
    r"unit[\s-]?circle|"
    # Logs
    r"log(?:arithm)?(?:s|ic)?|"
    r"ln\s*\(|natural[\s-]?log|"
    r"change[\s-]?of[\s-]?base|"
    # Calculus
    r"derivative|integral|differential|antiderivative|"
    r"limit(?:\s+of|\s+as|\s+at)|"
    r"calculus|"
    r"dx|d/dx|"
    # Complex numbers
    r"imaginary[\s-]?(?:number|unit)|"
    r"complex[\s-]?number|"
    # Advanced stats
    r"z[\s-]?score|standard[\s-]?deviation[\s-]?formula|normal[\s-]?distribution|"
    # Matrices / vectors
    r"matrix[\s-]?(?:multiplication|inverse|determinant)?|"
    r"determinant|eigen|"
    r"vector[\s-]?(?:product|dot|cross)|"
    # Series / sequences advanced
    r"gauss[\'’]?s?[\s-]?(?:sum|formula)|"
    r"sigma[\s-]?notation|"
    r"infinite[\s-]?(?:series|sum)|"
    # Conics beyond quadratic
    r"ellipse|hyperbola|conic[\s-]?section|"
    # Euler
    r"euler[\'’]?s?[\s-]?(?:number|identity|formula)|"
    r"natural[\s-]?(?:logarithm|constant)"
    r")\b",
    re.IGNORECASE,
)

# The literal letter "e" or "ln" needs careful handling — exclude common
# false positives where they're part of a word.
SUSPICIOUS_E_RE = re.compile(r"\be\s*≈\s*2\.71|\be\s*=\s*2\.71")


def gate_tier_concept_appropriate(q: dict) -> Optional[str]:
    """Hard-reject any concept above the 9th-grade Algebra 1 ceiling."""
    stem = q.get("question", "") or ""
    answer = q.get("answer", "") or ""
    choices = q.get("choices", []) or []
    context = q.get("context", "") or ""
    haystacks = [stem, answer, context] + [c if isinstance(c, str) else "" for c in choices]
    for h in haystacks:
        m = ABOVE_GRADE9_TOKENS.search(h)
        if m:
            return (
                f"tier_concept_appropriate: contains above-grade-9 concept "
                f"{m.group(0)!r} — math bank caps at Algebra 1 per MATH_FRAMEWORK §2"
            )
        if SUSPICIOUS_E_RE.search(h):
            return (
                "tier_concept_appropriate: references Euler's number e — "
                "math bank caps at 9th grade Algebra 1"
            )
    return None


# --------------------------------------------------------------------------
# Soft gate: named-equation-when-applicable
# --------------------------------------------------------------------------

# Equation symbols whose use in stem/answer SHOULD trigger a named-equation
# mention in context.
EQUATION_SYMBOL_HINTS = [
    (re.compile(r"\ba[²2]\s*\+\s*b[²2]\s*=\s*c[²2]\b"),
     re.compile(r"Pythagorean", re.IGNORECASE)),
    (re.compile(r"y\s*=\s*m\s*x\s*\+\s*b"),
     re.compile(r"slope[\s-]?intercept", re.IGNORECASE)),
    (re.compile(r"π\s*r\s*[²2]"),
     re.compile(r"area[\s-]?of|circle|A\s*=\s*π", re.IGNORECASE)),
    (re.compile(r"\(\s*[ab]\s*\+\s*[ab]\s*\)\s*\(\s*[ab]\s*\+\s*[ab]\s*\)"),
     re.compile(r"FOIL|distrib", re.IGNORECASE)),
]


def gate_named_equation_when_applicable(q: dict) -> Optional[str]:
    """Soft warning: if a stem/answer uses a recognizable foundational
    equation, context SHOULD name the equation (so the kid learns the
    name with the move).
    """
    tier = q.get("tier")
    if tier == 1:
        return None
    stem = q.get("question", "") or ""
    answer = q.get("answer", "") or ""
    context = q.get("context", "") or ""
    haystack = stem + " " + answer
    for symbol_re, name_re in EQUATION_SYMBOL_HINTS:
        if symbol_re.search(haystack):
            if not name_re.search(context):
                return (
                    f"soft-warn: named_equation_when_applicable: stem/answer "
                    f"uses {symbol_re.pattern!r} but context does not name the "
                    f"corresponding equation"
                )
    return None


# --------------------------------------------------------------------------
# Choice-shape parity (reused subject-agnostic pattern)
# --------------------------------------------------------------------------


def gate_choice_shape_parity(q: dict) -> Optional[str]:
    """The ANSWER must not be the odd-shape-out vs distractors.

    If 3 distractors share a shape and the answer has a different shape,
    that's a skim-tell — the kid sees one answer that looks different and
    can route to it without computing. But if 3 of 4 choices share a
    shape and one DISTRACTOR is the odd-one-out (a student-error like
    forgetting π or dropping a variable), that's fine — represents a
    real error mode.
    """
    choices = q.get("choices", []) or []
    if len(choices) != 4:
        return None
    answer = q.get("answer", "")

    def shape(c: str) -> str:
        if not isinstance(c, str):
            return "other"
        s = c.strip()
        # Multi-clause answers ("x = 3 or x = −2") — treat as algebraic
        if " or " in s.lower() or "," in s and any(
            tok in s for tok in ["=", "x", "y"]
        ):
            return "algebraic"
        # Plain integers / decimals (accept unicode minus too)
        if re.fullmatch(r"[-−]?\d+(?:\.\d+)?", s):
            return "decimal" if "." in s else "integer"
        # Currency
        if re.fullmatch(r"\$?[-−]?\d+(?:\.\d+)?\$?", s):
            return "currency"
        # Percent
        if re.fullmatch(r"[-−]?\d+(?:\.\d+)?\s*%", s):
            return "percent"
        # Fraction
        if re.fullmatch(r"[-−]?\d+\s*/\s*\d+", s):
            return "fraction"
        # π-form
        if "π" in s or re.search(r"\bpi\b", s.lower()):
            return "pi"
        # Algebraic (anything with x, y, ², or visible polynomial structure)
        if re.search(r"[xy]|²|³|\^", s):
            return "algebraic"
        return "other"

    shapes = [shape(str(c)) for c in choices]
    answer_shape = shape(str(answer))

    # Find distractor shapes
    distractor_shapes = [shape(str(c)) for c in choices if c != answer]
    if len(distractor_shapes) != 3:
        return None

    # Skim-tell condition: ALL 3 distractors share a shape that the answer
    # doesn't. EXCEPT when integer/decimal/currency/percent are mixed —
    # those are all "numeric" and fine together.
    numeric_family = {"integer", "decimal", "currency", "percent"}
    if all(s == distractor_shapes[0] for s in distractor_shapes):
        # All distractors same shape — does answer match?
        if answer_shape != distractor_shapes[0]:
            # Both in numeric family? OK
            if answer_shape in numeric_family and distractor_shapes[0] in numeric_family:
                return None
            return (
                f"choice_shape_parity: distractors all {distractor_shapes[0]!r} "
                f"but answer is {answer_shape!r} — answer is odd-one-out skim-tell"
            )
    return None


# --------------------------------------------------------------------------
# Gate registry
# --------------------------------------------------------------------------

SOFT_WARN_GATES: frozenset[str] = frozenset({
    "named_equation_when_applicable",
})

PER_QUESTION_GATES: list[tuple[str, Callable[[dict], Optional[str]]]] = [
    ("schema", gate_schema),
    ("no_placeholder_strings", gate_no_placeholder_strings),
    ("trick_context_required", gate_trick_context_required),
    ("stem_length_combat", gate_stem_length_combat),
    ("magnitude_leak", gate_magnitude_leak),
    ("tier_concept_appropriate", gate_tier_concept_appropriate),
    ("choice_shape_parity", gate_choice_shape_parity),
    # Soft-warn
    ("named_equation_when_applicable", gate_named_equation_when_applicable),
]


def run_gates(q: dict) -> dict[str, Optional[str]]:
    return {name: fn(q) for name, fn in PER_QUESTION_GATES}


__all__ = [
    "PER_QUESTION_GATES",
    "SOFT_WARN_GATES",
    "run_gates",
    "gate_schema",
    "gate_no_placeholder_strings",
    "gate_trick_context_required",
    "gate_stem_length_combat",
    "gate_magnitude_leak",
    "gate_tier_concept_appropriate",
    "gate_named_equation_when_applicable",
    "gate_choice_shape_parity",
    "STEM_LENGTH_CAPS",
]
