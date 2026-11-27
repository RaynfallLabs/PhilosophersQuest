"""The grade-aligned science bank (the 2026-11-25 refresh) keeps its shape.

Brandon, 2026-11-16 and 11-25: tier is school grade (T1 5th ... T5 9th), and
science went first as 1,000 questions, exactly 200 a tier, built in one-tier
units from a grade-by-grade curriculum map (bankbuild/science_refresh/). These
checks stop the bank drifting back into "every tier feels the same":
  * 200 questions a tier;
  * every topic is a unit of units.json, and all its questions sit in that
    unit's one tier;
  * every unit names at least one line of its own grade in the curriculum map;
  * every topic has a teaching card and a title;
and an old save's science record (topics met and read, mastery) from the old
bank neither crashes nor shows a blank.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))
REFRESH = ROOT / 'bankbuild' / 'science_refresh'
QUESTIONS = json.loads((ROOT / 'data' / 'questions' / 'science.json').read_text(encoding='utf-8'))
CARDS = json.loads((ROOT / 'data' / 'question_contexts' / 'science.json').read_text(encoding='utf-8'))
UNITS = {u['id']: u for u in json.loads((REFRESH / 'units.json').read_text(encoding='utf-8'))['units']}
MAP = json.loads((REFRESH / 'curriculum_map.json').read_text(encoding='utf-8'))
LINES = {line['id']: (int(grade), line) for grade, g in MAP['grades'].items() for line in g['lines']}
TIER_GRADE = {1: 5, 2: 6, 3: 7, 4: 8, 5: 9}


def test_two_hundred_questions_a_tier():
    assert Counter(q['tier'] for q in QUESTIONS) == {t: 200 for t in range(1, 6)}


def test_every_topic_is_one_unit_in_one_tier():
    tiers = defaultdict(set)
    for q in QUESTIONS:
        tiers[q['topic']].add(q['tier'])
    unknown = sorted(t for t in tiers if t not in UNITS)
    assert not unknown, f'topics that are not units of units.json: {unknown[:5]}'
    split = {t: sorted(s) for t, s in tiers.items() if len(s) > 1}
    assert not split, f'units spread over more than one tier: {split}'
    wrong = {t: (sorted(s), UNITS[t]['tier']) for t, s in tiers.items() if s != {UNITS[t]['tier']}}
    assert not wrong, f'units whose questions are not in the unit\'s tier: {wrong}'


def test_every_unit_names_a_line_of_its_own_grade():
    bad = {}
    for uid, u in UNITS.items():
        grades = {LINES[line][0] for line in u.get('map_lines', []) if line in LINES}
        if TIER_GRADE[u['tier']] not in grades:
            bad[uid] = (u['tier'], u.get('map_lines'))
    assert not bad, f'units with no curriculum line of their grade: {bad}'


def test_every_topic_has_a_card_and_a_title():
    topics = {q['topic'] for q in QUESTIONS}
    missing = sorted(t for t in topics if not str((CARDS.get(t) or {}).get('context_blurb', '')).strip())
    assert not missing, missing[:5]
    assert set(CARDS) == topics, sorted(set(CARDS) ^ topics)[:5]
    assert all(CARDS[t]['title'] == UNITS[t]['title'] for t in topics)


def test_an_old_save_with_old_science_topics_shows_no_blank():
    import topic_cards
    old = 'science|the-great-barrington-takedown'   # an old-bank ladder, retired
    assert not topic_cards.card('science', old.partition('|')[2])
    new = sorted(UNITS)[0]

    class Hero:
        topics_met = {old, f'science|{new}'}
        topics_read = {old}

    entries = topic_cards.codex_entries(Hero())
    assert [e['_topic'] for e in entries] == [new]
    assert entries[0]['name'] == UNITS[new]['title']


def test_an_old_save_keeps_no_science_mastery_it_did_not_earn():
    from quiz_engine import QuizEngine
    engine = QuizEngine()
    engine.restore_deck_state({'seen': {}, 'retired': {('science', 1): {'An old-bank question?'}},
                               'mastered': [('science', 1)]})
    assert not engine.is_mastered('science', 1)
    assert engine.tier_progress('science', 1) == (0, 200)
