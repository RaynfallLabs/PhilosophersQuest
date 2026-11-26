"""Where every unit stands, read from the files it has (plan section 10).

    py -m bankbuild.science_refresh.status            # counts per step, and what is next
    py -m bankbuild.science_refresh.status --all      # one line per unit

A unit's step is the last file it has, in pipeline order:
  draft.json      authored (facts.md beside it)
  judge.json      judged
  factcheck.json  fact-checked
  final.json      revised
  recheck.json    re-checked (finalize has dropped what still failed)
  card.json       covered (the card passed its gate and the cold reader)

Build order: the units in tier order, the stance units last (Brandon was
asked about the COVID unit on 2026-11-25), so an answer from him can still
reshape them before they are written.
"""
from __future__ import annotations

import sys

from bankbuild.science_refresh.common import UNITS_DIR, load_units, state

FILES = (('draft.json', 'authored'), ('judge.json', 'judged'), ('factcheck.json', 'factchecked'),
         ('final.json', 'revised'), ('recheck.json', 'rechecked'), ('card.json', 'covered'))
ORDER = ('new',) + tuple(s for _f, s in FILES)
STANCE_LAST = ('the-covid-record-weighed',)


def is_stance(u: dict) -> bool:
    return u.get('framing_note', '').startswith('STANCE')


def build_order(units: list[dict]) -> list[dict]:
    def key(u):
        return (u['id'] in STANCE_LAST, is_stance(u), u['tier'], units.index(u))
    return sorted(units, key=key)


def step_of(uid: str) -> str:
    d = UNITS_DIR / uid
    step = 'new'
    for fname, name in FILES:
        if (d / fname).exists():
            step = name
    if step == 'rechecked' and 'rechecked' not in state(uid):
        step = 'revised'            # recheck.json written, finalize not yet run
    return step


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    units = build_order(load_units())
    steps = {u['id']: step_of(u['id']) for u in units}
    if '--all' in sys.argv:
        for u in units:
            tag = ' stance' if is_stance(u) else ''
            print(f"T{u['tier']} {steps[u['id']]:12} {u['id']}{tag}")
        return
    for s in ORDER:
        ids = [u['id'] for u in units if steps[u['id']] == s]
        print(f'{s:12} {len(ids):3}  next: {", ".join(ids[:6])}')
    print(f"units {len(units)}, questions to write {sum(u.get('target_q', 0) for u in units)}")


if __name__ == '__main__':
    main()
