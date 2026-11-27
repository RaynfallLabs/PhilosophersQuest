"""Build the live science bank from the finished units (plan section 4, step 5).

    py -m bankbuild.science_refresh.build_bank            # counts only (dry run)
    py -m bankbuild.science_refresh.build_bank --write    # archive the old bank, write the new one

Reads every unit that has a saved `card.json`, keeps its final questions
minus the ones listed in `pick.json` ({"drop": {"<hash>": "<why>"}}), and writes
  data/questions/science.json        [{tier, question, answer, choices, context, topic}]
  data/question_contexts/science.json {topic: {title, context_blurb, teaches}}
`teaches` keeps only the kept questions' sentences. The old bank and cards are
copied once to bankbuild/science/_pre_refresh_backup/ and never deleted.
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import Counter

from bankbuild.cards.common import stem_hash
from bankbuild.science_refresh.common import HERE, ROOT, UNITS_DIR, load_units, read_json

QUESTIONS = ROOT / 'data' / 'questions' / 'science.json'
CONTEXTS = ROOT / 'data' / 'question_contexts' / 'science.json'
BACKUP = ROOT / 'bankbuild' / 'science' / '_pre_refresh_backup'
PICK = HERE / 'pick.json'
FIELDS = ('tier', 'question', 'answer', 'choices', 'context', 'topic')


def assemble() -> tuple[list[dict], dict, Counter, list[str]]:
    drop = (read_json(PICK, {}) or {}).get('drop', {})
    questions, contexts, counts, missing = [], {}, Counter(), []
    for u in load_units():
        uid = u['id']
        card = read_json(UNITS_DIR / uid / 'card.json')
        final = read_json(UNITS_DIR / uid / 'final.json')
        if not card or not final:
            missing.append(uid)
            continue
        kept = []
        for q in final['questions']:
            h = stem_hash(q['question'])
            if h in drop:
                continue
            row = {k: q[k] for k in FIELDS if k in q}
            row['tier'] = int(u['tier'])
            row['topic'] = uid
            kept.append((h, row))
            counts[(u['tier'], u['strand'])] += 1
        questions.extend(r for _, r in kept)
        hashes = {h for h, _ in kept}
        contexts[uid] = {
            'title': u['title'],
            'context_blurb': card['context_blurb'],
            'teaches': {h: s for h, s in (card.get('teaches') or {}).items() if h in hashes},
        }
    return questions, contexts, counts, missing


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    questions, contexts, counts, missing = assemble()
    tiers = Counter(q['tier'] for q in questions)
    for t in sorted(tiers):
        row = {s: counts[(t, s)] for s in ('physical', 'life', 'earth', 'method')}
        print(f'T{t}: {tiers[t]:4}  ' + '  '.join(f'{s} {n}' for s, n in row.items()))
    print(f'total {len(questions)} questions in {len(contexts)} units; {len(missing)} units not finished')
    if missing:
        print('  not finished: ' + ', '.join(missing))
    if '--write' not in sys.argv:
        return
    if missing:
        raise SystemExit('refusing to write: some units are not finished')
    BACKUP.mkdir(parents=True, exist_ok=True)
    for src, name in ((QUESTIONS, 'science_questions.json'), (CONTEXTS, 'science_contexts.json')):
        dst = BACKUP / name
        if not dst.exists():
            shutil.copy2(src, dst)
    QUESTIONS.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    CONTEXTS.write_text(json.dumps(contexts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'wrote {QUESTIONS.relative_to(ROOT)} and {CONTEXTS.relative_to(ROOT)}; old bank kept in {BACKUP.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
