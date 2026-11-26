"""Close a unit's one revision: drop whatever the re-check failed (plan section 4, step 6).

    py -m bankbuild.science_refresh.finalize <unit> [<unit> ...]

Every question the reviser changed or added must have a re-check verdict.
A `fail` (or a missing verdict) moves the question to `dropped`, so a unit
leaves the revision round with only questions that passed every stage.
"""
from __future__ import annotations

import sys

from bankbuild.cards.common import stem_hash
from bankbuild.science_refresh.common import UNITS_DIR, mark, read_json, write_json


def finalize(uid: str) -> str:
    d = UNITS_DIR / uid
    final = read_json(d / 'final.json')
    if not final:
        return f'{uid}: no final.json'
    changed = set(final.get('revised') or {}) | set(final.get('added') or {})
    recheck = (read_json(d / 'recheck.json', {}) or {}).get('questions', {})
    keep, dropped = [], list(final.get('dropped') or [])
    for q in final['questions']:
        h = stem_hash(q['question'])
        if h in changed:
            v = recheck.get(h)
            if not v or v.get('verdict') != 'pass':
                why = (v or {}).get('why') or 'no re-check verdict'
                dropped.append({'old_hash': h, 'question': q['question'], 'why': f'failed the re-check: {why}'})
                continue
        keep.append(q)
    final['questions'] = keep
    final['dropped'] = dropped
    write_json(d / 'final.json', final)
    mark(uid, 'rechecked', kept=len(keep), dropped=len(dropped))
    return f'{uid}: {len(keep)} questions final, {len(dropped)} dropped in all'


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    for uid in sys.argv[1:]:
        print(finalize(uid))


if __name__ == '__main__':
    main()
