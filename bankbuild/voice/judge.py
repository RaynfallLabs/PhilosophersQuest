"""Voice-pass judge packets and scoring.

    py -m bankbuild.voice.judge packet <subject> <batch> [--only topic,topic]
        -> bNNN_judge_in.json: for each ladder, its card, and for each
           surviving question its new stem, its shuffled choices and the old
           stem or stems it replaces. No keyed answers.
    py -m bankbuild.voice.judge score <subject> <batch>
        -> reads bNNN_judge.json, writes bNNN_score.json (topics judged this
           round replace their earlier result), prints a summary.

The judge output, per topic:
    {"voice": 1-5, "notes": "...", "twins_left": [[hash, hash], ...],
     "q": {"<new hash>": {"pick": "<choice>", "quote": "<card sentence or NONE>",
                          "same": true|false, "new_fact": "" | "<the claim>",
                          "tier": 1-5 (merged questions only), "note": "..."}}}

A question PASSES when the pick is the key, the quote is in the card, the new
stem asks what the old one asked ("same"), it adds no fact ("new_fact"
empty), and, for a merged question, the judge's tier is within one of the
writer's. A ladder passes when every question passes, its voice scores 4 or
5, and no twins are left.
"""
from __future__ import annotations

import sys

from bankbuild.cards import stage
from bankbuild.cards.common import norm, shuffled_choices, words
from bankbuild.voice.common import bpath, load_changes, load_notes, read_json, stem_hash, write_json


def _survivors(subject: str, batch: int) -> tuple[dict, dict, dict]:
    """({topic: [staged question]}, {new hash: [old stems]}, {new hash: merge})."""
    pkt = read_json(bpath(subject, batch, 'in'))
    ch = load_changes(subject, batch)
    notes = load_notes(subject, batch)
    bank, probs, _changed = stage.staged_bank(subject, [ch])
    if probs:
        sys.exit('fix the change file first:\n  ' + '\n  '.join(probs))
    topics = [t['topic'] for t in pkt['topics']]
    old_stem = {q['hash']: q['stem'] for t in pkt['topics'] for q in t['questions']}
    new_of = {r['hash']: stem_hash((r.get('new') or {}).get('question', old_stem.get(r['hash'], '')))
              for r in ch.get('replace') or []}
    before: dict[str, list[str]] = {}
    for h, stem in old_stem.items():
        before.setdefault(new_of.get(h, h), []).append(stem)
    merge_of: dict[str, dict] = {}
    for m in notes['merges']:
        nh = new_of.get(m['keep'], m['keep'])
        merge_of[nh] = m
        before[nh] = [old_stem[m['keep']]] + [old_stem[a] for a in m.get('absorbed') or []
                                              if a in old_stem]
    lad: dict[str, list[dict]] = {t: [] for t in topics}
    for q in bank:
        if q.get('topic') in lad:
            lad[q['topic']].append(q)
    for t in lad:
        lad[t].sort(key=lambda q: int(q.get('tier', 1)))
    return lad, before, merge_of


def make_packet(subject: str, batch: int, only: set[str] | None = None) -> int:
    pkt = read_json(bpath(subject, batch, 'in'))
    lad, before, merge_of = _survivors(subject, batch)
    out = []
    for t in pkt['topics']:
        name = t['topic']
        if only and name not in only:
            continue
        qs = []
        for q in lad[name]:
            h = stem_hash(q['question'])
            item = {'hash': h, 'stem': q['question'], 'choices': shuffled_choices(q),
                    'before': before.get(h, [q['question']])}
            if h in merge_of:
                item['merged'] = True
            qs.append(item)
        out.append({'topic': name, 'card': t.get('card', ''), 'questions': qs})
    write_json(bpath(subject, batch, 'judge_in'),
               {'subject': subject, 'batch': batch, 'topics': out})
    return len(out)


def score(subject: str, batch: int) -> dict:
    pkt = read_json(bpath(subject, batch, 'in'))
    lad, _before, merge_of = _survivors(subject, batch)
    judged = read_json(bpath(subject, batch, 'judge'))
    sp = bpath(subject, batch, 'score')
    res = read_json(sp) if sp.exists() else {}
    for t in pkt['topics']:
        name = t['topic']
        if name not in judged:
            continue
        j = judged[name] or {}
        hay = ' '.join(words(t.get('card', '')))
        fails = []
        for q in lad[name]:
            h = stem_hash(q['question'])
            jq = (j.get('q') or {}).get(h) or {}
            why = []
            if norm(str(jq.get('pick', ''))) != norm(q['answer']):
                why.append('wrong pick')
            quote = str(jq.get('quote', ''))
            if not norm(quote) or norm(quote) == 'none' or norm(quote) not in hay:
                why.append('unsupported quote')
            if jq.get('same') is not True:
                why.append('asks something else')
            if str(jq.get('new_fact', '') or '').strip():
                why.append(f'new fact: {jq["new_fact"]}')
            if h in merge_of:
                try:
                    if abs(int(jq.get('tier')) - int(merge_of[h]['tier'])) > 1:
                        why.append(f'tier: judge {jq.get("tier")}, writer {merge_of[h]["tier"]}')
                except (TypeError, ValueError):
                    why.append('tier: not rated')
            if why:
                fails.append({'hash': h, 'tier': q.get('tier'), 'why': '; '.join(why),
                              'judge_pick': jq.get('pick', ''), 'note': jq.get('note', '')})
        voice = j.get('voice')
        ladder = []
        if not isinstance(voice, int) or voice < 4:
            ladder.append(f'voice {voice}: {j.get("notes", "")}')
        if j.get('twins_left'):
            ladder.append(f'twins left: {j["twins_left"]}')
        res[name] = {'pass': not fails and not ladder, 'fails': fails, 'ladder': ladder,
                     'voice': voice}
    write_json(sp, res)
    return res


def main() -> None:
    cmd, subject, batch = sys.argv[1], sys.argv[2], int(sys.argv[3])
    if cmd == 'packet':
        only = None
        if '--only' in sys.argv:
            only = set(sys.argv[sys.argv.index('--only') + 1].split(','))
        n = make_packet(subject, batch, only)
        print(f'{subject} b{batch:03d}: judge packet with {n} ladders')
    elif cmd == 'score':
        res = score(subject, batch)
        ok = sum(1 for r in res.values() if r['pass'])
        nq = sum(len(r['fails']) for r in res.values())
        print(f'{subject} b{batch:03d}: {ok}/{len(res)} ladders pass; {nq} questions fail')
        for t, r in res.items():
            if not r['pass']:
                bits = [f"T{f['tier']} {f['hash']} ({f['why']})" for f in r['fails']] + r['ladder']
                print(f'   {t}: ' + '; '.join(bits))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
