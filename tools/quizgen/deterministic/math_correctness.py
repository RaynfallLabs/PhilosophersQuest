"""Math-correctness gate: verify the claimed answer is mathematically right.

Math has a unique property among quiz subjects: most answers can be
*computed* and checked. This gate sniffs the question shape, evaluates
the expected answer with sympy, and compares to the claimed answer.

Shapes handled (deterministic):
  - Pure arithmetic with ASCII or unicode operators: "7 x 8 = ?", "3 + 4 * 2 = ?"
  - Fractions: "1/2 + 1/3 = ?" (also unicode glyphs like 1/2, 1/3)
  - Percentages: "15% of 80 = ?", "What is 25% of 200?"
  - Powers: "2^5 = ?", "5² = ?"
  - Comparisons: "Which is larger: 2/3 or 3/4?"
  - Solve-for-x equations: "Solve for x: 2x + 5 = 13"
  - Function evaluation: "If f(x) = x + 3, what is f(7)?"
  - Square root: "sqrt(16) = ?" or unicode root

Anything else (word problems, geometry-with-formula, abstract concept,
calculus wonder) returns NA — those fall through to the LLM validator.

A FAIL here is a strong signal: the question is computationally wrong.
The generator/LLM-validator catches some of these, but a deterministic
check is much cheaper and more reliable for the shapes it covers.

Math-only gate. Subjects other than "math" get NA.
"""
from __future__ import annotations

import re
from typing import Any

from sympy import Rational, simplify, solve, sympify
from sympy.core.sympify import SympifyError
from sympy.parsing.sympy_parser import (
    parse_expr,
    implicit_multiplication_application,
    standard_transformations,
)

from tools.quizgen.deterministic.types import GateResult, GateStatus, Question

# unicode fraction glyphs -> ascii fraction strings
_UNICODE_FRACTIONS = {
    "½": "(1/2)",
    "⅓": "(1/3)",
    "⅔": "(2/3)",
    "¼": "(1/4)",
    "¾": "(3/4)",
    "⅕": "(1/5)",
    "⅖": "(2/5)",
    "⅗": "(3/5)",
    "⅘": "(4/5)",
    "⅙": "(1/6)",
    "⅚": "(5/6)",
    "⅐": "(1/7)",
    "⅛": "(1/8)",
    "⅜": "(3/8)",
    "⅝": "(5/8)",
    "⅞": "(7/8)",
    "⅑": "(1/9)",
    "⅒": "(1/10)",
}

# arithmetic operator unicode -> ascii
_UNICODE_OPS = {
    "×": "*",   # ×
    "÷": "/",   # ÷
    "−": "-",   # − (minus sign, U+2212)
    "⁄": "/",   # ⁄ (fraction slash)
    "⋅": "*",   # ⋅ (dot operator, U+22C5)
    "·": "*",   # · (middle dot, U+00B7) — also used for multiplication
}

_TRANSFORMS = standard_transformations + (implicit_multiplication_application,)


_ASCII_X_AS_TIMES_RE = re.compile(r"(\d)\s*x\s*(\d)")

# unicode superscript "digit" set (extended to include minus + decimal point)
_SUPERSCRIPT_DIGITS = "⁰¹²³⁴⁵⁶⁷⁸⁹"
# A superscript run: optional leading super-minus, then super-digits,
# optionally with a middle-dot followed by more super-digits (decimal).
# Crucially, the middle-dot is ONLY consumed when bracketed by super-digits,
# so a standalone `·` (used as multiplication between ascii operands) is
# not eaten here and falls through to _UNICODE_OPS normalization.
_SUPERSCRIPT_RUN_RE = re.compile(
    f"[⁻]?[{_SUPERSCRIPT_DIGITS}]+(?:·[{_SUPERSCRIPT_DIGITS}]+)*"
)
_SUPERSCRIPT_TO_DIGIT = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "⁻": "-",   # superscript minus (U+207B)
    "·": ".",   # middle dot becomes decimal point ONLY inside a super-run
}

