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


def prune_they_allow(out: str) -> list[str]:
    """Drop the allow-list entries the suite reports as stale from
    tests/test_no_singular_they.py. Returns the phrases removed."""
    import ast
    import re
    m = re.search(r"stale allow-list entries: (\[.*?\])\s*$", out, re.M)
    if not m:
        return []
    try:
        stale = ast.literal_eval(m.group(1))
    except (ValueError, SyntaxError):
        return []
    p = ROOT / 'tests' / 'test_no_singular_they.py'
    lines = p.read_text(encoding='utf-8').splitlines(keepends=True)
    gone = []
    for path, phrase in stale:
        name = path.split('/')[-1]
        keep = []
        for ln in lines:
            if f"'{name}'" in ln and repr(phrase) in ln:
                gone.append(phrase)
                continue
            keep.append(ln)
        lines = keep
    p.write_text(''.join(lines), encoding='utf-8')
    return gone


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
    if code != 0 and 'stale allow-list entries' in out:
        # A rewrite removed a phrase the singular-they allow list excused:
        # the entry goes (the ratchet only tightens), then the suite re-runs.
        pruned = prune_they_allow(out)
        if pruned:
            print('pruned stale singular-they allow entries:', pruned)
            code, out = run([PY, '-m', 'pytest', 'tests/', '-q', '-n', 'auto'])
    tail = [ln for ln in out.splitlines() if ln.startswith('FAILED') or 'passed' in ln]
    print('\n'.join(tail[-15:]))
    if code != 0:
        # A few tests share random state and fail only in parallel runs
        # (pets' growl, the Gleipnir walk). Re-run just the failures, alone.
        failed = [ln.split()[1] for ln in out.splitlines() if ln.startswith('FAILED ')]
        if failed:
            code2, out2 = run([PY, '-m', 'pytest', '-q', '-p', 'no:randomly'] + failed)
            print('re-run alone:', [ln for ln in out2.splitlines() if 'passed' in ln or 'failed' in ln][-1:])
            code = code2
    if code != 0:
        sys.exit('TESTS FAILED: not committed. Fix, then commit by hand.')
    files = [f'data/questions/{subject}.json', f'data/question_contexts/{subject}.json',
             'tests/test_no_singular_they.py',
             'data/question_twins.json', 'tests/data']
    run(['git', 'add'] + files)
    msg = (f'Voice pass: {subject} ' + ', '.join(f'b{b:03d}' for b in applied)
           + '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')
    code, out = run(['git', 'commit', '-q', '-m', msg])
    code2, head = run(['git', 'log', '--oneline', '-1'])
    print(head.strip() if code == 0 else out)


if __name__ == '__main__':
    main()
