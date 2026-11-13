"""Math grade-band gate: a maths question must sit inside its tier's band.

Each tier is a band on the school-grade score from
tools/balance/math_difficulty.py (T1 grades 1-2, T2 3-4, T3 4-5, T4 6-7,
T5 7-8; the bands live in tools/balance/math_grade_curve.json), and each
topic names the tiers it may appear at. This gate fails a question that
scores outside its tier's band, whose topic has no grade band at its tier,
that needs no real work (times 0 or 1, the root of 1) above tier 1, or
whose stem the scorer cannot read.

The fix is never a hand edit: run ``py -m tools.balance.math_grade_curve``,
which moves or replaces out-of-band questions (see docs/quiz/math_grade_curve.md).

Math-only gate. Subjects other than "math" get NA.
"""
from __future__ import annotations

from tools.balance import math_difficulty as md
from tools.quizgen.deterministic.types import GateResult, GateStatus, Question

GATE = "math_grade_band"


def validate_math_grade_band(q: Question, subject: str = "math") -> GateResult:
    if subject != "math":
        return GateResult(GATE, GateStatus.NA, f"Subject {subject!r} has no grade bands.")
    try:
        tier = int(q.get("tier", 0))
        lo, hi = md.tier_band(tier)
    except (KeyError, ValueError, TypeError):
        return GateResult(GATE, GateStatus.FAIL, f"no grade band for tier {q.get('tier')!r}")
    try:
        r = md.rate(q)
    except md.UnratedQuestion as e:
        return GateResult(GATE, GateStatus.FAIL, f"the scorer cannot read this stem: {e}")
    metrics = {"score": r.score, "band": [lo, hi], "kind": r.kind, "digits": r.digits,
               "steps": r.steps, "regroups": r.regroups}
    if r.trivial and tier > 1:
        return GateResult(GATE, GateStatus.FAIL, "needs no real work (times 0 or 1, a power or root of 1)", metrics)
    if not lo <= r.score < hi:
        side = "below" if r.score < lo else "above"
        return GateResult(GATE, GateStatus.FAIL,
                          f"score {r.score:.2f} is {side} the tier {tier} band [{lo}, {hi})", metrics)
    topic = q.get("topic", "")
    if tier not in md.allowed_tiers(topic):
        return GateResult(GATE, GateStatus.FAIL,
                          f"topic {topic!r} has no grade band at tier {tier}", metrics)
    return GateResult(GATE, GateStatus.PASS, "", metrics)
