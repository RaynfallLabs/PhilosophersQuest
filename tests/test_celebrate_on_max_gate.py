"""Phase 0 + Phase 1 (CHAIN_EFFECTS_PLAN, 2026-10-03) -- celebrate_on_max
gate + session id + opt-in call-site migration.

Verifies:
  * `celebrate_on_max` defaults to False; hitting max_chain ends the quiz
    silently (no full-screen "MAX CHAIN!" takeover).
  * `celebrate_on_max=True` is retained on the QuizEngine API as an
    escape hatch; the kwarg still sets `celebrating=True` when passed.
  * The quiz still completes cleanly at max_chain when celebration is
    skipped -- on_complete fires with success=True and score=chain.
  * `session_id` is monotonically increasing, and two consecutive
    zero-chain quizzes get distinct ids (the design-doc problem).
  * **Phase 1 migration**: the two former opt-in call sites now drive
    the celebration via `effects_runtime.fire(...)` instead of the
    engine's celebrating flag. NO src/ file passes
    `celebrate_on_max=True` to `start_quiz` anymore.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make src/ importable
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / 'src'))

from quiz_engine import QuizEngine, QuizMode  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _q(tier: int, text: str, answer: str = 'right') -> dict:
    return {
        'tier': tier,
        'question': text,
        'answer': answer,
        'choices': [answer, 'wrong1', 'wrong2', 'wrong3'],
    }


def _make_engine(subject: str = 'math') -> QuizEngine:
    eng = QuizEngine()
    bank = []
    for t in range(1, 6):
        for i in range(8):
            bank.append(_q(t, f'{subject}-T{t}-Q{i}'))
    eng._cache[subject] = bank
    return eng


def _results_sink():
    out: list = []

    def cb(result):
        out.append(result)

    return out, cb


# ---------------------------------------------------------------------------
# celebrate_on_max gating
# ---------------------------------------------------------------------------

def test_default_celebrate_on_max_is_false():
    """Default chain quiz: hitting max_chain does NOT set `celebrating`.

    This is the Phase 0 contract — the ~22 non-opt-in call sites must not
    trigger the full-screen takeover anymore.
    """
    eng = _make_engine()
    results, cb = _results_sink()
    eng.start_quiz('chain', 'math', tier=1, callback=cb, max_chain=3)
    for _ in range(3):
        eng.answer('right')
        eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    assert eng.celebrating is False
    # The quiz must have ended immediately (not held for 1.5s of celebration).
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].score == 3


def test_celebrate_on_max_true_sets_celebrating():
    """Opt-in chain quiz: hitting max_chain DOES set `celebrating`."""
    eng = _make_engine()
    results, cb = _results_sink()
    eng.start_quiz('chain', 'math', tier=1, callback=cb, max_chain=3,
                   celebrate_on_max=True)
    for _ in range(3):
        eng.answer('right')
        eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    assert eng.celebrating is True
    assert eng.celebration_text == 'MAX CHAIN!'
    # Quiz does not end until the celebration timer runs out.
    assert len(results) == 0
    eng.update(2.0)
    assert len(results) == 1
    assert results[0].success is True


def test_quiz_still_completes_when_celebration_skipped():
    """Chain mode with max_chain=5 and celebrate_on_max=False: five correct
    answers trigger on_complete with success=True and score=5. Confirms the
    _advance() rework still ends the quiz cleanly without the celebration
    hold."""
    eng = _make_engine()
    results, cb = _results_sink()
    eng.start_quiz('chain', 'math', tier=1, callback=cb, max_chain=5)
    for _ in range(5):
        eng.answer('right')
        eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    assert eng.celebrating is False
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].score == 5
    # And the engine is no longer "active" — we're in COMPLETE state.
    assert eng.active is False


def test_escalator_chain_default_does_not_celebrate():
    """Same gate for escalator_chain — the mode used by every routine
    chain quiz in the codebase (prayer, equip, hero specials, …)."""
    eng = _make_engine()
    results, cb = _results_sink()
    eng.start_quiz('escalator_chain', 'math', tier=1, callback=cb, max_chain=5)
    for _ in range(5):
        eng.answer('right')
        eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    assert eng.celebrating is False
    assert len(results) == 1
    assert results[0].score == 5


# ---------------------------------------------------------------------------
# session_id
# ---------------------------------------------------------------------------

def test_session_id_monotonic():
    """Two sequential start_quiz calls yield strictly-increasing session ids."""
    eng = _make_engine()
    _, cb = _results_sink()
    eng.start_quiz('chain', 'math', tier=1, callback=cb)
    first = eng.session_id
    eng.start_quiz('chain', 'math', tier=1, callback=cb)
    second = eng.session_id
    assert first > 0
    assert second > first


def test_session_id_distinct_for_zero_chain_quizzes():
    """Two consecutive chain quizzes that both end at chain 0 (first-answer
    miss) must still produce distinct session_ids. This is the exact
    problem the design doc flags — downstream effects can't tell two
    identical zero-chain sessions apart without this counter."""
    eng = _make_engine()
    results, cb = _results_sink()

    # Session 1 — miss immediately.
    eng.start_quiz('chain', 'math', tier=1, callback=cb)
    sid1 = eng.session_id
    eng.answer('wrong')
    eng.update(eng.WRONG_DISPLAY_TIME + 0.01)
    assert results[-1].score == 0

    # Session 2 — miss immediately again.
    eng.start_quiz('chain', 'math', tier=1, callback=cb)
    sid2 = eng.session_id
    eng.answer('wrong')
    eng.update(eng.WRONG_DISPLAY_TIME + 0.01)
    assert results[-1].score == 0

    assert sid1 != sid2
    assert sid2 == sid1 + 1


def test_session_id_increments_even_on_aborted_quiz():
    """A quiz with an empty bank aborts via `_end(success=False)` in
    start_quiz. The session id must still have been bumped BEFORE that
    early return, otherwise the next quiz would share this quiz's id."""
    eng = QuizEngine()
    eng._cache['math'] = []  # empty bank -> aborted start
    _, cb = _results_sink()
    before = eng.session_id
    eng.start_quiz('chain', 'math', tier=1, callback=cb)
    aborted = eng.session_id
    eng.start_quiz('chain', 'math', tier=1, callback=cb)
    after = eng.session_id
    assert aborted == before + 1
    assert after == aborted + 1


