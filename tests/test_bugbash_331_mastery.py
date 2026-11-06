"""Bug bash 3.3.1, subject mastery: only the bank as it is now counts.

A save keeps the run's right answers (by question text) and its mastered
tiers. After a bank update the save still listed tiers as mastered, and the
combat draw counted every remembered text, old ones included, against the
tier's size: tier 2 maths showed as cleared with 0 of its 560 questions
answered, cleared tiers auto-passed their quizzes, and the false clear
reached the "TIER N CLEARED" line and the Seeker (Tier Cleared, The
Examined Life).
"""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    import quiz_engine
    import save_system
    import bones
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    yield


def _old_save(n=560):
    """A save from before a bank update: the texts it answered are gone."""
    return {'seen': {},
            'retired': {('math', 2): {f'an old question {i}' for i in range(n)},
                        ('philosophy', 1): {f'an old stem {i}' for i in range(200)}},
            'mastered': {('math', 2), ('philosophy', 1)}}


def test_restored_mastery_counts_only_questions_in_the_bank():
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    qe.restore_deck_state(_old_save())
    assert qe.tier_progress('math', 2) == (0, 560)
    assert not qe.is_mastered('math', 2)
    assert not qe.is_mastered('philosophy', 1)


def test_a_true_clear_survives_the_restore():
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    stems = qe._tier_stems('philosophy', 1)
    qe.restore_deck_state({'seen': {}, 'retired': {('philosophy', 1): set(stems) | {'gone'}},
                           'mastered': {('philosophy', 1)}})
    assert qe.is_mastered('philosophy', 1)


def test_stale_mastery_does_not_auto_pass_a_quiz():
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    qe.restore_deck_state(_old_save())
    qe.start_quiz('threshold', 'philosophy', 1, lambda r: None, threshold=1)
    assert qe.auto_passed == 0 and qe.current_question is not None


def test_combat_draw_does_not_clear_a_tier_on_old_answers():
    from quiz_engine import QuizEngine
    qe = QuizEngine()
    state = _old_save()
    state['mastered'] = set()
    qe.restore_deck_state(state)
    qe.start_quiz('chain', 'math', 2, lambda r: None, max_chain=5)
    assert qe.just_mastered is None
    assert not qe.is_mastered('math', 2)


def test_stale_mastery_gives_no_philosophy_trait_or_seeker_event():
    import pygame
    pygame.init()
    from main import Game
    import items
    import philosophy_mastery as pm
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name='__bb331_mastery__')
    events = []
    g._seeker_event = lambda name, **kw: events.append(name)
    g.quiz_engine.restore_deck_state(_old_save())
    g._philosophy_mastery_check()
    assert not pm.mastered_tiers(g.player)
    assert 'philosophy_tier' not in events
