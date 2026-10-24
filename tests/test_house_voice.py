"""The house voice, the Chronicler (docs/quiz/HOUSE_VOICE.md, Brandon 2026-10-24).

* the lint's rules, on stems written to break them;
* the ratchet: the number of stems in each bank that break the lint may only
  go down (tests/data/voice_lint_baseline.json; bankbuild/voice/apply.py
  lowers it as the voice pass applies each batch).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bankbuild.voice.lint import bank_report, lint_stem  # noqa: E402

GOOD = ("Che Guevara had about 300 rebels outside Santa Clara late in 1958, in the last months "
        "of Cuba's revolution. The dictator Fulgencio Batista sent an armored train with 3,500 "
        "fresh soldiers and heavy guns to crush them. Che had a captured bulldozer and some "
        "dynamite. What did his band do to the train?")


def _fails(stem, subject='history', tier=2):
    return [r.split('(')[0] for r in lint_stem(stem, subject, tier)[0]]


def test_a_stem_in_the_voice_passes():
    assert lint_stem(GOOD, 'history', 2) == ([], [])


def test_the_date_may_not_lead():
    assert 'date_first' in _fails('In late 1958, Che Guevara had 300 rebels. What did he do?')
    assert 'date_first' in _fails('In 1987 Thomas Sowell wrote a book. What did it say?')
    assert 'date_first' in _fails('During the 1960s a cook in Lyon made a sauce. What was it?')
    assert 'date_first' not in _fails('In the fifth book of the Iliad, a hero spears Ares. Who guides his arm?')


def test_you_only_in_a_thought_experiment():
    assert 'second_person' in _fails('If you salt the water first, the pasta tastes better. Why?')
    assert 'second_person' not in _fails('Suppose you find a wallet with $500 in it. What should you do?')
    # A quoted line keeps its own words.
    assert 'second_person' not in _fails("A critic snaps, 'You can't trust her,' at the scientist. "
                                         "What has he done wrong?", 'philosophy')


def test_tics_and_punctuation():
    assert 'exclamation' in _fails('The ship sank in minutes! What sank it?')
    assert 'dashes' in _fails('The ship — a liner — sank in minutes. What sank it?')
    assert 'which_of_the_following' in _fails('Which of the following sank the ship?')
    assert 'caps_emphasis' in _fails('The ship did NOT sink at once. What kept it up?')
    assert 'caps_emphasis' not in _fails('NASA sent DNA samples on the shuttle. What did they show?')
    assert 'no_question_mark' in _fails('Name the ship that sank.')
    assert 'bad_opening' in _fails('Imagine a ship sinking in minutes. What sank it?')


def test_length_bands_and_exemptions():
    long = ' '.join(['word'] * 90) + ' and what?'
    assert 'too_long' in _fails(long, 'history', 3)
    assert lint_stem(long, 'math', 3) == ([], [])
    assert 'too_long' not in _fails(long, 'grammar', 3)


def test_no_bank_breaks_the_voice_more_than_it_did():
    base = json.loads((ROOT / 'tests' / 'data' / 'voice_lint_baseline.json').read_text(encoding='utf-8'))
    grown = {}
    for subject, allowed in base.items():
        r = bank_report(subject)
        failing = r['n'] - r['clean']
        if failing > allowed:
            grown[subject] = (allowed, failing)
    assert not grown, ('stems that break the house-voice lint grew (allowed, now): '
                       f'{grown}. See docs/quiz/HOUSE_VOICE.md; bankbuild.voice.lint shows them.')
