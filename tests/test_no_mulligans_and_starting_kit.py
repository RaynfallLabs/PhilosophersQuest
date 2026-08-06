"""Tests for the four playtest bugs batched into commit (Group A1, A2, B1+B2).

User direction 2026-05-29:
- A1: NO mulligans in ANY quiz mode. First wrong answer ends the quiz.
- A2: Identified item names display in title case ("Linen Padded",
  not "linen padded").
- B1+B2: Starting common items (iron sword, shortbow, heal potion)
  must be INVISIBLE to the identify system — the kid already knows
  what they got. This means id_level=5 AND added to known_class_ids.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ---------------------------------------------------------------------------
# A1 — Threshold modes end on first wrong (already covered by updated
#      test_threshold_first_wrong_ends_quiz in test_quiz_engine.py).
# This file adds the source-regression check so a future edit that
# re-introduces the "math impossible" early-exit (still tolerant of a
# few wrongs) is flagged immediately.
# ---------------------------------------------------------------------------

def test_quiz_engine_threshold_mode_has_zero_tolerance():
    """Source-regression: _advance in threshold/escalator_threshold
    must end the quiz on `not self.last_correct`. If anyone reverts to
    "early exit when math impossible" the test fails."""
    import quiz_engine
    src = inspect.getsource(quiz_engine.QuizEngine._advance)
    # In the threshold/escalator_threshold branch, the first guard
    # must be a check for last_correct==False (and call _end).
    assert "not self.last_correct" in src, (
        "_advance must end on first wrong answer in threshold modes"
    )
    # The legacy "remaining < required" early-exit is gone
    assert "+ remaining < self.required" not in src, (
        "the old math-impossible early exit must be removed; the new "
        "zero-tolerance rule subsumes it"
    )


# ---------------------------------------------------------------------------
# A2 — compose_*_name title-cases output
# ---------------------------------------------------------------------------

def test_compose_item_name_returns_title_case():
    from items import compose_item_name
    assert compose_item_name("linen", "padded") == "Linen Padded"
    assert compose_item_name("iron", "shortsword") == "Iron Shortsword"


def test_compose_unidentified_name_returns_title_case():
    from items import compose_unidentified_name
    # linen's unidentified_descriptor is "rough fabric"
    assert compose_unidentified_name("rough fabric", "padded") == "Rough Padded"


def test_compose_preserves_existing_caps():
    """If the composed name already has mixed-case (e.g. someone passes
    a proper noun), title-casing must NOT clobber it."""
    from items import compose_item_name
    # "Excalibur sword" already has mixed case — keep it as-is.
    assert compose_item_name("Excalibur", "sword") == "Excalibur sword"


# ---------------------------------------------------------------------------
# B1+B2 — Starting commons are invisible to the identify system
# ---------------------------------------------------------------------------

def test_mark_starting_item_known_fully_identifies_uniformly():
    """Source-regression on the _mark_starting_item_known helper.
    One-question identify model (2026-08-06): ALL starting items
    (unique OR common, no distinction) arrive FULLY identified —
    id_level=5, buc_known, type registered as known."""
    import main
    src = inspect.getsource(main.Game._give_starting_kit)
    helper_idx = src.find("def _mark_starting_item_known")
    assert helper_idx > 0, "helper must exist in _give_starting_kit"
    helper_end = src.find("shard = Item", helper_idx)
    helper_src = src[helper_idx: helper_end]
    assert "id_level = 5" in helper_src, (
        "_mark_starting_item_known must fully identify starting items"
    )
    assert "buc_known = True" in helper_src
    # Marks the id as known so per-id filters treat it consistently
    assert "known_item_ids" in helper_src
    # MUST NOT branch on is_unique — the rule is uniform
    assert "is_unique" not in helper_src, (
        "helper must not split behavior on is_unique — all starting "
        "items are fully identified uniformly"
    )