# ---------------------------------------------------------------------------
# Legitimate opt-in call sites (static grep check)
# ---------------------------------------------------------------------------

_SRC = Path(__file__).resolve().parent.parent / 'src'


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_divine_intercession_fires_takeover():
    """Phase 1 migration: `game_divine.py::_confirm_divine_intercession`
    no longer passes `celebrate_on_max=True`; instead, on quiz success
    it fires the ``divine_intercession_takeover`` effect via the
    EffectsRuntime so the celebration animates post-quiz."""
    text = _read(_SRC / 'game_divine.py')
    marker = 'def _confirm_divine_intercession'
    assert marker in text, "Could not find _confirm_divine_intercession in game_divine.py"
    body = text[text.index(marker):]
    # Narrow to just this method (stop at the next def).
    next_def = body.index('\n    def ', 10)
    body = body[:next_def]
    assert "'divine_intercession_takeover'" in body or '"divine_intercession_takeover"' in body, (
        "Divine Intercession must fire the divine_intercession_takeover "
        "effect in its on_complete callback. Phase 1 migration missing."
    )
    assert 'celebrate_on_max=True' not in body, (
        "Divine Intercession's start_quiz call should NO LONGER pass "
        "celebrate_on_max=True after Phase 1 migration. The takeover "
        "is driven by effects_runtime.fire() instead."
    )


def test_unicorn_fires_takeover():
    """Phase 1 migration: `game_encounters.py::_start_unicorn_quiz`
    no longer passes `celebrate_on_max=True`; instead, on quiz success
    it fires the ``unicorn_bond_takeover`` effect."""
    text = _read(_SRC / 'game_encounters.py')
    marker = 'def _start_unicorn_quiz'
    assert marker in text, "Could not find _start_unicorn_quiz in game_encounters.py"
    body = text[text.index(marker):]
    next_def = body.index('\n    def ', 10)
    body = body[:next_def]
    assert "'unicorn_bond_takeover'" in body or '"unicorn_bond_takeover"' in body, (
        "Unicorn boon must fire the unicorn_bond_takeover effect in "
        "its on_complete callback. Phase 1 migration missing."
    )
    assert 'celebrate_on_max=True' not in body, (
        "Unicorn boon start_quiz should NO LONGER pass "
        "celebrate_on_max=True after Phase 1 migration."
    )


def test_no_src_file_opts_in_anymore():
    """Phase 1: ``celebrate_on_max=True`` is a legacy escape hatch kept
    on the QuizEngine API but never passed by any live call site. If a
    third opt-in appears the author should justify it in the plan
    before relaxing this test."""
    offenders: list[str] = []
    for py in _SRC.rglob('*.py'):
        if py.name == 'quiz_engine.py':
            # Definition site -- the kwarg appears in signature + docstring.
            continue
        if 'celebrate_on_max=True' in py.read_text(encoding='utf-8'):
            offenders.append(str(py.relative_to(_SRC)))
    assert not offenders, (
        "No src/ file should opt into celebrate_on_max=True after "
        f"Phase 1 migration. Unexpected sites: {offenders}"
    )
