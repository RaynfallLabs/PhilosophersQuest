"""The achievement engine (src/achievements.py) on a small inline rule set:
counters of every kind, triggers of every kind, ladders, and the validator.
"""
import copy

import pytest

import achievements as ach
import seeker_codes as sc
import seeker_profile as sp

DATA = {
    'categories': [{'id': 'scholar', 'name': 'Scholar'}, {'id': 'secrets', 'name': 'Secrets'}],
    'counters': {
        'answered': {'on': 'quiz_answer'},
        'right_math': {'on': 'quiz_answer', 'where': {'subject': 'math', 'correct': True}},
        'damage': {'on': 'damage', 'add': 'amount', 'where': {'by': 'hero'}},
        'blow': {'on': 'damage', 'best': 'amount', 'where': {'by': 'hero'}},
        'streak': {'on': 'quiz_answer', 'streak': {'correct': True}},
        'builds': {'on': 'run_start', 'collect': 'build'},
        'kills_run': {'on': 'kill', 'scope': 'run'},
    },
    'achievements': [
        {'id': 'q1', 'name': 'One', 'category': 'scholar', 'rarity': 'common', 'hint': 'h',
         'unlocked_text': 'u', 'code_word': 'ONE', 'art': 'q1', 'ladder': 'q', 'tier': 1,
         'trigger': {'stat': 'answered', 'at_least': 2}},
        {'id': 'q2', 'name': 'Two', 'category': 'scholar', 'rarity': 'rare', 'hint': 'h',
         'unlocked_text': 'u', 'code_word': 'TWO', 'art': 'q2', 'ladder': 'q', 'tier': 2,
         'trigger': {'stat': 'answered', 'at_least': 4}},
        {'id': 'blow', 'name': 'Blow', 'category': 'scholar', 'rarity': 'rare', 'hint': 'h',
         'unlocked_text': 'u', 'code_word': 'BLOW', 'art': 'b',
         'trigger': {'stat': 'blow', 'at_least': 100}},
        {'id': 'streak3', 'name': 'Streak', 'category': 'scholar', 'rarity': 'rare', 'hint': 'h',
         'unlocked_text': 'u', 'code_word': 'ROLL', 'art': 's',
         'trigger': {'stat': 'streak', 'at_least': 3}},
        {'id': 'duck', 'name': 'Duck', 'category': 'secrets', 'rarity': 'epic', 'hint': 'Munchkin.',
         'spoiler_words': ['hatch'], 'unlocked_text': 'u', 'code_word': 'QUACK', 'art': 'd',
         'trigger': {'event': 'duck_hatched'}},
        {'id': 'xyzzy3', 'name': 'Deep', 'category': 'secrets', 'rarity': 'epic', 'hint': 'h',
         'unlocked_text': 'u', 'code_word': 'DEEP', 'art': 'x',
         'trigger': {'event': 'xyzzy', 'where': {'chain': {'at_least': 3}}}},
        {'id': 'phil_win', 'name': 'Thinker', 'category': 'secrets', 'rarity': 'legendary',
         'hint': 'h', 'unlocked_text': 'u', 'code_word': 'THINK', 'art': 'p',
         'trigger': {'event': 'run_end', 'where': {'victory': True,
                                                   'build': ['socrates of athens', 'plato of athens']}}},
        {'id': 'two_builds', 'name': 'Names', 'category': 'secrets', 'rarity': 'rare', 'hint': 'h',
         'unlocked_text': 'u', 'code_word': 'NAMES', 'art': 'n',
         'trigger': {'stat': 'builds', 'at_least': 2}},
        {'id': 'run5', 'name': 'Busy', 'category': 'scholar', 'rarity': 'rare', 'hint': 'h',
         'unlocked_text': 'u', 'code_word': 'BUSY', 'art': 'r',
         'trigger': {'run': 'kills_run', 'at_least': 5}},
        {'id': 'combo', 'name': 'Combo', 'category': 'scholar', 'rarity': 'epic', 'hint': 'h',
         'unlocked_text': 'u', 'code_word': 'COMBO', 'art': 'c',
         'trigger': {'all': [{'stat': 'right_math', 'at_least': 1}, {'stat': 'damage', 'at_least': 50}]}},
    ],
}


@pytest.fixture
def prof(tmp_path):
    saved_keys, saved_dir = sc._KEYS_OVERRIDE, sp._DIR_OVERRIDE
    sc._KEYS_OVERRIDE = {'label': 'pq1', 'keys': {'pq1': bytes(range(32))}}
    sp._DIR_OVERRIDE = str(tmp_path)
    yield sp.load('Robyn')
    sc._KEYS_OVERRIDE, sp._DIR_OVERRIDE = saved_keys, saved_dir


