"""Tests for src/quiz_engine.py — the central QuizEngine driving every action.

Covers all 4 modes (threshold, chain, escalator_threshold, escalator_chain),
plus:
- QuizResult shape (success/score/correct/asked)
- Timer math (base_seconds + extra + modifier)
- Tier escalation (capped at 5, deck switch on _escalate)
- Empty-pool graceful fail (no IndexError on missing bank)
- Malformed JSON graceful fail
- max_chain auto-success + celebration path
- Threshold early-exit when math becomes impossible
- Question bank coverage table (every subject has all 5 tiers)

Tests are intentionally hermetic: most use an in-memory question bank
injected via the engine's `_cache` dict, avoiding any dependency on the
shipping bank files.
"""
import json
import os
import sys

import pytest

# Make src/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quiz_engine import QuizEngine, QuizMode, QuizResult, QuizState  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _q(tier: int, q_text: str, answer: str, choices: list[str] | None = None) -> dict:
    """Build a minimal question dict."""
    return {
        'tier': tier,
        'question': q_text,
        'answer': answer,
        'choices': choices or [answer, 'wrong1', 'wrong2', 'wrong3'],
    }


def _build_bank(subject: str = 'math', per_tier: int = 8) -> list[dict]:
    """Build a synthetic question bank: per_tier questions for tiers 1..5."""
    bank = []
    for t in range(1, 6):
        for i in range(per_tier):
            bank.append(_q(t, f'{subject}-T{t}-Q{i}', 'right'))
    return bank


def _make_engine(subject: str = 'math', per_tier: int = 8) -> QuizEngine:
    """Build an engine pre-loaded with a synthetic bank for one subject."""
    eng = QuizEngine()
    eng._cache[subject] = _build_bank(subject, per_tier)
    return eng


def _captured_result() -> tuple[list, callable]:
    """Return (storage_list, callback) — callback appends results to the list."""
    storage: list[QuizResult] = []

    def cb(result):
        storage.append(result)

    return storage, cb


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------

def test_quizresult_fields():
    """QuizResult exposes success/score/correct/asked."""
    r = QuizResult(success=True, score=4, correct=4, asked=5)
    assert r.success is True
    assert r.score == 4
    assert r.correct == 4
    assert r.asked == 5


# ---------------------------------------------------------------------------
# Mode 1: THRESHOLD — must answer X correct
# ---------------------------------------------------------------------------

def test_threshold_success_when_enough_correct():
    """Threshold mode: hits required correct count → success=True, ends immediately."""
    eng = _make_engine()
    results, cb = _captured_result()
    eng.start_quiz('threshold', 'math', tier=1, callback=cb, threshold=2)
    # Need 2 correct out of ceil(2*1.5)=3 questions
    for _ in range(2):
        eng.answer('right')
        eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].correct == 2
    assert results[0].asked == 2
    # Score for threshold mode = correct count (not chain)
    assert results[0].score == 2


def test_threshold_first_wrong_ends_quiz():
    """Threshold mode: zero-tolerance per user direction 2026-05-29.
    Any wrong answer ends the quiz immediately. Replaces the older
    'early exit when math impossible' rule — which was a softer
    variant of the same idea."""
    eng = _make_engine()
    results, cb = _captured_result()
    eng.start_quiz('threshold', 'math', tier=1, callback=cb, threshold=3)
    eng.answer('wrong')
    eng.update(eng.WRONG_DISPLAY_TIME + 0.01)
    assert len(results) == 1
    assert results[0].success is False
    assert results[0].correct == 0
    assert results[0].asked == 1, (
        "first wrong must end the quiz immediately — no mulligans"
    )


def test_threshold_first_wrong_after_partial_correct_ends_quiz():
    """Two right then a wrong → quiz ends with success iff partial >= threshold."""
    eng = _make_engine()
    results, cb = _captured_result()
    eng.start_quiz('threshold', 'math', tier=1, callback=cb, threshold=3)
    for _ in range(2):
        eng.answer('right')
        eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    eng.answer('wrong')
    eng.update(eng.WRONG_DISPLAY_TIME + 0.01)
    assert len(results) == 1
    # 2 correct < 3 threshold -> fail
    assert results[0].success is False
    assert results[0].correct == 2
    assert results[0].asked == 3


