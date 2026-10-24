"""Cut a subject's ladders into voice-pass writer batches.

    py -m bankbuild.voice.extract <subject> [--size 25] [--topics a,b,c] [--limit N]

Ladders joined by a same-fact twin group (data/question_twins.json) always
land in the same batch, so one writer decides each merge. Topics already
done, or already in an extracted batch, are skipped, so re-running is safe.
Each batch gets the next free number. Writes _voice/<subject>/bNNN_in.json.
"""
from __future__ import annotations

import argparse

from bankbuild.cards.common import ladders, load_cards, strip_source
from bankbuild.voice.common import (bpath, gid, save_status, stem_hash, status, subject_config,
                                    twin_groups, write_json)
from bankbuild.voice.lint import lint_stem


def components(topics: list[str], groups: list[list[str]], topic_of: dict) -> list[list[str]]:
    """Topics joined by twin groups, each component in sorted order, the
    components ordered by their first topic."""
    parent = {t: t for t in topics}

    def find(t):
        while parent[t] != t:
            parent[t] = parent[parent[t]]
            t = parent[t]
        return t
    for g in groups:
        ts = sorted({topic_of[h] for h in g if topic_of.get(h) in parent})
        for t in ts[1:]:
            parent[find(t)] = find(ts[0])
    comps: dict[str, list[str]] = {}
    for t in topics:
        comps.setdefault(find(t), []).append(t)
    return sorted((sorted(c) for c in comps.values()), key=lambda c: c[0])


def packet(subject: str, batch: int, topics: list[str], lad: dict, cards: dict,
           groups: list[list[str]]) -> dict:
    in_batch = {stem_hash(q['question']) for t in topics for q in lad[t]}
    topic_of = {stem_hash(q['question']): t for t in topics for q in lad[t]}
    gmap = {}
    out_groups = {}
    for g in groups:
        members = [h for h in g if h in in_batch]
        if len(members) >= 2:
            name = gid(g)
            out_groups[name] = [{'hash': h, 'topic': topic_of[h]} for h in members]
            for h in members:
                gmap[h] = name
    cfg = subject_config(subject)
    out = []
    for t in topics:
        card = cards.get(t) if isinstance(cards.get(t), dict) else {}
        qs = []
        for q in lad[t]:
            h = stem_hash(q['question'])
            f, w = lint_stem(q['question'], subject, int(q.get('tier', 1)))
            qs.append({'hash': h, 'tier': int(q.get('tier', 1)), 'stem': q['question'],
                       'answer': q['answer'], 'choices': q.get('choices', []),
                       'context': strip_source(q.get('context', '')),
                       'lint': {'fail': f, 'warn': w}, 'twin_group': gmap.get(h)})
        out.append({'topic': t, 'title': card.get('title', ''),
                    'card': card.get('context_blurb', ''), 'questions': qs})
    return {'subject': subject, 'batch': batch, **cfg, 'twin_groups': out_groups, 'topics': out}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('subject')
    ap.add_argument('--size', type=int, default=25)
    ap.add_argument('--topics', default='')
    ap.add_argument('--limit', type=int, default=0, help='at most this many batches')
    a = ap.parse_args()
    lad = ladders(a.subject)
    cards = load_cards(a.subject)
    groups = twin_groups(a.subject)
    st = status(a.subject)
    taken = set(st['done']) | {t for b in st['batches'].values() for t in b['topics']}
    want = [t for t in (a.topics.split(',') if a.topics else sorted(lad)) if t]
    missing = [t for t in want if t not in lad]
    if missing:
        raise SystemExit(f'no such topics: {missing}')
    topic_of = {stem_hash(q['question']): t for t, qs in lad.items() for q in qs}
    # A named topic brings its whole twin component with it.
    comps = components(sorted(lad), groups, topic_of)
    wanted = set(want)
    comps = [c for c in comps if wanted & set(c)]
    comps = [[t for t in c if t not in taken] for c in comps]
    comps = [c for c in comps if c]
    nums = [int(k[1:]) for k in st['batches']] or [0]
    n = max(nums) + 1
    made = []
    cur: list[str] = []

    def flush():
        nonlocal n, cur
        if cur:
            write_json(bpath(a.subject, n, 'in'), packet(a.subject, n, cur, lad, cards, groups))
            st['batches'][f'b{n:03d}'] = {'topics': cur, 'state': 'extracted'}
            made.append((n, len(cur), sum(len(lad[t]) for t in cur)))
            n += 1
            cur = []
    for c in comps:
        if a.limit and len(made) >= a.limit:
            break
        if cur and len(cur) + len(c) > a.size:
            flush()
            if a.limit and len(made) >= a.limit:
                break
        cur += c
    if not (a.limit and len(made) >= a.limit):
        flush()
    save_status(a.subject, st)
    for num, nt, nq in made:
        print(f'{a.subject} b{num:03d}: {nt} ladders, {nq} questions')
    if not made:
        print(f'{a.subject}: nothing left to extract')


if __name__ == '__main__':
    main()
