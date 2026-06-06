"""Cross-game quiz anti-repeat memory (2026-06-06).

The deck shuffles fairly -- proven empirically (50 fresh processes reseed
distinctly; first-question distribution matches uniform-random theory). But true
randomness has NO memory: a fresh game re-rolls from scratch and can re-show a
recent opener by pure chance, which reads as "not random". QuizEngine now
persists the last N question texts shown per (subject, tier) and seeds a new
game's `_seen` so its deck pushes those to the back. These tests lock in that a
brand-new engine (= a new game launch) avoids what a prior game just showed.

`conftest._isolate_quiz_history` already redirects the history file to a temp
dir; each test further pins it to its own tmp_path for determinism.
"""
import json
import os

import quiz_engine
from quiz_engine import QuizEngine


def _pin_history_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))


def test_new_game_avoids_recently_shown_questions(monkeypatch, tmp_path):
    _pin_history_dir(monkeypatch, tmp_path)

    # --- Game 1: show a run of math T1 questions, then end (persists). --------
    e1 = QuizEngine()
    e1.start_quiz('chain', 'math', 1, callback=lambda r: None, max_chain=5)
    shown1 = [e1.current_question['question']]
    for _ in range(9):
        e1._next_question()                    # walk the deck deterministically
        shown1.append(e1.current_question['question'])
    e1._persist_cross_game_history()
    assert os.path.exists(quiz_engine._quiz_history_path()), 'history not written'

    # --- Game 2: a BRAND-NEW engine (new game launch) loads that history. -----
    e2 = QuizEngine()
    e2.start_quiz('chain', 'math', 1, callback=lambda r: None, max_chain=5)
    g2 = [e2.current_question['question']]
    for _ in range(4):
        e2._next_question()
        g2.append(e2.current_question['question'])

    # The new game's opening questions must be drawn from the UNSEEN pool, so
    # they cannot overlap what game 1 just showed. (Deterministic, not chance:
    # _shuffle_unseen_first puts all unseen questions ahead of the seen ones.)
    assert set(g2).isdisjoint(shown1), \
        'new game re-showed questions the previous game already asked'


def test_history_file_seeds_seen_set(monkeypatch, tmp_path):
    _pin_history_dir(monkeypatch, tmp_path)

    # A real history T1 question, hand-written into the history file.
    probe = QuizEngine()
    t1 = [q for q in probe.load_questions('history') if q.get('tier', 1) == 1]
    assert t1, 'no history T1 questions to probe'
    target = t1[0]['question']
    with open(quiz_engine._quiz_history_path(), 'w', encoding='utf-8') as f:
        json.dump({'history|1': [target]}, f)

    # A fresh engine loads it and treats `target` as already seen.
    e = QuizEngine()
    assert e._recent.get(('history', 1)) == [target]
    assert target in e._seen.get(('history', 1), set())


def test_corrupt_history_file_is_non_fatal(monkeypatch, tmp_path):
    _pin_history_dir(monkeypatch, tmp_path)
    with open(quiz_engine._quiz_history_path(), 'w', encoding='utf-8') as f:
        f.write('}{ not json at all')
    # Construction must not raise, and a quiz must still start cleanly.
    e = QuizEngine()
    e.start_quiz('chain', 'math', 1, callback=lambda r: None, max_chain=5)
    assert e.current_question is not None