# ---------------------------------------------------------------------------
# Mode 2: CHAIN — build combo until wrong
# ---------------------------------------------------------------------------

def test_chain_score_is_chain_length():
    """Chain mode: score = peak chain length, success always True."""
    eng = _make_engine()
    results, cb = _captured_result()
    eng.start_quiz('chain', 'math', tier=1, callback=cb)
    # 4 correct then wrong → chain = 4
    for _ in range(4):
        eng.answer('right')
        eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    eng.answer('wrong')
    eng.update(eng.WRONG_DISPLAY_TIME + 0.01)
    assert len(results) == 1
    assert results[0].success is True   # chain mode always succeeds
    assert results[0].score == 4         # peak chain length
    assert results[0].correct == 4
    assert results[0].asked == 5


def test_chain_first_question_wrong_score_zero():
    """Chain mode: first wrong → chain=0, success=True (score=0)."""
    eng = _make_engine()
    results, cb = _captured_result()
    eng.start_quiz('chain', 'math', tier=1, callback=cb)
    eng.answer('wrong')
    eng.update(eng.WRONG_DISPLAY_TIME + 0.01)
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].score == 0


def test_chain_max_chain_celebration_and_end():
    """Chain mode with max_chain: hitting max_chain triggers celebration → end."""
    eng = _make_engine()
    results, cb = _captured_result()
    eng.start_quiz('chain', 'math', tier=1, callback=cb, max_chain=3)
    for _ in range(3):
        eng.answer('right')
        eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    # At max_chain we go into celebration state, NOT instantly ended
    assert eng.celebrating is True
    assert eng.celebration_text == 'MAX CHAIN!'
    # Tick the celebration timer to expiry
    eng.update(2.0)
    assert len(results) == 1
    assert results[0].score == 3
    assert results[0].success is True


# ---------------------------------------------------------------------------
# Mode 3: ESCALATOR_THRESHOLD — questions get harder each round
# ---------------------------------------------------------------------------

def test_escalator_threshold_escalates_tier_each_question():
    """Escalator threshold: tier bumps up after each question (capped at 5)."""
    eng = _make_engine()
    results, cb = _captured_result()
    eng.start_quiz('escalator_threshold', 'math', tier=1, callback=cb, threshold=3)
    # 1st q answered correct → tier escalates before next question
    eng.answer('right')
    assert eng.tier == 1   # tier doesn't change DURING current question
    eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    # Now we should be on tier 2 question
    assert eng.tier == 2
    eng.answer('right')
    eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    assert eng.tier == 3
    eng.answer('right')
    eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    # 3 correct — threshold met, quiz ends
    assert len(results) == 1
    assert results[0].success is True


def test_escalator_threshold_tier_caps_at_5():
    """Escalator threshold: tier caps at 5 after multiple correct answers."""
    eng = _make_engine()
    results, cb = _captured_result()
    eng.start_quiz('escalator_threshold', 'math', tier=4, callback=cb, threshold=10, total_qs=10)
    # Tier 4 → 5 after first correct
    eng.answer('right')
    eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    assert eng.tier == 5
    # Tier 5 → still 5 after another correct (capped)
    eng.answer('right')
    eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    assert eng.tier == 5


# ---------------------------------------------------------------------------
# Mode 4: ESCALATOR_CHAIN — tiers ramp, chain ends on wrong
# ---------------------------------------------------------------------------

def test_escalator_chain_tier_climbs_each_rung():
    """Escalator chain: each correct answer bumps tier."""
    eng = _make_engine()
    _, cb = _captured_result()
    eng.start_quiz('escalator_chain', 'math', tier=1, callback=cb, max_chain=5)
    eng.answer('right')
    eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    assert eng.tier == 2
    eng.answer('right')
    eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    assert eng.tier == 3


