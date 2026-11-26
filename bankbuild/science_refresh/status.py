"""Where every unit stands, and what the lead launches next (plan section 10).

    py -m bankbuild.science_refresh.status                 # counts, in flight, ready per step
    py -m bankbuild.science_refresh.status --all           # one line per unit
    py -m bankbuild.science_refresh.status --launch <step> <id,id,...> [--batch N]
    py -m bankbuild.science_refresh.status --done <label>  # an agent finished
    py -m bankbuild.science_refresh.status --next-batch    # the next free card batch number

A unit's steps, read from its files (a step in flight is not "ready"):
  research   no draft.json yet                       one agent a unit
  judge      draft.json, no judge.json               one agent for up to 3 units
  factcheck  draft.json, no factcheck.json           one agent a unit
  revise     judge.json and factcheck.json, no final.json      up to 3 units
  recheck    final.json changed questions, no recheck.json      up to 3 units
  finalize   final.json (+ recheck.json when anything changed), not yet finalized (lead's script)
  card       finalized, no card batch yet            up to 3 units (lead makes the packet)
  reader     card batch written and gated, not scored           up to 6 units (2 batches)
  save       scored, no card.json                    (lead's script)
In-flight agents live in `_inflight.json` (gitignored scratch).

Build order: the units in tier order, the stance units last (Brandon was
asked about the COVID unit on 2026-11-25), so an answer from him can still
reshape them before they are written.
"""
from __future__ import annotations

import re
import sys

from bankbuild.cards.common import batch_path
from bankbuild.science_refresh.common import HERE, ROOT, UNITS_DIR, load_units, read_json, state, write_json

INFLIGHT = HERE / '_inflight.json'
STANCE_LAST = ('the-covid-record-weighed',)
STEPS = ('research', 'judge', 'factcheck', 'revise', 'recheck', 'finalize', 'card', 'reader', 'save', 'done')


def is_stance(u: dict) -> bool:
    return u.get('framing_note', '').startswith('STANCE')


def build_order(units: list[dict]) -> list[dict]:
    def key(u):
        return (u['id'] in STANCE_LAST, is_stance(u), u['tier'], units.index(u))
    return sorted(units, key=key)


def inflight() -> dict:
    return read_json(INFLIGHT, {}) or {}


def busy() -> dict[tuple[str, str], str]:
    """(unit, step) -> label, for every agent in flight."""
    out = {}
    for label, job in inflight().items():
        for uid in job['units']:
            out[(uid, job['step'])] = label
    return out


def needs(uid: str) -> set[str]:
    """Every step this unit is ready for now (judge and factcheck run side by side)."""
    d = UNITS_DIR / uid
    st = state(uid)
    if (d / 'card.json').exists():
        return {'done'}
    if not (d / 'draft.json').exists():
        return {'research'}
    out = set()
    has_j, has_f = (d / 'judge.json').exists(), (d / 'factcheck.json').exists()
    if not has_j:
        out.add('judge')
    if not has_f:
        out.add('factcheck')
    if out:
        return out
    final = read_json(d / 'final.json')
    if not final:
        return {'revise'}
    if 'rechecked' not in st:
        changed = set(final.get('revised') or {}) | set(final.get('added') or {})
        if changed and not (d / 'recheck.json').exists():
            return {'recheck'}
        return {'finalize'}
    carded = st.get('carded')
    if not carded:
        return {'card'}
    b = carded['batch'] if isinstance(carded, dict) else carded
    score = read_json(batch_path('science', b, 'score'), {}) or {}
    if uid not in score:
        return {'reader'}
    return {'save'}


def ready(units: list[dict]) -> dict[str, list[str]]:
    b = busy()
    out: dict[str, list[str]] = {s: [] for s in STEPS}
    for u in units:
        for s in sorted(needs(u['id'])):
            if (u['id'], s) not in b:
                out[s].append(u['id'])
    return out


def next_batch() -> int:
    nums = [901]
    for p in (ROOT / '_cards' / 'science').glob('b*_in.json'):
        m = re.match(r'b(\d+)_in\.json$', p.name)
        if m:
            nums.append(int(m.group(1)) + 1)
    for job in inflight().values():
        if job.get('batch'):
            nums.append(int(job['batch']) + 1)
    return max(nums)


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    args = sys.argv[1:]
    units = build_order(load_units())
    if args[:1] == ['--launch']:
        step, ids = args[1], args[2].split(',')
        job = {'step': step, 'units': ids}
        if '--batch' in args:
            job['batch'] = int(args[args.index('--batch') + 1])
        fl = inflight()
        label = f'{step}:{ids[0]}'
        fl[label] = job
        write_json(INFLIGHT, fl)
        print(label)
        return
    if args[:1] == ['--done']:
        fl = inflight()
        fl.pop(args[1], None)
        write_json(INFLIGHT, fl)
        print(f'done {args[1]}; {len(fl)} in flight')
        return
    if args[:1] == ['--next-batch']:
        print(next_batch())
        return
    if args[:1] == ['--all']:
        for u in units:
            tag = ' stance' if is_stance(u) else ''
            print(f"T{u['tier']} {','.join(sorted(needs(u['id']))):18} {u['id']}{tag}")
        return
    fl = inflight()
    print(f'in flight ({len(fl)}):')
    for label, job in fl.items():
        print(f"  {label}  {job['step']} {','.join(job['units'])}" + (f" b{job['batch']}" if job.get('batch') else ''))
    r = ready(units)
    for s in STEPS:
        ids = r[s]
        if s == 'done':
            print(f'done       {len(ids):3}')
        else:
            print(f'{s:10} {len(ids):3}  {", ".join(ids[:6])}')
    print(f"units {len(units)}, questions to write {sum(u.get('target_q', 0) for u in units)}; next card batch {next_batch()}")


if __name__ == '__main__':
    main()
