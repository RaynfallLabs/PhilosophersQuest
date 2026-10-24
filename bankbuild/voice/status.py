"""Where the voice pass stands.

    py -m bankbuild.voice.status [subject ...]

One line per subject: ladders done of all, batches by state, and the
voice-lint pass rate of the bank as it is now.
"""
from __future__ import annotations

import sys

from bankbuild.cards.common import ladders
from bankbuild.voice.common import ORDER, WORK, status
from bankbuild.voice.lint import bank_report


def main() -> None:
    subjects = sys.argv[1:] or [s for s in ORDER]
    for s in subjects:
        st = status(s)
        n = len(ladders(s))
        states: dict[str, int] = {}
        for b in st['batches'].values():
            states[b.get('state', '?')] = states.get(b.get('state', '?'), 0) + 1
        r = bank_report(s)
        print(f"{s:10} {len(st['done']):4}/{n:<4} ladders done   batches "
              + (', '.join(f'{k} {v}' for k, v in sorted(states.items())) or 'none')
              + f"   lint pass {r['clean'] * 100 / r['n']:.0f}%")
    if not WORK.exists():
        print('(no _voice/ working folder yet)')


if __name__ == '__main__':
    main()
