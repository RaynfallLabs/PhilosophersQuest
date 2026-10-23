"""Rote-subject context cards: a lesson and one worked example.

    py -m bankbuild.cards.rote extract <subject> [--size 30]
    py -m bankbuild.cards.rote gate <subject> <batch> [--quiet]
    py -m bankbuild.cards.rote merge <subject> <batch> [<batch> ...]

Ruling (Brandon, 2026-10-22): grammar and math are the two snappy-rote
subjects, so their cards do NOT teach every rung the way a wonder-subject
teaching card does. "Just teach the grammar lesson with an example, kids can
figure out from there" / for math, "method cards and an example". The kid
APPLIES the rule, so there is no `teaches` map and no cold-reader judge: the
card would defeat its own purpose if it handed over each answer.

What that changes versus the teaching gate (bankbuild/cards/gate.py):
  * short: 55-220 words, not 60+45 per question;
  * a worked example is required;
  * a keyed answer of 4 or more words may NOT appear verbatim, which is the
    reverse of the teaching rule. Short keys ("its", "affect", "12") are
    exempt: a card about affect versus effect has to use both words, and a
    method card has to do arithmetic.
A whole wrong CHOICE may appear: in grammar the misuse is the lesson
("Let's eat, Grandma!"), per the Comma-Saves-Lives voice rule.
"""
from __future__ import annotations

import json
import re
import sys

from bankbuild.cards.common import CDIR, batch_path, ladders, load_cards, norm, read_json, write_json
from bankbuild.cards.gate import AUTHOR_VOICE, JARGON, URL, _contains, _singular_they

MIN_WORDS, MAX_WORDS = 55, 220
EXAMPLE_RE = re.compile(r'\b(examples?|for instance)\b', re.I)
# A key short enough that the card cannot avoid it, so it is not a giveaway.
KEY_EXEMPT_WORDS = 4


def packet(subject: str, topic: str, qs: list[dict], old: dict | None) -> dict:
    return {
        'topic': topic,
        'old_card': (old or {}).get('context_blurb', '') if isinstance(old, dict) else str(old or ''),
        'length': {'min_words': MIN_WORDS, 'max_words': MAX_WORDS},
        'questions': [{
            'tier': int(q.get('tier', 1)),
            'stem': q['question'],
            'answer': q['answer'],
            'choices': q.get('choices', []),
        } for q in qs],
    }


def check_card(pkt: dict, card: dict) -> list[str]:
    errs: list[str] = []
    text = (card or {}).get('context_blurb', '') or ''
    if not text.strip():
        return ['empty card']
    if (card or {}).get('teaches'):
        errs.append('a rote card must not carry a `teaches` map (the kid applies the rule)')
    n = len(text.split())
    if n < MIN_WORDS:
        errs.append(f'too short: {n} words (min {MIN_WORDS})')
    if n > MAX_WORDS:
        errs.append(f'too long: {n} words (max {MAX_WORDS}) - teach the rule, not the history')
    if not EXAMPLE_RE.search(text):
        errs.append('no worked example (say "Example:" and show the rule applied)')
    low = text.lower()
    errs += [f'author note: "{p.strip()}"' for p in AUTHOR_VOICE if p in low]
    m = JARGON.search(text)
    if m:
        errs.append(f'quiz jargon: "{m.group(0)}"')
    # No GIVEAWAY check here: "then the answer is 35" is correct prose in a
    # worked example. The keyed-answer rule below is the real guard.
    if URL.search(text):
        errs.append('source line or URL')
    for kind, start, end in _singular_they(text):
        errs.append(f'singular they ({kind}): "...{text[max(0, start - 40):end + 10]}..." '
                    '(use he, she or it; if the referent really is plural, reword so the lint sees it)')
    hay = ' '.join(norm(text).split())
    for q in pkt['questions']:
        ans = str(q['answer'])
        if len(ans.split()) >= KEY_EXEMPT_WORDS and _contains(hay, ans):
            errs.append(f'gives away a keyed answer verbatim: "{ans[:60]}" '
                        '(use a different example, so the kid applies the rule)')
    return errs


def gate_batch(subject: str, batch: int) -> dict[str, list[str]]:
    pkt = read_json(batch_path(subject, batch, 'in'))
    cards = read_json(batch_path(subject, batch, 'cards'))
    return {p['topic']: check_card(p, cards.get(p['topic'])) for p in pkt['topics']}


def _extract(argv) -> None:
    subject = argv[0]
    size = int(argv[argv.index('--size') + 1]) if '--size' in argv else 30
    lad = ladders(subject)
    old = load_cards(subject)
    topics = sorted(lad)
    n = 1
    for i in range(0, len(topics), size):
        chunk = topics[i:i + size]
        write_json(batch_path(subject, n, 'in'),
                   {'subject': subject, 'batch': n, 'rote': True,
                    'topics': [packet(subject, t, lad[t], old.get(t)) for t in chunk]})
        n += 1
    print(f'{subject}: {len(topics)} topics in {n - 1} rote batches (b001..b{n - 1:03d})')


def _gate(argv) -> None:
    subject, batch = argv[0], int(argv[1])
    res = gate_batch(subject, batch)
    bad = {t: e for t, e in res.items() if e}
    if '--quiet' not in argv:
        for t, e in bad.items():
            print(f'FAIL {t}')
            for x in e:
                print(f'   - {x}')
    print(f'{subject} b{batch:03d}: {len(res) - len(bad)}/{len(res)} rote cards pass the gate')
    sys.exit(1 if bad else 0)


def _merge(argv) -> None:
    subject, batches = argv[0], [int(b) for b in argv[1:] if b.isdigit()]
    live = load_cards(subject)
    applied = held = 0
    for b in batches:
        res = gate_batch(subject, b)
        cards = read_json(batch_path(subject, b, 'cards'))
        for topic, errs in res.items():
            if errs or topic not in cards:
                held += 1
                continue
            live[topic] = {'context_blurb': cards[topic]['context_blurb']}
            applied += 1
    p = CDIR / f'{subject}.json'
    p.write_text(json.dumps(live, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    done = sum(1 for t in ladders(subject) if (live.get(t) or {}).get('context_blurb'))
    print(f'{subject}: applied {applied} rote cards, held {held}; {done} done in total')


def main() -> None:
    cmd, argv = sys.argv[1], sys.argv[2:]
    {'extract': _extract, 'gate': _gate, 'merge': _merge}[cmd](argv)


if __name__ == '__main__':
    main()
