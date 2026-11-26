"""The refresh's mechanical gates (plan section 4, step 3). No model runs here.

    py -m bankbuild.science_refresh.gates                 # gate every unit
    py -m bankbuild.science_refresh.gates solar-system    # print one unit's findings
    py -m bankbuild.science_refresh.gates --kind draft u1  # gate the drafts, not finals

The question gates are the repo's own: `bankbuild.cards.stage.check` run over
the NEW bank (every live science question deleted, every unit's questions
added), so the refresh is held to exactly what the suite and later card
batches hold every bank to:
  - the Chronicler voice lint (bankbuild/voice/lint.py);
  - the tell gate: the stem prints its own answer, or shares a two-word run
    with the answer and no wrong choice;
  - choice parity (longest choice at most 3.5x the shortest; the science
    gate's shape parity);
  - numbers as answers (a bare year, ratio or percent keyed to a
    "how much / what year" stem);
  - acronyms taught before tested;
  - no singular "they";
  - duplicates across the whole new bank;
  - the science content gates (tools/quizgen/gates/science.py).
Some of stage's checks are information only here, by ruling:
  - length_budget and the voice lint's word bands (short, long, too_long, and
    the closer's length): science has no quiz clock any more, and Brandon
    ruled on 2026-11-25 that length is never a gate (subject matter and
    clarity are);
  - anti_rote at T1-T2: plain basics are allowed at T1-T2 (ruling 11-16); the
    gate itself is changed in the section-6 sweep.
`bankbuild/tellgate.py` adds its telegraph patterns as FLAGS for the
adversarial judge to confirm or clear (PIPELINE section 6), never as failures.

The refresh's own structure gates:
  - every unit names at least one line of the curriculum map, and every line
    it names is in its own grade (T1 = 5th ... T5 = 9th);
  - every question sits in its unit's tier and carries the unit id as topic;
  - unit titles are Title Case.
Findings go to units/<id>/gates.json: {hash: {fail, warn, info, flag}}.
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys

from bankbuild.cards.common import QDIR, stem_hash
from bankbuild.science_refresh.common import (SUBJECT, TIER_GRADE, UNITS_DIR, load_units,
                                              map_lines, unit_questions, write_json)

LINE_RE = re.compile(r'^\s+(FAIL|warn) ([0-9a-f]{10}) \(([^,]*), T(\d)\): (.*)$')
INFO_ALWAYS = ('length_budget:', 'voice: short(', 'voice: long(', 'voice: too_long(',
               'voice: closer_long(', 'voice: closer_too_long(')
INFO_LOW_TIERS = ('anti_rote:',)
SMALL_WORDS = frozenset('a an the and or nor but of in on at to for by with from as vs via into'.split())


def title_problems(title: str) -> list[str]:
    ws = re.findall(r"[A-Za-z][\w'-]*", title or '')
    if not ws:
        return ['no title']
    # A word that already carries a capital inside it (pH, mRNA) is written
    # the way science writes it.
    bad = [w for i, w in enumerate(ws)
           if w[0].islower() and not any(c.isupper() for c in w)
           and (i == 0 or w.lower() not in SMALL_WORDS)]
    return [f'title not Title Case: {", ".join(bad)}'] if bad else []


def unit_problems(u: dict, lines: dict[str, dict], qs: list[dict]) -> list[str]:
    errs = []
    tier = u.get('tier')
    if tier not in TIER_GRADE:
        return [f'unit tier {tier!r} is not 1-5']
    named = u.get('map_lines') or []
    if not named:
        errs.append('names no line of the curriculum map')
    for lid in named:
        line = lines.get(lid)
        if line is None:
            errs.append(f'map line {lid} is not in curriculum_map.json')
        elif line['grade'] != TIER_GRADE[tier]:
            errs.append(f'map line {lid} is grade {line["grade"]}, but T{tier} is grade {TIER_GRADE[tier]}')
    errs += title_problems(u.get('title', ''))
    for q in qs:
        h = stem_hash(q.get('question', ''))
        if q.get('tier') != tier:
            errs.append(f'{h}: tier {q.get("tier")} in a T{tier} unit')
        if q.get('topic') != u['id']:
            errs.append(f'{h}: topic {q.get("topic")!r} is not the unit id')
    answers = [str(q.get('answer', '')).strip().lower() for q in qs]
    for a in sorted({a for a in answers if answers.count(a) > 1}):
        errs.append(f'two questions key the same answer: "{a}"')
    return errs


def run(kind_pref: tuple[str, ...] = ('final', 'draft'), write: set[str] | None = None) -> dict:
    """Gate every unit's questions together. Returns {unit_id: report}.

    Every unit's questions go into the bank (duplicates are checked across
    all of them), but gates.json is written only for the units in `write`
    (all of them when it is None), so agents gating their own units at the
    same time never rewrite each other's reports. A unit whose file does not
    parse (an author mid-write) is left out and reported, never a crash."""
    from bankbuild.cards.stage import check
    from bankbuild.tellgate import gate as tell_gate

    units = load_units()
    lines = map_lines()
    bank: list[dict] = []
    per_unit: dict[str, list[dict]] = {}
    which: dict[str, str] = {}
    broken: dict[str, str] = {}
    for u in units:
        try:
            kind, qs = unit_questions(u['id'], kind_pref)
        except (ValueError, KeyError, TypeError) as e:
            kind, qs = '', []
            broken[u['id']] = f'{type(e).__name__}: {e}'
        which[u['id']] = kind
        per_unit[u['id']] = qs
        bank += [dict(q) for q in qs]
    live = json.loads((QDIR / f'{SUBJECT}.json').read_text(encoding='utf-8'))
    changes = {'delete': sorted({stem_hash(q['question']) for q in live}), 'add': bank}

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        check(SUBJECT, [changes])
    found: dict[str, dict[str, list[str]]] = {}
    loose: list[str] = []
    for raw in buf.getvalue().splitlines():
        m = LINE_RE.match(raw)
        if not m:
            if raw.strip().startswith('FAIL'):
                loose.append(raw.strip())
            continue
        level, h, _topic, tier, msg = m.groups()
        slot = 'fail' if level == 'FAIL' else 'warn'
        if msg.startswith(INFO_ALWAYS) or (msg.startswith(INFO_LOW_TIERS) and int(tier) <= 2):
            slot = 'info'
        found.setdefault(h, {'fail': [], 'warn': [], 'info': [], 'flag': []})[slot].append(msg)

    reports = {}
    for u in units:
        qs = per_unit[u['id']]
        if u['id'] in broken:
            reports[u['id']] = {'kind': 'unparsed', 'unit': [f'its file does not parse: {broken[u["id"]]}'],
                                'questions': {}, 'n_fail': 1}
            continue
        rep = {'kind': which[u['id']], 'unit': unit_problems(u, lines, qs), 'questions': {}}
        for q in qs:
            h = stem_hash(q['question'])
            r = found.get(h, {'fail': [], 'warn': [], 'info': [], 'flag': []})
            r = {k: list(v) for k, v in r.items()}
            r['flag'] += [f"tell:{f['pattern']}: {f['detail']}" for f in tell_gate(q)]
            rep['questions'][h] = r
        rep['n_fail'] = len(rep['unit']) + sum(len(r['fail']) for r in rep['questions'].values())
        reports[u['id']] = rep
        if qs and (write is None or u['id'] in write):
            write_json(UNITS_DIR / u['id'] / 'gates.json', rep)
    if loose:
        reports['_loose'] = loose
    return reports


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    args = sys.argv[1:]
    pref = ('final', 'draft')
    if '--kind' in args:
        i = args.index('--kind')
        pref = (args[i + 1],)
        args = args[:i] + args[i + 2:]
    reports = run(pref, set(args) if args else None)
    for line in reports.pop('_loose', []):
        print('BANK', line)
    show = args or [u for u, r in reports.items() if r['kind']]
    total = 0
    for uid in show:
        r = reports.get(uid)
        if not r:
            print(f'{uid}: no such unit in units.json')
            continue
        if not r['kind']:
            print(f'{uid}: no questions yet')
            continue
        total += r['n_fail']
        print(f'{uid} ({r["kind"]}): {len(r["questions"])} questions, {r["n_fail"]} failures')
        for e in r['unit']:
            print('  UNIT', e)
        for h, f in r['questions'].items():
            for slot in ('fail', 'warn', 'flag', 'info'):
                for msg in f[slot]:
                    print(f'  {slot.upper():4} {h}: {msg}')
    print(f'TOTAL failures in the units shown: {total}')
    sys.exit(1 if total else 0)


if __name__ == '__main__':
    main()
