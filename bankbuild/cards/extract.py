"""Cut a subject's ladders into author batches.

    py -m bankbuild.cards.extract <subject> --size 30 [--topics a,b,c] [--start N]

Writes _cards/<subject>/bNNN_in.json for every batch and a plan.json listing
which topics sit in which batch. Topics already marked done in
_cards/<subject>/status.json are skipped, so re-running is safe.
"""
from __future__ import annotations

import argparse

from bankbuild.cards.common import (WORK, batch_path, ladders, load_cards, read_json,
                                    stem_hash, strip_source, target_words, write_json)


def packet(subject: str, topic: str, qs: list[dict], old: dict) -> dict:
    lo, target, cap = target_words(len(qs))
    return {
        'topic': topic,
        'old_card': (old or {}).get('context_blurb', '') if isinstance(old, dict) else str(old or ''),
        'length': {'min_words': lo, 'target_words': target, 'max_words': cap},
        'questions': [{
            'hash': stem_hash(q['question']),
            'tier': int(q.get('tier', 1)),
            'stem': q['question'],
            'answer': q['answer'],
            'choices': q.get('choices', []),
            'context': strip_source(q.get('context', '')),
        } for q in qs],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('subject')
    ap.add_argument('--size', type=int, default=30)
    ap.add_argument('--topics', default='')
    ap.add_argument('--start', type=int, default=1, help='first batch number')
    a = ap.parse_args()
    lad = ladders(a.subject)
    old = load_cards(a.subject)
    status_p = WORK / a.subject / 'status.json'
    done = set(read_json(status_p).get('done', [])) if status_p.exists() else set()
    topics = [t for t in (a.topics.split(',') if a.topics else sorted(lad)) if t and t not in done]
    plan = {}
    n = a.start
    for i in range(0, len(topics), a.size):
        chunk = topics[i:i + a.size]
        write_json(batch_path(a.subject, n, 'in'),
                   {'subject': a.subject, 'batch': n,
                    'topics': [packet(a.subject, t, lad[t], old.get(t)) for t in chunk]})
        plan[f'b{n:03d}'] = chunk
        n += 1
    write_json(WORK / a.subject / f'plan_from_b{a.start:03d}.json', plan)
    print(f'{a.subject}: {len(topics)} topics in {len(plan)} batches (b{a.start:03d}..b{n - 1:03d})')


if __name__ == '__main__':
    main()
