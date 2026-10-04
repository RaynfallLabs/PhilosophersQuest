"""Math context cards by skill class (2026-10-04).

Math questions are rote items, not topic ladders, so instead of a ladder
blurb each question carries a skill-class ``topic`` and the class has one
short method card in ``data/question_contexts/math.json``.
"""
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / 'src'))
sys.path.insert(0, str(_ROOT))

from tools.balance.math_topics import (  # noqa: E402
    ALL_TOPICS, topic_for_context)

_BANK = json.loads((_ROOT / 'data' / 'questions' / 'math.json')
                   .read_text(encoding='utf-8'))
_CARDS = json.loads((_ROOT / 'data' / 'question_contexts' / 'math.json')
                    .read_text(encoding='utf-8'))


def test_every_math_question_has_a_topic_matching_its_tip():
    assert _BANK
    for q in _BANK:
        assert q.get('topic'), q['question']
        assert q['topic'] == topic_for_context(q['context']), q['question']


def test_every_topic_has_a_card_and_no_orphans():
    used = {q['topic'] for q in _BANK}
    assert used == set(ALL_TOPICS)
    assert set(_CARDS) == used
    for topic, entry in _CARDS.items():
        blurb = entry['context_blurb']
        words = len(blurb.split())
        assert 50 <= words <= 170, (topic, words)


def test_cards_do_not_spell_out_a_question_from_their_own_class():
    """A method card teaches the technique with numbers of its own; it
    must not contain the exact sum of any question in the class it
    covers."""
    leaks = []
    for q in _BANK:
        core = q['question'].replace(' = ?', '').rstrip('?').strip()
        if len(core) < 3 or not any(c.isdigit() for c in core):
            continue
        pat = r'(?<![\d.,^/])' + re.escape(core) + r'(?![\d.,^/])'
        if re.search(pat, _CARDS[q['topic']]['context_blurb']):
            leaks.append((q['topic'], core))
    assert not leaks, leaks[:10]


def test_unknown_tip_is_a_hard_error():
    import pytest
    with pytest.raises(ValueError):
        topic_for_context('A brand new kind of question.')


def test_engine_serves_math_cards():
    from quiz_engine import QuizEngine, _CONTEXT_SUBJECTS
    assert 'math' in _CONTEXT_SUBJECTS
    eng = QuizEngine()
    for topic in ALL_TOPICS:
        assert eng.get_context_blurb('math', topic), topic
    eng.subject = 'math'
    eng.current_question = _BANK[0]
    assert eng.current_context_blurb() == \
        _CARDS[_BANK[0]['topic']]['context_blurb'].strip()
