"""Teaching cards in the quiz engine (ruling 2026-10-18): the card teaches
every rung, a wrong untimed answer holds on the lesson line until a key,
and card reads are counted for the pilot."""
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

import quiz_engine as qe_mod  # noqa: E402
from quiz_engine import QuizEngine, QuizState  # noqa: E402

STEM = "Which beast guards the gate?"
Q = {'question': STEM, 'answer': 'Cerberus', 'choices': ['Cerberus', 'Fenrir', 'Ladon', 'Orthrus'],
     'tier': 1, 'topic': 'gatekeeper', 'context': 'Cerberus guards Hades. Source: https://x'}


def _engine(tmp_path, teaches=True):
    card = {'context_blurb': 'A three-headed dog named Cerberus guards the gate of Hades.'}
    if teaches:
        card['teaches'] = {hashlib.sha1(STEM.encode()).hexdigest()[:10]:
                           'A three-headed dog named Cerberus guards the gate of Hades.'}
    (tmp_path / 'theology.json').write_text(json.dumps({'gatekeeper': card}), encoding='utf-8')
    qe_mod._CONTEXTS_DIR_OVERRIDE = str(tmp_path)
    try:
        e = QuizEngine()
        e._load_context_blurbs()
    finally:
        qe_mod._CONTEXTS_DIR_OVERRIDE = None
    e.subject = 'theology'
    e.tier = 1
    e.current_question = dict(Q)
    e.state = QuizState.ASKING
    e.timed = False
    return e


def test_lesson_is_the_cards_teaching_sentence(tmp_path):
    e = _engine(tmp_path)
    assert e.lesson_for() == 'A three-headed dog named Cerberus guards the gate of Hades.'


def test_lesson_falls_back_to_context_without_its_source(tmp_path):
    e = _engine(tmp_path, teaches=False)
    assert e.lesson_for() == 'Cerberus guards Hades.'


def test_untimed_wrong_answer_holds_until_a_key(tmp_path):
    e = _engine(tmp_path)
    e.answer('Fenrir')
    assert e.state == QuizState.RESULT and e._result_hold
    e.update(10.0)
    assert e.state == QuizState.RESULT, 'the lesson must wait for the player'
    assert not e.release_result_hold(), 'a key inside the first second is ignored'
    e._result_hold_until = time.monotonic() - 0.1
    assert e.release_result_hold()
    assert not e._result_hold


def test_timed_wrong_answer_keeps_the_flash(tmp_path):
    e = _engine(tmp_path)
    e.timed = True
    e.answer('Fenrir')
    assert not e._result_hold


def test_right_answer_never_holds(tmp_path):
    e = _engine(tmp_path)
    e.answer('Cerberus')
    assert not e._result_hold


def test_card_reads_are_counted_once_per_question(tmp_path):
    e = _engine(tmp_path)
    e.pause_timer()
    e.resume_timer()
    e.pause_timer()
    e.answer('Cerberus')
    row = e._answer_times['theology|1']
    assert row['cards_opened'] == 1
    assert row['right_after_card'] == 1
