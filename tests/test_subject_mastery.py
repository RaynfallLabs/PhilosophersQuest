"""Per-run SUBJECT MASTERY (2026-06-08).

Answer EVERY distinct question in a (subject, tier) correctly in a run and you
master that tier: wrong answers recycle (re-presented), right answers retire,
and once the whole tier deck is cleared it AUTO-SUCCEEDS for the rest of the run
(escalator chains start at your frontier; a fully-mastered subject auto-succeeds
outright). Per-run only -- survives save/load mid-run, resets on a new game.

Full-tier-clear takes a long real run, so this is a logic test (play-test-limits
rule), driven on tiny synthetic banks.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from quiz_engine import QuizEngine, QuizMode


def _q(text, tier):
    return {'question': text, 'choices': [text + '1', text + '2', text + '3', text + '4'],
            'answer': text + '1', 'tier': tier, 'context': ''}


def _engine(subject, qs):
    e = QuizEngine()
    e._cache[subject] = qs           # bypass file loading
    return e


def _play_quiz_all_correct(e, mode, subject, tier, **kw):
    """Run one quiz answering every shown question correctly; advance past the
    result timer manually. Returns the QuizResult."""
    out = []
    e.start_quiz(mode, subject, tier, lambda r: out.append(r), **kw)
    guard = 0
    while e.active and guard < 100:
        guard += 1
        if e.current_question is None:
            break
        e.answer(e.current_question['answer'])
        e._advance()
    return out[0] if out else None


def test_full_tier_size_counts_distinct_questions_at_tier():
    e = _engine('s', [_q('a', 1), _q('b', 1), _q('c', 2)])
    assert e._full_tier_size('s', 1) == 2
    assert e._full_tier_size('s', 2) == 1


def test_clearing_every_question_masters_the_tier():
    e = _engine('s', [_q('a', 1), _q('b', 1)])     # tier 1 has exactly 2
    assert not e.is_mastered('s', 1)
    _play_quiz_all_correct(e, QuizMode.THRESHOLD, 's', 1, threshold=1)
    assert not e.is_mastered('s', 1)               # only 1 of 2 retired
    _play_quiz_all_correct(e, QuizMode.THRESHOLD, 's', 1, threshold=1)
    assert e.is_mastered('s', 1)                   # both retired -> mastered
    assert ('s', 1) in e.mastered_tiers()


def test_right_retires_so_the_deck_shrinks():
    e = _engine('s', [_q('a', 1), _q('b', 1)])
    e.start_quiz(QuizMode.CHAIN, 's', 1, lambda r: None, max_chain=10)
    first = e.current_question['question']
    e.answer(e.current_question['answer'])         # correct -> retire `first`
    assert first in e._retired[('s', 1)]


def test_wrong_does_not_retire_recycles():
    e = _engine('s', [_q('a', 1), _q('b', 1)])
    e.start_quiz(QuizMode.CHAIN, 's', 1, lambda r: None, max_chain=10)
    first = e.current_question['question']
    e.answer('WRONG_CHOICE')                        # wrong -> NOT retired
    assert first not in e._retired.get(('s', 1), set())


def test_mastered_tier_auto_succeeds_without_asking():
    e = _engine('s', [_q('a', 1)])                 # 1-question tier
    _play_quiz_all_correct(e, QuizMode.THRESHOLD, 's', 1, threshold=1)
    assert e.is_mastered('s', 1)
    out = []
    e.start_quiz(QuizMode.THRESHOLD, 's', 1, lambda r: out.append(r), threshold=1)
    assert e.auto_passed >= 1                       # passed without showing a question
    assert out and out[0].success


def test_escalator_starts_at_frontier_when_low_tier_mastered():
    e = _engine('s', [_q('a', 1), _q('b', 2)])
    e._mastered = {('s', 1)}                        # T1 already cleared this run
    e.start_quiz(QuizMode.ESCALATOR_CHAIN, 's', 1, lambda r: None, max_chain=5)
    assert e.auto_passed >= 1                       # T1 auto-passed
    assert e.tier == 2                              # now fighting at T2
    assert e.current_question is not None and e.current_question['tier'] == 2


def test_mastery_is_per_tier_noncontiguous_auto_pass():
    """It's TIER mastery, not subject. A mastered MIDDLE tier auto-passes mid-
    chain while the un-mastered tiers around it are still fought: fight T1 ->
    auto-pass mastered T2 -> fight T3. (T1/T3 get two questions so answering one
    doesn't accidentally master them.)"""
    e = _engine('s', [_q('a1', 1), _q('a2', 1), _q('b', 2), _q('c1', 3), _q('c2', 3)])
    e._mastered = {('s', 2)}                       # ONLY T2 mastered
    asked = []
    e.start_quiz(QuizMode.ESCALATOR_CHAIN, 's', 1, lambda r: None, max_chain=3)
    guard = 0
    while e.active and guard < 30:
        guard += 1
        if e.current_question is None:
            break
        asked.append(e.current_question['tier'])
        e.answer(e.current_question['answer'])
        e._advance()
        if e.celebrating:                          # flush the max-chain celebration
            e.update(2.0)
    assert 2 not in asked                          # T2 auto-passed, never shown
    assert 1 in asked and 3 in asked               # T1 and T3 were fought
    assert e.auto_passed >= 1


def test_fully_mastered_subject_auto_succeeds_outright():
    e = _engine('s', [_q('a', 1), _q('b', 2)])
    e._mastered = {('s', t) for t in range(1, 6)}  # every tier mastered
    out = []
    e.start_quiz(QuizMode.ESCALATOR_CHAIN, 's', 1, lambda r: out.append(r), max_chain=5)
    assert out and out[0].success
    assert e.auto_passed >= 1


def test_fully_mastered_escalator_threshold_succeeds_sphinx_mjolnir():
    """The Sphinx (philosophy) + Mjolnir forge (math) are escalator_threshold T3
    threshold=4 total=6. Mastering tiers 3,4,5 must SUCCEED -- it AUTO-FAILED
    before the fix (3 auto-passes give correct_count=3 < required 4, and the
    capped branch ended success=False, losing the unique reward)."""
    e = _engine('s', [_q(f'q{t}', t) for t in (3, 4, 5)])
    e._mastered = {('s', 3), ('s', 4), ('s', 5)}
    out = []
    e.start_quiz(QuizMode.ESCALATOR_THRESHOLD, 's', 3, lambda r: out.append(r),
                 threshold=4, total_qs=6)
    assert out and out[0].success, "fully-mastered escalator_threshold must succeed"
    assert e.auto_passed == 3


def test_mastery_persists_across_save_load_within_a_run():
    e = _engine('s', [_q('a', 1), _q('b', 1)])
    e._retired = {('s', 1): {'a'}}
    e._mastered = {('s', 2)}
    state = e.get_deck_state()
    e2 = QuizEngine()
    e2.restore_deck_state(state)
    assert e2._retired.get(('s', 1)) == {'a'}
    assert e2.is_mastered('s', 2)


def test_new_game_starts_with_no_mastery():
    e = QuizEngine()
    assert e._mastered == set()
    assert e._retired == {}
