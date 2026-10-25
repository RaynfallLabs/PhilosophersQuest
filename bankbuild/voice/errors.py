"""Gather the question errors the voice-pass writers report.

    py -m bankbuild.voice.errors      # writes _voice/QUESTION_ERRORS.md

Writers never fix a fact in this pass: a false key, a wrong answer that is
also right, a stem that contradicts its context or card goes in their notes
file. This collects every batch's list, by subject, for a fix pass.
"""
from __future__ import annotations

import json

from bankbuild.voice.common import ORDER, WORK


def main() -> None:
    lines = ['# Question errors found by the voice pass', '',
             'Each was left as it is (keys and facts never change in the voice pass).', '']
    total = 0
    for s in ORDER:
        rows = []
        for p in sorted((WORK / s).glob('b*_notes.json')):
            notes = json.loads(p.read_text(encoding='utf-8'))
            for e in notes.get('question_errors') or []:
                if isinstance(e, dict):
                    rows.append(f"- `{e.get('hash', '')}` ({p.name[:4]}): {e.get('problem', '')}")
                else:
                    rows.append(f'- ({p.name[:4]}): {e}')
        if rows:
            lines += [f'## {s} ({len(rows)})', ''] + rows + ['']
            total += len(rows)
    (WORK / 'QUESTION_ERRORS.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'{total} question errors -> {WORK / "QUESTION_ERRORS.md"}')


if __name__ == '__main__':
    main()