# √N or √(N) → sqrt(N) for sympy
_SQRT_GLYPH_RE = re.compile(r"√\s*\(?\s*(\d+(?:\.\d+)?)\s*\)?")


def _collapse_superscripts(text: str) -> str:
    """Replace runs of unicode superscript chars with **(N) (multi-digit aware,
    handles negative exponents and decimals inside the superscript)."""
    def repl(m):
        expanded = "".join(_SUPERSCRIPT_TO_DIGIT.get(c, c) for c in m.group(0))
        return f"**({expanded})"
    return _SUPERSCRIPT_RUN_RE.sub(repl, text)


def _normalize(text: str) -> str:
    """Replace unicode math glyphs with ascii equivalents."""
    if not isinstance(text, str):
        return ""
    for src, dst in _UNICODE_FRACTIONS.items():
        text = text.replace(src, dst)
    # collapse contiguous superscript runs FIRST (e.g., ¹⁰ → **10) before
    # the single-glyph fallback would have mishandled them.
    text = _collapse_superscripts(text)
    for src, dst in _UNICODE_OPS.items():
        text = text.replace(src, dst)
    # informal ascii 'x' between digits = multiplication (common in puzzles)
    text = _ASCII_X_AS_TIMES_RE.sub(r"\1*\2", text)
    # √N or √(N) → sqrt(N) so sympy can parse
    text = _SQRT_GLYPH_RE.sub(r"sqrt(\1)", text)
    # caret -> python power
    text = text.replace("^", "**")
    return text


def _strip_answer(ans: str) -> str:
    """Strip 'x = ' / 'x=' prefix and surrounding whitespace from an answer."""
    s = ans.strip()
    # 'x = 4' -> '4'
    m = re.match(r"^[a-zA-Z]\s*=\s*(.+)$", s)
    if m:
        return m.group(1).strip()
    return s


def _try_parse(expr: str):
    """sympy.parse_expr with implicit multiplication and unicode normalization.

    Returns the parsed sympy expression, or None if it can't parse.
    """
    expr = _normalize(expr)
    try:
        return parse_expr(expr, transformations=_TRANSFORMS, evaluate=True)
    except (SympifyError, SyntaxError, TypeError, ValueError):
        return None


def _eq(actual, expected) -> bool:
    """Compare two sympy values for equality, tolerant of rationals/floats."""
    if actual is None or expected is None:
        return False
    try:
        diff = simplify(actual - expected)
        if diff == 0:
            return True
        # also accept tiny floating-point diff
        as_float = float(diff)
        return abs(as_float) < 1e-9
    except (TypeError, ValueError, AttributeError):
        return False