def test_escalator_chain_score_is_chain_length():
    """Escalator chain: score = chain length (matches CHAIN mode shape)."""
    eng = _make_engine()
    results, cb = _captured_result()
    eng.start_quiz('escalator_chain', 'math', tier=1, callback=cb, max_chain=5)
    for _ in range(3):
        eng.answer('right')
        eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    eng.answer('wrong')
    eng.update(eng.WRONG_DISPLAY_TIME + 0.01)
    assert len(results) == 1
    assert results[0].score == 3
    assert results[0].correct == 3
    assert results[0].asked == 4


def test_escalator_chain_max_chain_celebrates_and_ends():
    """Escalator chain hitting max_chain triggers celebration then ends."""
    eng = _make_engine()
    results, cb = _captured_result()
    eng.start_quiz('escalator_chain', 'math', tier=1, callback=cb, max_chain=5)
    for _ in range(5):
        eng.answer('right')
        eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    assert eng.celebrating is True
    eng.update(2.0)
    assert len(results) == 1
    assert results[0].score == 5


# ---------------------------------------------------------------------------
# Timer math
# ---------------------------------------------------------------------------

def test_timer_base_seconds_plus_extra():
    """base_seconds + extra_seconds is the effective timer."""
    eng = _make_engine()
    _, cb = _captured_result()
    eng.start_quiz('threshold', 'math', tier=1, callback=cb,
                   base_seconds=40, extra_seconds=5)
    # round(40 * 1.0) + 5 = 45
    assert eng.timer_seconds == 45
    assert eng.time_remaining == 45.0


def test_timer_modifier_scales_base_only():
    """timer_modifier scales base_seconds; extra_seconds is added AFTER."""
    eng = _make_engine()
    _, cb = _captured_result()
    eng.start_quiz('threshold', 'math', tier=1, callback=cb,
                   base_seconds=40, extra_seconds=10, timer_modifier=0.5)
    # round(40 * 0.5) + 10 = 30
    assert eng.timer_seconds == 30


def test_timer_legacy_fallback_uses_wisdom():
    """Without base_seconds, falls back to legacy (10 + wisdom) formula."""
    eng = _make_engine()
    _, cb = _captured_result()
    eng.start_quiz('threshold', 'math', tier=1, callback=cb, wisdom=15)
    # round((10 + 15) * 1.0) + 0 = 25
    assert eng.timer_seconds == 25


def test_timer_expiry_fails_quiz_and_advances():
    """Timer hitting 0 mid-question counts as a wrong answer."""
    eng = _make_engine()
    results, cb = _captured_result()
    eng.start_quiz('chain', 'math', tier=1, callback=cb, base_seconds=5)
    # Eat all 5 seconds — engine should auto-fail the question
    eng.update(5.5)
    # Now we're in RESULT state with last_correct=False
    assert eng.last_correct is False
    assert eng.chain == 0
    # And the result phase ticks down → ends the quiz
    eng.update(eng.WRONG_DISPLAY_TIME + 0.01)
    # Timer-expired in chain mode: still success=True (chain mode never "fails")
    # but score = 0 because no chain was built
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].score == 0


# ---------------------------------------------------------------------------
# Question bank loading
# ---------------------------------------------------------------------------

def test_empty_bank_fails_gracefully():
    """Missing question file should NOT crash; quiz fails cleanly with success=False."""
    eng = QuizEngine()
    eng._cache['no_such_subject'] = []   # simulate empty load
    results, cb = _captured_result()
    eng.start_quiz('threshold', 'no_such_subject', tier=1, callback=cb)
    # Callback fired with failure result — no IndexError, no hang
    assert len(results) == 1
    assert results[0].success is False
    assert results[0].correct == 0
    assert results[0].asked == 0


def test_load_questions_handles_malformed_json(tmp_path, monkeypatch):
    """load_questions catches JSONDecodeError and returns empty list."""
    # Build a malformed JSON file in a temp dir and point the engine at it.
    bad_file = tmp_path / 'broken.json'
    bad_file.write_text('{ this is not valid json', encoding='utf-8')

    import quiz_engine as qe_mod
    monkeypatch.setattr(qe_mod, '_QUESTIONS_DIR', str(tmp_path))

    eng = QuizEngine()
    out = eng.load_questions('broken')
    assert out == []


