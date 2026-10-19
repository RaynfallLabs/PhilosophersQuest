"""Fix question text by stem hash, keeping teaching cards in step.

    py -m bankbuild.cards.fix_questions fixes.json [--write]

fixes.json is a list of
    {"subject": "animal", "hash": "e7897d5f51", "field": "question"|"answer"|"context",
     "old": "<exact substring>", "new": "<replacement>"}

A fix to the answer is applied to the matching choice as well, so the key
always sits among the choices. When a stem changes, its hash changes; the
topic's `teaches` entry in data/question_contexts/<subject>.json moves to the
new hash. Without --write it only reports what it would do.
"""
from __future__ import annotations

import json
import sys

from bankbuild.cards.common import CDIR, QDIR, stem_hash


def main() -> None:
    fixes = json.loads(open(sys.argv[1], encoding='utf-8').read())
    write = '--write' in sys.argv
    by_subject: dict[str, list] = {}
    for f in fixes:
        by_subject.setdefault(f['subject'], []).append(f)
    for subject, fs in by_subject.items():
        qpath = QDIR / f'{subject}.json'
        raw = qpath.read_text(encoding='utf-8')
        qs = json.loads(raw)
        cpath = CDIR / f'{subject}.json'
        cards = json.loads(cpath.read_text(encoding='utf-8')) if cpath.exists() else {}
        index = {stem_hash(q['question']): q for q in qs}
        alias: dict[str, str] = {}          # a hash an earlier fix in this run replaced
        for f in fs:
            h = f['hash']
            while h in alias:
                h = alias[h]
            q = index.get(h)
            if q is None:
                print(f'  ! {subject} {f["hash"]}: no such question')
                continue
            field = f['field']
            hay = ' | '.join(q.get('choices', [])) if field == 'choices' else str(q.get(field, ''))
            if f['old'] not in hay:
                print(f'  ! {subject} {f["hash"]}: "{f["old"][:40]}" not in {field}')
                continue
            old_hash = stem_hash(q['question'])
            if field == 'answer':
                old_ans = q['answer']
                q['answer'] = old_ans.replace(f['old'], f['new'])
                q['choices'] = [q['answer'] if c == old_ans else c for c in q.get('choices', [])]
            elif field == 'choices':
                # Every choice (and the key, kept identical to its choice).
                was_key = [c == q['answer'] for c in q.get('choices', [])]
                q['choices'] = [c.replace(f['old'], f['new']) for c in q.get('choices', [])]
                for c, k in zip(q['choices'], was_key):
                    if k:
                        q['answer'] = c
            else:
                q[field] = q[field].replace(f['old'], f['new'])
            new_hash = stem_hash(q['question'])
            moved = ''
            if new_hash != old_hash:
                entry = cards.get(q.get('topic'))
                if isinstance(entry, dict) and old_hash in (entry.get('teaches') or {}):
                    entry['teaches'][new_hash] = entry['teaches'].pop(old_hash)
                    moved = ' (teaches re-keyed)'
                index[new_hash] = index.pop(old_hash)
                alias[old_hash] = new_hash
            print(f'  {subject} {f["hash"]} {field}: "{f["old"][:50]}" -> "{f["new"][:50]}"{moved}')
        if write:
            text = json.dumps(qs, ensure_ascii=False, indent=2)   # every bank file is indent-2
            qpath.write_text(text + ('\n' if raw.endswith('\n') else ''), encoding='utf-8', newline='\n')
            cpath.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(f'{subject}: written')


if __name__ == '__main__':
    main()
