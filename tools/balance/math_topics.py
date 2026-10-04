"""Math skill classes ("topics") for the context-card system.

Math questions are short rote items, not topic ladders, so they never had
a ``topic`` field -- and the in-quiz context modal keys on
``(subject, topic)``. This module groups every math question into a skill
class from its one-line ``context`` strategy tip, so each class can carry
one method card in ``data/question_contexts/math.json``.

Used by:
  * ``build_math_bank_v3.py`` -- stamps ``topic`` when the bank is rebuilt;
  * ``python -m tools.balance.math_topics`` -- one-off migration that
    stamps ``topic`` onto the existing ``data/questions/math.json`` in
    place (no stem / answer / choice / tier changes).

Rules are ordered; the first regex that matches the tip wins. An
unmatched tip is a hard error so a new generator can't silently ship
questions without a class.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
MATH_BANK = _ROOT / 'data' / 'questions' / 'math.json'
MATH_CONTEXTS = _ROOT / 'data' / 'question_contexts' / 'math.json'

# (regex on the context tip, topic). Order matters -- specific first.
TOPIC_RULES: tuple[tuple[str, str], ...] = (
    (r'^Exponent rule',                              'Exponent Rules'),
    (r'^Try each divisibility rule',                 'Divisibility Rules'),
    (r'^Memorize the classic triples',               'Pythagorean Triples'),
    (r'^Sum formula',                                'Sum of 1 to N'),
    (r'^% change|^Percent = \(part / whole\)',       'Finding the Percent'),
    (r'^\d+% shortcut|^3-digit %',                   'Percent of a Number'),
    (r'root',                                        'Square and Cube Roots'),
    (r'^Squares|^Teen squares|^Cubes|^Powers of|^Larger powers of'
     r'|^Exponent recall|^Substitute the memorized', 'Squares, Cubes and Powers'),
    (r'^Skip-count',                                 'Skip Counting'),
    (r'^Missing addend|^Missing subtrahend',         'Missing Numbers'),
    (r'^Subtraction fact',                           'Subtraction Facts'),
    (r'^Addition fact|^Adding 10|^Anything plus 0|^Doubles|^Zero identity',
                                                     'Addition Facts'),
    (r'^Add multiples of 10|^Subtract multiples of 10',
                                                     'Adding and Subtracting Tens'),
    (r'^Division = inverse',                         'Division Facts'),
    (r'^Times-table fact',                           'Times Tables'),
    (r'^Doubling|^Halving',                          'Doubling and Halving'),
    (r'^Round:',                                     'Rounding'),
    (r'^Add tens, add ones|^Subtract with borrow',   'Two-Digit Addition and Subtraction'),
    (r'^Multiply by parts|^Distribute: ',            'Multiplying by Parts'),
    (r'^Order of ops|^Both mults first|^Multiply first, then left-to-right',
                                                     'Order of Operations'),
    (r'^Negative arithmetic|^Sign rule',             'Negative Numbers'),
    (r'^Simplify: ',                                 'Simplifying Fractions'),
    (r'^Common F|^Decimal fluency|^Move decimal|^Extended F',
                                                     'Fractions, Decimals and Percents'),
    (r'^Fraction of qty|^Fraction × integer|^Multiply the fractions first',
                                                     'Fraction of a Quantity'),
    (r'^Fraction op',                                'Fraction Arithmetic'),
    (r'^One-step',                                   'One-Step Equations'),
    (r'^Two-step algebra|^Divide both sides by k|^Distribute first',
                                                     'Two-Step Equations'),
)

_COMPILED = tuple((re.compile(pat), topic) for pat, topic in TOPIC_RULES)
ALL_TOPICS = tuple(dict.fromkeys(topic for _pat, topic in TOPIC_RULES))


def topic_for_context(context: str) -> str:
    """Skill class for a question's strategy tip. Raises on no match."""
    for pat, topic in _COMPILED:
        if pat.search(context or ''):
            return topic
    raise ValueError(f'no math topic rule matches context tip {context!r}')


def stamp_topics(questions: list[dict]) -> dict[str, int]:
    """Set ``topic`` on every question in place; return counts per topic."""
    counts: dict[str, int] = {}
    for q in questions:
        topic = topic_for_context(q.get('context', ''))
        q['topic'] = topic
        counts[topic] = counts.get(topic, 0) + 1
    return counts


def main(argv: list[str]) -> int:
    dry = '--dry-run' in argv
    samples = '--samples' in argv
    questions = json.loads(MATH_BANK.read_text(encoding='utf-8'))
    counts = stamp_topics(questions)
    for topic in ALL_TOPICS:
        print(f'{counts.get(topic, 0):5}  {topic}')
        if samples:
            seen = set()
            for q in questions:
                if q['topic'] == topic and q['context'] not in seen:
                    seen.add(q['context'])
                    print(f"         T{q['tier']}  {q['question']}  ->  {q['answer']}"
                          f"   [{q['context'][:48]}]")
                    if len(seen) >= 6:
                        break
    print(f'{len(questions)} questions, {len(counts)} topics')
    if MATH_CONTEXTS.exists():
        blurbs = json.loads(MATH_CONTEXTS.read_text(encoding='utf-8'))
        missing = [t for t in counts if t not in blurbs]
        orphan = [t for t in blurbs if t not in counts]
        if missing or orphan:
            print(f'BLURB MISMATCH  missing={missing}  orphan={orphan}')
            return 1
    if not dry:
        MATH_BANK.write_text(
            json.dumps(questions, indent=2, ensure_ascii=False),
            encoding='utf-8')
        print(f'stamped {MATH_BANK}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