def test_question_bank_coverage_all_subjects_all_tiers():
    """Every subject in SUBJECT_TIMER has T1..T5 questions on disk."""
    from player import Player
    subjects = list(Player.SUBJECT_TIMER.keys())

    # Use the real engine to load each bank
    eng = QuizEngine()
    missing = []
    for subj in subjects:
        bank = eng.load_questions(subj)
        if not bank:
            missing.append((subj, 'EMPTY BANK'))
            continue
        tiers_present = {q.get('tier', 1) for q in bank}
        for t in (1, 2, 3, 4, 5):
            if t not in tiers_present:
                missing.append((subj, f'missing tier {t}'))
    assert not missing, f'Bank coverage gaps: {missing}'


# ---------------------------------------------------------------------------
# Deck / question selection invariants
# ---------------------------------------------------------------------------

def test_deck_uses_only_requested_tier():
    """Deck for tier 3 contains only T3 questions (no T1/T2 spill)."""
    eng = _make_engine()
    _, cb = _captured_result()
    eng.start_quiz('threshold', 'math', tier=3, callback=cb, threshold=1)
    deck = eng._decks[('math', 3)]
    assert all(q.get('tier', 1) == 3 for q in deck)


def test_deck_persists_across_sessions():
    """Repeated quizzes at same subject/tier resume from prior position."""
    eng = _make_engine()
    _, cb = _captured_result()
    # First quiz
    eng.start_quiz('threshold', 'math', tier=1, callback=cb, threshold=1)
    first_q = eng.current_question
    eng.answer('right')
    eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    # Second quiz — should resume from next deck position
    eng.start_quiz('threshold', 'math', tier=1, callback=cb, threshold=1)
    second_q = eng.current_question
    assert second_q is not first_q
    # Deck index advanced
    assert eng._deck_idx[('math', 1)] > 0


# ---------------------------------------------------------------------------
# answer() state machine
# ---------------------------------------------------------------------------

def test_answer_noop_outside_asking_state():
    """answer() returns False when not in ASKING state."""
    eng = _make_engine()
    _, cb = _captured_result()
    eng.start_quiz('threshold', 'math', tier=1, callback=cb, threshold=1)
    eng.answer('right')   # enters RESULT state
    assert eng.state == QuizState.RESULT
    # Second call in RESULT state is a no-op
    out = eng.answer('right')
    assert out is False


def test_answer_is_whitespace_insensitive_but_case_exact():
    """Answers are whitespace-stripped but case-EXACT (bug bash 2026-06-01).

    Previously the engine .lower()'d both sides, which made grammar
    capitalization questions impossible to grade — all 4 case-variants
    collapsed to the same string and ANY pick registered correct. The
    fix is exact case; whitespace stripping is preserved so trailing
    spaces on multi-line render still match."""
    eng = _make_engine()
    _, cb = _captured_result()
    eng.start_quiz('chain', 'math', tier=1, callback=cb)
    assert eng.answer('  right  ') is True   # whitespace OK
    assert eng.answer('  RIGHT  ') is False  # case must match
    assert eng.chain == 1                      # only the first one counted


# ---------------------------------------------------------------------------
# Mode string vs QuizMode enum
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('mode_str', ['threshold', 'chain', 'escalator_threshold', 'escalator_chain'])
def test_start_quiz_accepts_mode_strings(mode_str):
    """All four mode strings are valid inputs to start_quiz."""
    eng = _make_engine()
    _, cb = _captured_result()
    eng.start_quiz(mode_str, 'math', tier=1, callback=cb)
    assert isinstance(eng.mode, QuizMode)
    assert eng.mode.value == mode_str


def test_invalid_mode_string_raises():
    """Passing an unrecognized mode raises ValueError."""
    eng = _make_engine()
    _, cb = _captured_result()
    with pytest.raises(ValueError):
        eng.start_quiz('totally_invalid_mode', 'math', tier=1, callback=cb)


# ---------------------------------------------------------------------------
# Active / inactive predicate
# ---------------------------------------------------------------------------

