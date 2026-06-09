"""Save decks must not serve stale questions after a bank update (2026-06-06).

The quiz engine used to pickle the shuffled deck's question OBJECTS into the
save; on load it re-installed them, so a rebuilt/expanded question bank never
reached a loaded game — the player kept seeing the old questions (e.g. the whole
philosophy rebuild was invisible to an existing save). Now only the seen-set is
persisted and decks rebuild from the current JSON on load.
"""
from quiz_engine import QuizEngine


def test_restore_does_not_serve_stale_pickled_questions():
    e = QuizEngine()
    # A save from BEFORE a bank update: its deck holds a question that no longer
    # exists in the current bank.
    e.restore_deck_state({
        'decks': {('math', 1): [{'question': 'STALE OLD Q', 'answer': 'a',
                                 'choices': ['a', 'b', 'c', 'd']}]},
        'deck_idx': {('math', 1): 0},
        'last_q': {},
        'seen': {('math', 1): {'STALE OLD Q'}},
    })
    e.start_quiz('chain', 'math', 1, callback=lambda r: None, max_chain=5)
    current = {q['question'] for q in e.load_questions('math')}
    assert e.current_question['question'] != 'STALE OLD Q'
    assert e.current_question['question'] in current


def test_seen_set_still_persists_but_decks_do_not():
    e = QuizEngine()
    e.restore_deck_state({
        'decks': {('math', 1): [{'question': 'x', 'answer': 'a', 'choices': ['a']}]},
        'seen': {('math', 1): {'some seen text'}},
    })
    assert e._seen.get(('math', 1)) == {'some seen text'}   # anti-repeat kept
    assert e._decks == {}                                    # stale deck dropped


def test_get_deck_state_persists_no_question_objects():
    e = QuizEngine()
    e._seen = {('math', 1): {'a', 'b'}}
    e._decks = {('math', 1): [{'question': 'q'}]}
    state = e.get_deck_state()
    # The seen-set persists (anti-repeat) and per-run mastery persists
    # (retired + mastered, added 2026-06-08), but the shuffled DECKS -- the
    # question OBJECTS -- must NEVER be pickled: that was the stale-question bug.
    assert state['seen'] == {('math', 1): {'a', 'b'}}
    assert 'decks' not in state and 'deck_idx' not in state
    assert 'retired' in state and 'mastered' in state