def _apply(book, prof, run, event, **f):
    got = book.apply(prof, run, event, **f)
    for aid in got:
        prof.unlock(aid)
    return got


def test_inline_data_is_valid():
    assert ach.validate(DATA) == []


def test_ladder_unlocks_each_tier_once(prof):
    book = ach.Book(DATA)
    assert _apply(book, prof, None, 'quiz_answer', subject='history', correct=False) == []
    assert _apply(book, prof, None, 'quiz_answer', subject='history', correct=False) == ['q1']
    assert _apply(book, prof, None, 'quiz_answer', subject='history', correct=False) == []
    assert _apply(book, prof, None, 'quiz_answer', subject='history', correct=False) == ['q2']
    assert _apply(book, prof, None, 'quiz_answer', subject='history', correct=False) == []
    assert book.progress('q2', prof) == (4, 4)


def test_jump_past_two_tiers_unlocks_both(prof):
    book = ach.Book(DATA)
    prof.add('answered', 10)                  # an old profile meets a new ladder
    assert sorted(book.settled(prof)) == ['q1', 'q2']


def test_best_and_add_counters(prof):
    book = ach.Book(DATA)
    _apply(book, prof, None, 'damage', amount=60, by='pet')
    assert prof.stat('damage') == 0           # pets do not count for the hero
    _apply(book, prof, None, 'damage', amount=60, by='hero')
    got = _apply(book, prof, None, 'damage', amount=120, by='hero')
    assert prof.stat('damage') == 180 and prof.best('blow') == 120
    assert 'blow' in got


def test_streak_resets_on_a_wrong_answer(prof):
    book = ach.Book(DATA)
    for c in (True, True, False, True, True):
        assert 'streak3' not in _apply(book, prof, None, 'quiz_answer', subject='x', correct=c)
    assert 'streak3' in _apply(book, prof, None, 'quiz_answer', subject='x', correct=True)
    assert prof.best('streak') == 3


def test_event_triggers_and_where_tests(prof):
    book = ach.Book(DATA)
    assert _apply(book, prof, None, 'duck_hatched') == ['duck']
    assert _apply(book, prof, None, 'xyzzy', chain=2) == []
    assert _apply(book, prof, None, 'xyzzy', chain=4) == ['xyzzy3']
    assert _apply(book, prof, None, 'run_end', victory=True, build='aristotle of stagira') == []
    assert _apply(book, prof, None, 'run_end', victory=False, build='plato of athens') == []
    assert _apply(book, prof, None, 'run_end', victory=True, build='plato of athens') == ['phil_win']


def test_collect_and_run_scope(prof):
    book = ach.Book(DATA)
    assert _apply(book, prof, None, 'run_start', build='fianna') == []
    assert _apply(book, prof, None, 'run_start', build='fianna') == []
    assert _apply(book, prof, None, 'run_start', build='corwin') == ['two_builds']
    run = ach.RunTally()
    for _ in range(4):
        assert _apply(book, prof, run, 'kill', monster='rat') == []
    assert _apply(book, prof, run, 'kill', monster='rat') == ['run5']
    assert prof.stat('kills_run') == 0        # never in the lifetime profile
    assert ach.RunTally(run.data).stat('kills_run') == 5   # plain dict survives a save


def test_all_combinator(prof):
    book = ach.Book(DATA)
    _apply(book, prof, None, 'damage', amount=50, by='hero')
    assert _apply(book, prof, None, 'quiz_answer', subject='math', correct=True) == ['combo']


def _bad(mutate):
    d = copy.deepcopy(DATA)
    mutate(d)
    return ach.validate(d)


def test_validator_refuses_mistakes():
    assert _bad(lambda d: d['achievements'][0].update(trigger={'stat': 'nope', 'at_least': 1}))
    assert _bad(lambda d: d['achievements'][0].update(trigger={'event': 'not_an_event'}))
    assert _bad(lambda d: d['achievements'][5]['trigger']['where'].update(colour='red'))
    assert _bad(lambda d: d['achievements'][1].update(code_word='ONE'))          # duplicate word
    assert _bad(lambda d: d['achievements'][1].update(code_word='DEVIL'))        # DEV prefix
    assert _bad(lambda d: d['achievements'][1].update(name='one'))               # duplicate name
    assert _bad(lambda d: d['achievements'][1]['trigger'].update(at_least=1))    # ladder must rise
    assert _bad(lambda d: d['achievements'][4].update(hint='Watch it hatch.'))   # spoiler
    assert _bad(lambda d: d['achievements'][8].update(trigger={'stat': 'kills_run', 'at_least': 5}))
    assert _bad(lambda d: d['counters'].update(bad={'on': 'damage', 'add': 'colour'}))
    assert _bad(lambda d: d['achievements'][0].update(rarity='mythic'))
    assert _bad(lambda d: d['achievements'][0].update(surprise=True))