def test_active_property_lifecycle():
    """active = True only while a quiz is running."""
    eng = QuizEngine()
    assert eng.active is False
    eng._cache['math'] = _build_bank('math', 4)
    _, cb = _captured_result()
    eng.start_quiz('chain', 'math', tier=1, callback=cb)
    assert eng.active is True
    eng.answer('wrong')
    eng.update(eng.WRONG_DISPLAY_TIME + 0.01)
    assert eng.active is False
    assert eng.state == QuizState.COMPLETE


# ---------------------------------------------------------------------------
# Timed vs untimed policy (2026-05-29 timer-policy change)
# ---------------------------------------------------------------------------
#
# Policy: combat math attack is the ONE timed action. Every other quiz
# (identify, lockpick, equip, prayer, cooking, magic, etc.) is untimed
# so the kid can READ the substantive bank content. start_quiz auto-
# detects via `subject == 'math'`; an explicit `timed=` kwarg overrides.


def test_timed_defaults_to_true_for_math():
    eng = QuizEngine()
    eng._cache['math'] = _build_bank('math', 2)
    _, cb = _captured_result()
    eng.start_quiz('chain', 'math', tier=1, callback=cb)
    assert eng.timed is True
    assert eng.timer_seconds > 0
    assert eng.time_remaining > 0


def test_timed_defaults_to_false_for_non_math_subjects():
    for subject in ('philosophy', 'economics', 'theology', 'cooking',
                     'science', 'history', 'geography', 'grammar',
                     'animal', 'ai', 'trivia'):
        eng = QuizEngine()
        eng._cache[subject] = _build_bank(subject, 2)
        _, cb = _captured_result()
        eng.start_quiz('threshold', subject, tier=1, callback=cb, threshold=2)
        assert eng.timed is False, f"{subject} should be untimed by default"
        assert eng.timer_seconds == 0
        assert eng.time_remaining == 0.0


def test_timed_explicit_override_true():
    """Caller can force a timer on a non-math quiz if a future feature needs it."""
    eng = QuizEngine()
    eng._cache['philosophy'] = _build_bank('philosophy', 2)
    _, cb = _captured_result()
    eng.start_quiz('threshold', 'philosophy', tier=1, callback=cb,
                    threshold=2, timed=True, base_seconds=20)
    assert eng.timed is True
    assert eng.timer_seconds > 0


def test_timed_explicit_override_false_for_math():
    """And conversely — caller can force-untime a math quiz for a debug/menu use."""
    eng = QuizEngine()
    eng._cache['math'] = _build_bank('math', 2)
    _, cb = _captured_result()
    eng.start_quiz('chain', 'math', tier=1, callback=cb, timed=False)
    assert eng.timed is False
    assert eng.timer_seconds == 0


def test_untimed_quiz_update_does_not_tick():
    """update(dt) must NOT decrement an untimed quiz's clock — it starts
    at 0 and any decrement would auto-fail the quiz instantly."""
    eng = QuizEngine()
    eng._cache['philosophy'] = _build_bank('philosophy', 4)
    _, cb = _captured_result()
    eng.start_quiz('escalator_chain', 'philosophy', tier=1, callback=cb,
                    max_chain=5)
    assert eng.timed is False
    assert eng.time_remaining == 0.0
    # Tick a generous amount; the quiz must remain ASKING.
    eng.update(60.0)
    assert eng.state == QuizState.ASKING
    assert eng.active is True
    # time_remaining stays 0 — never decremented.
    assert eng.time_remaining == 0.0


def test_untimed_quiz_completes_via_chain_fail_not_timer():
    """An untimed escalator-chain quiz must end when the kid gets one
    wrong, NOT when the (zero) timer 'runs out' on the first _advance."""
    eng = QuizEngine()
    eng._cache['philosophy'] = _build_bank('philosophy', 4)
    results, cb = _captured_result()
    eng.start_quiz('escalator_chain', 'philosophy', tier=1, callback=cb,
                    max_chain=5)
    eng.answer(eng.current_question['answer'])  # right
    eng.update(eng.RESULT_DISPLAY_TIME + 0.01)
    assert eng.active is True  # still going, not timer-ended
    eng.answer('wrong')
    eng.update(eng.WRONG_DISPLAY_TIME + 0.01)
    assert eng.active is False
    assert results[0].score == 1
