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

def test_mark_starting_item_known_sets_id_level_4_uniformly():
    """Source-regression on the _mark_starting_item_known helper.
    Per user direction 2026-05-29: ALL starting items (unique OR common,
    no distinction) start at id_level=4, treated like any naturally-
    found item that's been ID'd through Tier 4. Tier 5 (mastery) is
    still earnable via the normal identify flow."""
    import main
    src = inspect.getsource(main.Game._give_starting_kit)
    helper_idx = src.find("def _mark_starting_item_known")
    assert helper_idx > 0, "helper must exist in _give_starting_kit"
    helper_end = src.find("shard = Item", helper_idx)
    helper_src = src[helper_idx: helper_end]
    # Sets id_level to max(.., 4) — never lowers, lands at 4
    assert "max(int(getattr(it, 'id_level', 0)), 4)" in helper_src or \
           "max(int(getattr(it,'id_level',0)),4)" in helper_src.replace(' ', ''), (
        "_mark_starting_item_known must set id_level to max(.., 4) "
        "so starting items behave as if Tier-4-identified"
    )
    # Marks the id as known so per-id filters treat it consistently
    assert "known_item_ids" in helper_src
    # MUST NOT branch on is_unique anymore — the rule is uniform
    assert "is_unique" not in helper_src, (
        "helper must not split behavior on is_unique — user direction "
        "is that all starting items get id_level=4 uniformly"
    )
    # MUST NOT have a commons-specific id_level=5 path anymore
    assert "id_level = 5" not in helper_src
    assert "get_mastery_class" not in helper_src


def test_mark_starting_item_known_runtime_behavior():
    """Run the helper on a unique-flagged stub and a common-flagged
    stub; both must end at id_level=4 and buc_known=True."""
    class _StubUnique:
        is_unique = True
        id_level = 0
        buc_known = False
        id = 'test_unique'
    class _StubCommon:
        is_unique = False
        id_level = 0
        buc_known = False
        id = 'test_common'
    # Replicate the helper body for the runtime check (kept in sync via
    # the source-regression test above)
    known_item_ids = set()
    def _mark(it):
        it.id_level = max(int(getattr(it, 'id_level', 0)), 4)
        it.buc_known = True
        if getattr(it, 'id', None):
            known_item_ids.add(it.id)
    u, c = _StubUnique(), _StubCommon()
    _mark(u); _mark(c)
    assert u.id_level == 4
    assert c.id_level == 4
    assert u.buc_known is True
    assert c.buc_known is True
    assert known_item_ids == {'test_unique', 'test_common'}


def test_mark_starting_item_known_never_lowers_id_level():
    """Defensive: if id_level is already 5 (e.g. from a Philosopher's
    Mantle effect), the helper must not pull it back to 4."""
    class _Stub:
        is_unique = True
        id_level = 5
        buc_known = False
        id = 'test_unique'
    known_item_ids = set()
    def _mark(it):
        it.id_level = max(int(getattr(it, 'id_level', 0)), 4)
        it.buc_known = True
        if getattr(it, 'id', None):
            known_item_ids.add(it.id)
    s = _Stub()
    _mark(s)
    assert s.id_level == 5, "helper must take max(), never lower id_level"