# ----------------------------------------------------------------------
# shape sniffers — each returns (expected_sympy_value, shape_tag) or None
# ----------------------------------------------------------------------
_PERCENT_OF_RE = re.compile(
    r"(?:what\s+is\s+)?(\d+(?:\.\d+)?)\s*%\s+of\s+(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_SOLVE_RE = re.compile(r"solve(?:\s+for\s+([a-zA-Z]))?\s*:\s*(.+?)(?:\?|$)", re.IGNORECASE)
_FUNCTION_RE = re.compile(
    r"if\s+([a-zA-Z])\s*\(\s*([a-zA-Z])\s*\)\s*=\s*(.+?),\s*"
    r"(?:what\s+is\s+)?\1\s*\(\s*(-?\d+(?:\.\d+)?)\s*\)",
    re.IGNORECASE,
)
_COMPARE_RE = re.compile(
    r"which\s+is\s+(larger|greater|smaller|less|bigger)\s*:?\s*(.+?)\s+or\s+(.+?)\s*\??\s*$",
    re.IGNORECASE,
)
_ARITHMETIC_EQ_RE = re.compile(r"^(.+?)\s*=\s*\??\s*$")
_FRACTION_OF_RE = re.compile(
    r"(?:what\s+is\s+)?(\d+)\s*/\s*(\d+)\s+of\s+(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def _try_percent_of(text: str):
    m = _PERCENT_OF_RE.search(text)
    if not m:
        return None
    pct = sympify(m.group(1))
    base = sympify(m.group(2))
    return (pct * base / 100, "percent_of")


def _try_solve(text: str):
    m = _SOLVE_RE.search(text)
    if not m:
        return None
    var_name = (m.group(1) or "x").lower()
    eq_text = m.group(2).strip()
    if "=" not in eq_text:
        return None
    lhs, rhs = eq_text.split("=", 1)
    lhs_expr = _try_parse(lhs)
    rhs_expr = _try_parse(rhs)
    if lhs_expr is None or rhs_expr is None:
        return None
    try:
        from sympy import Symbol
        var = Symbol(var_name)
        sols = solve(lhs_expr - rhs_expr, var)
        if not sols:
            return None
        if len(sols) == 1:
            return (sols[0], "solve_for_x_single")
        return (sols, "solve_for_x_multi")
    except (NotImplementedError, ValueError, TypeError):
        return None


def _try_function_eval(text: str):
    m = _FUNCTION_RE.search(text)
    if not m:
        return None
    _fn_name, var_name, body, x_val = m.group(1), m.group(2), m.group(3), m.group(4)
    body_expr = _try_parse(body)
    if body_expr is None:
        return None
    try:
        from sympy import Symbol
        var = Symbol(var_name)
        return (body_expr.subs(var, sympify(x_val)), "function_eval")
    except (TypeError, ValueError):
        return None


def _try_compare(text: str):
    m = _COMPARE_RE.search(text)
    if not m:
        return None
    direction = m.group(1).lower()
    a_text, b_text = m.group(2).strip(), m.group(3).strip()
    a_expr = _try_parse(a_text)
    b_expr = _try_parse(b_text)
    if a_expr is None or b_expr is None:
        return None
    try:
        diff = simplify(a_expr - b_expr)
        if diff == 0:
            return (None, "compare_equal")  # signal: equal, distinct shape
        if direction in ("larger", "greater", "bigger"):
            winner_text = a_text if diff > 0 else b_text
        else:  # smaller / less
            winner_text = a_text if diff < 0 else b_text
        return (winner_text, "compare_text")
    except (TypeError, ValueError):
        return None


def _try_fraction_of(text: str):
    """'1/2 of 48 = ?' / 'What is 3/4 of 40?' / '1/3 of 60 = ?'."""
    m = _FRACTION_OF_RE.search(text)
    if not m:
        return None
    num, den, base = m.group(1), m.group(2), m.group(3)
    try:
        return (Rational(int(num), int(den)) * sympify(base), "fraction_of")
    except (ValueError, ZeroDivisionError):
        return None


# Tokens we allow inside a "pure arithmetic" expression — any other
# alphabetic content disqualifies the question (it's prose, not math).
_ARITH_ALLOWED_TOKENS = {"sqrt"}
_ARITH_LETTER_RUN_RE = re.compile(r"[A-Za-z]+")


def _try_pure_arithmetic(text: str):
    """Catch '7 × 8 = ?' / '3 + 4 * 2 = ?' / '2^5 = ?' / 'sqrt(16) = ?' shapes.

    After unicode normalization, the only letter tokens allowed are the
    sympy keywords listed in `_ARITH_ALLOWED_TOKENS`. Any other prose word
    (e.g., 'what', 'is', 'the') disqualifies the question.
    """
    m = _ARITHMETIC_EQ_RE.match(text.strip())
    if not m:
        return None
    expr = m.group(1).strip()
    normalized = _normalize(expr)
    # all alphabetic runs must be in the allowed token set
    for word in _ARITH_LETTER_RUN_RE.findall(normalized):
        if word.lower() not in _ARITH_ALLOWED_TOKENS:
            return None
    try:
        result = parse_expr(normalized, transformations=_TRANSFORMS, evaluate=True)
        return (result, "pure_arithmetic")
    except (SympifyError, SyntaxError, TypeError, ValueError, ZeroDivisionError):
        return None


_SHAPES = [
    _try_function_eval,    # before solve_for_x to grab the "If f(x)=" prefix
    _try_solve,            # specific keyword "Solve"
    _try_compare,          # specific keyword "Which is larger/smaller"
    _try_percent_of,       # specific keyword "% of"
    _try_fraction_of,      # specific keyword "<a/b> of N"
    _try_pure_arithmetic,  # generic fallback (now handles sqrt as well)
]


def _check_shape(question_text: str):
    """Run sniffers in order. Return (expected_value, shape_tag) or None."""
    for fn in _SHAPES:
        result = fn(question_text)
        if result is not None:
            return result
    return None


def _answer_matches(expected: Any, shape_tag: str, claimed: str) -> bool:
    """Compare expected sympy value vs claimed answer string."""
    claimed_clean = _strip_answer(claimed)

    if shape_tag == "compare_text":
        # expected is text of the winning side from the question.
        # First try numeric equality — `0.30` and `0.3` should match.
        expected_norm = _normalize(expected).strip()
        claimed_norm = _normalize(claimed_clean).strip()
        if expected_norm == claimed_norm:
            return True
        exp_val = _try_parse(expected_norm)
        cl_val = _try_parse(claimed_norm)
        return _eq(exp_val, cl_val)

    if shape_tag == "compare_equal":
        # the two sides are equal; answer must say so
        return bool(re.search(r"equal|same", claimed_clean, re.IGNORECASE))

    if shape_tag == "solve_for_x_multi":
        # answer can be "x = 2 or x = 3" — extract numeric tokens, compare as sets
        nums = re.findall(r"-?\d+(?:\.\d+)?(?:/\d+)?", claimed_clean)
        try:
            claimed_set = {sympify(n) for n in nums}
            expected_set = {sympify(v) for v in expected}
            return claimed_set == expected_set
        except (SympifyError, TypeError, ValueError):
            return False

    # default: parse claimed as a single sympy value, compare to expected
    claimed_expr = _try_parse(claimed_clean)
    return _eq(claimed_expr, expected)


def validate_math_correctness(q: Question, subject: str | None = None) -> GateResult:
    """Verify a math question's claimed answer is computationally correct.

    Math-only gate. Returns NA for other subjects, and for math questions
    whose shape isn't recognized (those fall through to LLM validation).
    """
    if subject is not None and subject != "math":
        return GateResult(
            gate="math_correctness",
            status=GateStatus.NA,
            detail=f"Gate is math-only; subject={subject!r}.",
        )

    question_text = q.get("question", "")
    answer = q.get("answer", "")
    if not isinstance(question_text, str) or not isinstance(answer, str):
        return GateResult(
            gate="math_correctness",
            status=GateStatus.NA,
            detail="Schema unfit for correctness check.",
        )

    shape_result = _check_shape(question_text)
    if shape_result is None:
        return GateResult(
            gate="math_correctness",
            status=GateStatus.NA,
            detail="Question shape not recognized; falls through to LLM check.",
        )

    expected, shape_tag = shape_result

    matches = _answer_matches(expected, shape_tag, answer)
    metrics = {
        "shape": shape_tag,
        "expected_str": str(expected),
        "claimed_answer": answer,
    }
    if matches:
        return GateResult(
            gate="math_correctness",
            status=GateStatus.PASS,
            metrics=metrics,
        )
    return GateResult(
        gate="math_correctness",
        status=GateStatus.FAIL,
        detail=f"Computed {expected} via shape {shape_tag!r}; claimed answer {answer!r}",
        metrics=metrics,
    )
