"""Apply judged batches, run the suite, and commit only when it is green.

    py -m bankbuild.voice.land <subject> <batch>[,<batch>...] [--hold a,b]

Runs `apply --write` for each batch (passing ladders only), then the fast
suite. On any failure it prints the failing tests and stops WITHOUT
committing (the working tree keeps the applied changes for a fix). On
success it commits the bank, cards, twins file and test baselines.
"""
from __future__ import annotations

import subprocess
import sys

from bankbuild.cards.common import ROOT

PY = sys.executable


def run(args: list[str]) -> tuple[int, str]:
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def main() -> None:
    subject = sys.argv[1]
    batches = [int(b) for b in sys.argv[2].split(',') if b]
    hold = []
    if '--hold' in sys.argv:
        hold = ['--hold', sys.argv[sys.argv.index('--hold') + 1]]
    applied = []
    for b in batches:
        code, out = run([PY, '-m', 'bankbuild.voice.apply', subject, str(b), '--write'] + hold)
        last = out.strip().splitlines()[-1] if out.strip() else ''
        print(last)
        if code == 0 and 'applied' in last:
            applied.append(b)
    if not applied:
        sys.exit('nothing applied')
    code, out = run([PY, '-m', 'pytest', 'tests/', '-q', '-n', 'auto'])
    tail = [ln for ln in out.splitlines() if ln.startswith('FAILED') or 'passed' in ln]
    print('\n'.join(tail[-15:]))
    if code != 0:
        sys.exit('TESTS FAILED: not committed. Fix, then commit by hand.')
    files = [f'data/questions/{subject}.json', f'data/question_contexts/{subject}.json',
             'data/question_twins.json', 'tests/data']
    run(['git', 'add'] + files)
    msg = (f'Voice pass: {subject} ' + ', '.join(f'b{b:03d}' for b in applied)
           + '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')
    code, out = run(['git', 'commit', '-q', '-m', msg])
    code2, head = run(['git', 'log', '--oneline', '-1'])
    print(head.strip() if code == 0 else out)


if __name__ == '__main__':
    main()
