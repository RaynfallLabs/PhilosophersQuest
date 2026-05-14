"""Length-budget gate: total record cost (question + 4 choices) must fit
the per-tier parse budget so the question can be read inside the in-game
timer window.

Per philosophy.md §1 (and analogous per-subject specs): T1-T3 budget is
600 chars; T4-T5 is 800. The pipeline reads the budget from the per-
subject spec, but the defaults here match philosophy and are the right
floor for the rest until each subject's spec is added.

If we later need per-subject budgets, expose them through specs.py rather
than hardcoding here.
"""
from __future__ import annotations

from tools.quizgen.deterministic.types import GateResult, GateStatus, Question

# Tier -> target record budget in chars (question + 4 choices). Per
# philosophy.md §2, the hard rejection threshold is target * (1 + GRACE).
# Caps bumped 2026-05-11 to enable scaffolding-over-compression — kids
# need room in the prompt to learn unfamiliar concepts. T1 stays tight
# (it's the image-led entry tier and the timer was always generous for it).
DEFAULT_TIER_BUDGETS: dict[int, int] = {
    1: 600,    # image-led entry — keep tight
    2: 700,    # famous ideas with scaffolded surprise
    3: 750,    # less-famous moves; room for inline glosses
    4: 950,    # technical move via consequence; room to teach the move
    5: 1000,   # hard problems / sophisticated disputes
}

# Per-subject budget overrides. Where not listed, default applies.
# Cooking budgets come from `docs/quiz/subjects/cooking.md` §2.
SUBJECT_TIER_BUDGETS: dict[str, dict[int, int]] = {
    "cooking":   {1: 280, 2: 480, 3: 680, 4: 900, 5: 1100},
    "animal":    {1: 280, 2: 480, 3: 680, 4: 900, 5: 1100},
    "science":   {1: 280, 2: 480, 3: 680, 4: 900, 5: 1100},
    "ai":        {1: 280, 2: 480, 3: 680, 4: 900, 5: 1100},
    "geography": {1: 280, 2: 480, 3: 680, 4: 900, 5: 1100},
    "history":   {1: 280, 2: 480, 3: 680, 4: 900, 5: 1100},
    "theology":  {1: 280, 2: 480, 3: 680, 4: 900, 5: 1100},
}

GRACE_FACTOR = 1.05  # +5% per philosophy.md §2


def validate_length_budget(
    q: Question,
    tier_budgets: dict[int, int] | None = None,
    subject: str | None = None,
) -> GateResult:
    if tier_budgets is None:
        if subject in SUBJECT_TIER_BUDGETS:
            tier_budgets = SUBJECT_TIER_BUDGETS[subject]
        else:
            tier_budgets = DEFAULT_TIER_BUDGETS
    tier = q.get("tier")
    question_text = q.get("question", "")
    choices = q.get("choices") or []
    if not isinstance(question_text, str) or not isinstance(choices, list):
        return GateResult(
            gate="length_budget",
            status=GateStatus.NA,
            detail="Schema unfit for budget check.",
        )

    total = len(question_text) + sum(len(c) for c in choices if isinstance(c, str))
    target = tier_budgets.get(tier, max(tier_budgets.values()))
    hard_cap = int(target * GRACE_FACTOR)
    metrics = {
        "total_chars": total,
        "tier": tier,
        "target": target,
        "hard_cap": hard_cap,
        "question_chars": len(question_text),
        "choices_chars": [len(c) if isinstance(c, str) else 0 for c in choices],
    }

    if total > hard_cap:
        return GateResult(
            gate="length_budget",
            status=GateStatus.FAIL,
            detail=f"Total record cost {total} chars > tier {tier} hard cap {hard_cap} (target {target} + 5%)",
            metrics=metrics,
        )
    return GateResult(gate="length_budget", status=GateStatus.PASS, metrics=metrics)
