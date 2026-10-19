"""Coverage judge packets and scoring.

    py -m bankbuild.cards.judge packet <subject> <batch> [--only topic,topic]
        -> writes bNNN_judge_in.json: each card plus each question's stem and
           shuffled choices. No keyed answers, no contexts.
    py -m bankbuild.cards.judge score <subject> <batch>
        -> reads bNNN_judge.json ({topic: {hash: {"pick": str, "quote": str}}}),
           checks every pick against the key and every quote word for word
           against the card, writes bNNN_score.json, prints a summary.

A question PASSES when the pick is the keyed answer AND the quote appears in
the card. A ladder passes when every question passes.
"""
from __future__ import annotations

import sys

from bankbuild.cards.common import batch_path, norm, read_json, shuffled_choices, words, write_json


def make_packet(subject: str, batch: int, only: set[str] | None = None) -> int:
    pkt = read_json(batch_path(subject, batch, 'in'))
    cards = read_json(batch_path(subject, batch, 'cards'))
    out = []
    for p in pkt['topics']:
        t = p['topic']
        if only and t not in only:
            continue
        if t not in cards:
            continue
        out.append({
            'topic': t,
            'card': cards[t]['context_blurb'],
            'questions': [{'hash': q['hash'], 'stem': q['stem'],
                           'choices': shuffled_choices({'question': q['stem'], 'choices': q['choices']})}
                          for q in p['questions']],
        })
    write_json(batch_path(subject, batch, 'judge_in'), {'subject': subject, 'batch': batch, 'topics': out})
    return len(out)


def score(subject: str, batch: int) -> dict:
    pkt = read_json(batch_path(subject, batch, 'in'))
    cards = read_json(batch_path(subject, batch, 'cards'))
    judged = read_json(batch_path(subject, batch, 'judge'))
    res = {}
    for p in pkt['topics']:
        t = p['topic']
        if t not in judged:
            continue
        hay = ' '.join(words(cards.get(t, {}).get('context_blurb', '')))
        fails = []
        for q in p['questions']:
            j = (judged[t] or {}).get(q['hash']) or {}
            pick, quote = str(j.get('pick', '')), str(j.get('quote', ''))
            right = norm(pick) == norm(q['answer'])
            supported = bool(norm(quote)) and norm(quote) in hay
            if not (right and supported):
                fails.append({'hash': q['hash'], 'tier': q['tier'],
                              'why': ('wrong pick' if not right else '') +
                                     (' unsupported quote' if not supported else ''),
                              'judge_pick': pick})
        res[t] = {'pass': not fails, 'fails': fails}
    write_json(batch_path(subject, batch, 'score'), res)
    return res


def main() -> None:
    cmd, subject, batch = sys.argv[1], sys.argv[2], int(sys.argv[3])
    if cmd == 'packet':
        only = None
        if '--only' in sys.argv:
            only = set(sys.argv[sys.argv.index('--only') + 1].split(','))
        n = make_packet(subject, batch, only)
        print(f'{subject} b{batch:03d}: judge packet with {n} cards')
    elif cmd == 'score':
        res = score(subject, batch)
        ok = sum(1 for r in res.values() if r['pass'])
        nq = sum(len(r['fails']) for r in res.values())
        print(f'{subject} b{batch:03d}: {ok}/{len(res)} ladders fully covered; {nq} questions not covered')
        for t, r in res.items():
            if not r['pass']:
                print(f'   {t}: ' + '; '.join(f"T{f['tier']} {f['hash']} ({f['why'].strip()})" for f in r['fails']))


if __name__ == '__main__':
    main()
