"""Teaching cards for refresh units, through the repo's own card tooling.

    py -m bankbuild.science_refresh.cards packet <batch> <unit> [<unit> ...]
        -> _cards/science/bNNN_in.json from the units' FINAL questions
    (the writer writes bNNN_cards.json and passes `py -m bankbuild.cards.gate science <batch>`;
     then `py -m bankbuild.cards.judge packet science <batch>`, the cold reader,
     `py -m bankbuild.cards.judge score science <batch>`)
    py -m bankbuild.science_refresh.cards save <batch>
        -> units/<id>/card.json for every card that passes the gate AND full coverage

Refresh batches are numbered from 901, clear of the 2026-10 rollout's batches.
`_cards/` is scratch (untracked); a saved card.json is the unit's durable copy.
"""
from __future__ import annotations

import sys

from bankbuild.cards.common import batch_path, read_json as cread, write_json as cwrite
from bankbuild.cards.extract import packet as card_packet
from bankbuild.science_refresh.common import SUBJECT, UNITS_DIR, mark, unit_questions, write_json


def make_packet(batch: int, uids: list[str]) -> None:
    topics = []
    for uid in uids:
        kind, qs = unit_questions(uid, ('final',))
        if kind != 'final' or not qs:
            raise SystemExit(f'{uid}: no final questions yet')
        topics.append(card_packet(SUBJECT, uid, qs, None))
    cwrite(batch_path(SUBJECT, batch, 'in'), {'subject': SUBJECT, 'batch': batch, 'topics': topics})
    print(f'science b{batch:03d}: packet with {len(topics)} units: ' + ', '.join(uids))


def save(batch: int) -> None:
    from bankbuild.cards.gate import check_card
    pkt = cread(batch_path(SUBJECT, batch, 'in'))
    cards = cread(batch_path(SUBJECT, batch, 'cards'))
    score = cread(batch_path(SUBJECT, batch, 'score'))
    for p in pkt['topics']:
        t = p['topic']
        errs = check_card(p, cards.get(t))
        covered = (score.get(t) or {}).get('pass')
        if errs or not covered:
            why = f'{len(errs)} gate failures' if errs else 'not fully covered'
            print(f'  {t}: NOT saved ({why})')
            continue
        write_json(UNITS_DIR / t / 'card.json',
                   {'topic': t, 'batch': batch, 'context_blurb': cards[t]['context_blurb'],
                    'teaches': cards[t]['teaches'],
                    'words': len(cards[t]['context_blurb'].split())})
        mark(t, 'covered', batch=batch)
        print(f'  {t}: saved')


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    cmd, batch = sys.argv[1], int(sys.argv[2])
    if cmd == 'packet':
        make_packet(batch, sys.argv[3:])
    elif cmd == 'save':
        save(batch)
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
