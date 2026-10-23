"""The teaching-moment bundle (2026-10-23): topic cards with no quiz running.

* every card has a title (bankbuild/cards/titles.py);
* C on a missed question opens its whole card, and goes back;
* the Encyclopedia's Lore Codex (m) lists every topic met;
* Study Mode By Topic: read the card, then its questions easiest first;
* the sidebar's Meals line; the help screen's How Quizzes Work page.

The screens themselves need a play-test; these prove the wiring.
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import topic_cards  # noqa: E402

pygame.init()
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _kd(k, uni=''):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode=uni, scancode=0)


@pytest.fixture
def save_dir(tmp_path, monkeypatch):
    import save_system
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    return tmp_path


def _game():
    from main import Game
    from game_states import STATE_PLAYER
    g = Game(_screen(), player_name='loretest')
    g.state = STATE_PLAYER
    return g


class _P:
    pass


def _a_topic(subject='history'):
    topic = sorted(topic_cards.cards(subject))[0]
    return topic, topic_cards.ladder(subject, topic)


# -- titles ------------------------------------------------------------------

@pytest.mark.parametrize('path', sorted((ROOT / 'data' / 'question_contexts').glob('*.json')),
                         ids=lambda p: p.stem)
def test_every_card_has_a_title_case_title(path):
    cards = json.loads(path.read_text(encoding='utf-8'))
    bad = [t for t, e in cards.items()
           if not (isinstance(e, dict) and str(e.get('title', '')).strip())]
    assert not bad, f"{path.stem}: {len(bad)} cards without a title: {bad[:5]} " \
                    "(add it to bankbuild/cards/topic_titles.json, run bankbuild.cards.titles)"
    # A first word all in lower case is a slip; "xAI" and "e/acc" are names.
    lower = [e['title'] for e in cards.values()
             if (w := e['title'].split()[0]).isalpha() and w == w.lower()]
    assert not lower, lower[:5]


def test_title_falls_back_to_a_readable_id():
    assert topic_cards.title('history', 'no-such-topic-here') == 'No Such Topic Here'


# -- the module ----------------------------------------------------------------

def test_topics_are_in_title_order_and_all_have_cards():
    pairs = topic_cards.topics('animal')
    assert pairs and [p[1].lower() for p in pairs] == sorted(p[1].lower() for p in pairs)
    assert all(topic_cards.card('animal', t) for t, _ in pairs)


def test_ladder_runs_easiest_first_and_finds_its_topic_by_stem():
    topic, qs = _a_topic()
    assert qs and [int(q['tier']) for q in qs] == sorted(int(q['tier']) for q in qs)
    assert topic_cards.topic_for('history', qs[0]['question']) == topic
    old_entry = {'subject': 'history', 'question': qs[0]['question']}    # pre-card save
    assert topic_cards.missed_topic(old_entry) == ('history', topic)
    assert topic_cards.lesson('history', qs[0])                          # history teaches


def test_met_and_read_feed_the_codex():
    topic, _qs = _a_topic()
    p = _P()
    topic_cards.note_met(p, 'history', topic)
    topic_cards.note_met(p, 'history', 'retired-topic-with-no-card')
    entries = topic_cards.codex_entries(p)
    assert [e['_topic'] for e in entries] == [topic]
    assert entries[0]['_read'] is False
    topic_cards.note_read(p, 'history', topic)
    assert topic_cards.codex_entries(p)[0]['_read'] is True


def test_an_old_player_save_gains_empty_records():
    from player import Player
    p = Player.__new__(Player)
    state = Player().__dict__.copy()
    state.pop('topics_met')
    state.pop('topics_read')
    p.__setstate__(state)
    assert p.topics_met == set() and p.topics_read == set()


# -- the game ------------------------------------------------------------------

def test_answering_a_question_marks_its_topic_met(save_dir):
    g = _game()
    topic, qs = _a_topic()
    g.quiz_engine.subject = 'history'
    g.quiz_engine.current_question = qs[0]
    g._on_quiz_answer(True)
    assert f'history|{topic}' in g.player.topics_met


def test_c_on_a_missed_question_opens_its_card_and_esc_goes_back(save_dir):
    from game_states import STATE_STUDY, STATE_TOPIC_CARD, STATE_REVIEW_MISSED
    g = _game()
    topic, qs = _a_topic()
    entry = {'subject': 'history', 'question': qs[0]['question'], 'correct': qs[0]['answer'],
             'chosen': 'x', 'context': ''}                  # recorded before cards: no topic
    g.missed_questions = [entry]
    g._open_study_journal()
    assert g.state == STATE_STUDY
    g.handle_event(_kd(pygame.K_c, 'c'))
    assert g.state == STATE_TOPIC_CARD and g._topic_card['topic'] == topic
    assert f'history|{topic}' in g.player.topics_read
    g.render()                                             # draws without error
    g.handle_event(_kd(pygame.K_ESCAPE))
    assert g.state == STATE_STUDY
    # and from the post-death review
    g.state = STATE_REVIEW_MISSED
    g._review_idx = 0
    g.handle_event(_kd(pygame.K_c, 'c'))
    assert g.state == STATE_TOPIC_CARD
    g.handle_event(_kd(pygame.K_c, 'c'))
    assert g.state == STATE_REVIEW_MISSED


def test_lore_codex_lists_met_topics_and_enter_marks_read(save_dir):
    from game_states import STATE_ENCYCLOPEDIA
    g = _game()
    topic, _qs = _a_topic()
    topic_cards.note_met(g.player, 'history', topic)
    g._open_encyclopedia()
    assert g.state == STATE_ENCYCLOPEDIA
    g.handle_event(_kd(pygame.K_m, 'm'))
    assert g.encyclopedia_category == 'lore_codex'
    assert [e['_topic'] for e in g.encyclopedia_entries] == [topic]
    lines = g._encyclopedia_article_lines('lore_codex', g.encyclopedia_entries[0])
    assert len(lines) > 3                                   # title, subject, the card
    g.render()
    g.handle_event(_kd(pygame.K_RETURN, '\r'))
    assert f'history|{topic}' in g.player.topics_read


def test_help_has_a_how_quizzes_work_page(save_dir):
    from game_states import STATE_HELP, STATE_PLAYER
    page = json.loads((ROOT / 'data' / 'ui' / 'how_quizzes_work.json').read_text(encoding='utf-8'))
    assert len(page['sections']) >= 5 and all(s['heading'] for s in page['sections'])
    g = _game()
    g.handle_event(_kd(pygame.K_SLASH, '?'))
    assert g.state == STATE_HELP and g._help_page == 0
    g.render()
    g.handle_event(_kd(pygame.K_TAB))
    assert g._help_page == 1
    g.render()
    g.handle_event(_kd(pygame.K_DOWN))
    g.handle_event(_kd(pygame.K_ESCAPE))
    assert g.state == STATE_PLAYER


def test_meals_line_counts_this_floors_cooked_max_hp():
    from hud_context import cooking_hp_line
    from player import Player
    p = Player()
    assert cooking_hp_line(p) == (f"Meals: +0/{p.PER_FLOOR_HP_CAP} Max HP", 'open')
    p.try_apply_cook_hp_gain(2)
    assert cooking_hp_line(p)[0].startswith("Meals: +2/")
    p.try_apply_cook_hp_gain(10)
    assert cooking_hp_line(p)[1] == 'full'
    p.reset_floor_cook_caps()
    p.cooking_hp_gained = p.cooking_softcap()
    assert cooking_hp_line(p)[1] == 'capped'


# -- Study Mode ------------------------------------------------------------------

def test_study_mode_by_topic_reads_the_card_then_runs_the_ladder():
    from study_mode import StudyMode
    s = StudyMode(_screen())
    s._selected = next(i for i, (k, _n, _c) in enumerate(s._SUBJECTS) if k == 'history')
    s._handle_key(pygame.K_RETURN)                 # subject
    assert s._phase == 'mode'
    s._handle_key(pygame.K_DOWN)
    s._handle_key(pygame.K_RETURN)                 # By Topic
    assert s._phase == 'topics' and s._topics
    s._handle_key(pygame.K_RETURN)                 # first topic: its card
    assert s._phase == 'card'
    topic = s._topic
    s._kit_content(pygame.Rect(0, 0, 900, 600), draw=True)
    s._handle_key(pygame.K_RETURN)                 # answer its questions
    assert s._phase == 'quiz'
    ladder = topic_cards.ladder('history', topic)
    assert [q['question'] for q in s._questions] == [q['question'] for q in ladder]
    s._handle_key(pygame.K_c)                      # the card mid-quiz, and back
    assert s._phase == 'card' and s._card_return == 'quiz'
    s._handle_key(pygame.K_ESCAPE)
    assert s._phase == 'quiz'
    for q in s._questions:
        wrong = next(c for c in q['choices'] if c != q['answer'])
        s._handle_key(pygame.K_1 + q['choices'].index(wrong))
        assert s._phase == 'result' and s._lesson_for_result()
        s._kit_content(pygame.Rect(0, 0, 1200, 600), draw=True)
        s._handle_key(pygame.K_RETURN)
    assert s._phase == 'done' and s._asked_count == len(ladder)
    s._handle_key(pygame.K_RETURN)
    assert s._phase == 'topics'


def test_study_mode_by_difficulty_still_works():
    from study_mode import StudyMode
    s = StudyMode(_screen())
    s._handle_key(pygame.K_RETURN)                 # Math
    s._handle_key(pygame.K_RETURN)                 # By Difficulty
    assert s._phase == 'tier'
    s._handle_key(pygame.K_RETURN)                 # Tier 1
    assert s._phase == 'quiz' and s._questions and not s._by_topic


def test_study_mode_letter_jumps_to_a_title():
    from study_mode import StudyMode
    s = StudyMode(_screen())
    s._subject = 'trivia'
    s._phase = 'topics'
    s._topics = topic_cards.topics('trivia')
    s._selected = 0
    s._handle_key(pygame.K_s)
    assert s._topics[s._selected][1].lower().removeprefix('the ').startswith('s')
