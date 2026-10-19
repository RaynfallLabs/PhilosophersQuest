"""Apply passing teaching cards to the shipped data.

    py -m bankbuild.cards.merge <subject> <batch> [<batch> ...]

A card is applied only when it passes the deterministic gate AND its coverage
score (bNNN_score.json) shows every question covered. The judge's verified
quotes are not used as `teaches`; the author's `teaches` map is, after the
gate has proved each sentence sits word for word in the card.

Writes data/question_contexts/<subject>.json (other topics untouched) and
appends the applied topics to _cards/<subject>/status.json "done".
"""
from __future__ import annotations

import json
import sys

from bankbuild.cards.common import CDIR, WORK, batch_path, read_json, write_json
from bankbuild.cards.gate import gate_batch


def main() -> None:
    subject = sys.argv[1]
    batches = [int(b) for b in sys.argv[2:]]
    path = CDIR / f'{subject}.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    status_p = WORK / subject / 'status.json'
    status = read_json(status_p) if status_p.exists() else {'done': [], 'held': {}}
    applied, held = 0, 0
    for b in batches:
        gate = gate_batch(subject, b)
        sp = batch_path(subject, b, 'score')
        score = read_json(sp) if sp.exists() else {}
        cards = read_json(batch_path(subject, b, 'cards'))
        for topic, errs in gate.items():
            sc = score.get(topic)
            if errs or not sc or not sc.get('pass'):
                status['held'][topic] = {'batch': b, 'gate': errs,
                                         'coverage': (sc or {}).get('fails', 'not judged')}
                held += 1
                continue
            entry = data.get(topic) if isinstance(data.get(topic), dict) else {}
            entry = dict(entry)
            entry['context_blurb'] = cards[topic]['context_blurb'].strip()
            entry['teaches'] = cards[topic]['teaches']
            data[topic] = entry
            if topic not in status['done']:
                status['done'].append(topic)
            status['held'].pop(topic, None)
            applied += 1
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_json(status_p, status)
    print(f'{subject}: applied {applied} cards, held {held}; '
          f'{len(status["done"])} done in total')


if __name__ == '__main__':
    main()
