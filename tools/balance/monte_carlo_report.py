#!/usr/bin/env python
"""Report a tools/balance/monte_carlo.py run against the win targets.

Usage: py tools/balance/monte_carlo_report.py <out_dir> [sections]
Sections (default all): t targets, a ablation, l luck (mastery's deaths by
floor and the gates), d death bands and killers, p pace (turns, newcomers,
hunger, load).

The targets (Brandon 2026-11-13, feedback_mastery_survives; 2026-11-16
"Systems other than cooking should have real impact; ignoring any of them
will result in failure"):
  mastery 85-92%; slow mastery (x1.5 answer time) 65-80%; committed
  (ignores systems) 5-15%; casual 0-3%; the builds as mastery;
  no dumb luck for mastery: an ordinary floor kills under 0.05% of runs,
  floors 90-99 under 1% together, each gate with its quest 1-2%;
  ablation: taking any one system away costs at least 5 points, and none is
  worth more than about 30 alone (the 11-13 rule; the 11-16 rule is stronger).
"""
import glob
import math
import os
import pickle
import sys
from collections import Counter

TARGETS = {
    ('mastery', 1.0): (85, 92, 'every system'),
    ('mastery', 1.5): (65, 80, 'slow mastery'),
    ('mastery_mage', 1.0): (85, 92, 'as mastery'),
    ('mastery_dex', 1.0): (85, 92, 'as mastery'),
    ('committed', 1.0): (5, 15, 'ignores systems'),
    ('casual', 1.0): (0, 3, 'casual'),
}
GATES = (20, 40, 60, 80, 100)
BANDS = [(1, 9), (10, 19), (21, 39), (41, 59), (61, 79), (81, 99)]


def load(d):
    cells = {}
    for f in sorted(glob.glob(os.path.join(d, '*.pkl'))):
        with open(f, 'rb') as fh:
            r = pickle.load(fh)
        p, _a, sp, _k = r['label']
        cells[(p, sp)] = r
    return cells


def surv(r):
    st, n = r['stats'], r['trials']
    s, dead = {}, 0
    for f in range(1, 101):
        dead += st.get(f, {}).get('first_deaths', 0)
        s[f] = 1 - dead / n
    return s


def ci(p, n):
    return 1.96 * math.sqrt(max(p * (1 - p), 1e-9) / max(1, n))


def name(key):
    p, sp = key
    return f"{p}{' x' + format(sp, 'g') if sp != 1.0 else ''}"


def section_targets(cells):
    print("1. WINS against the targets (kid model, win = Abaddon dead, no death all run)")
    print(f"   {'cell':22} {'runs':>4} {'F20':>5} {'F40':>5} {'F60':>5} {'F80':>5} {'win':>5} {'+-':>3}  target")
    order = list(TARGETS) + sorted(k for k in cells if k not in TARGETS)
    for key in order:
        r = cells.get(key)
        if r is None:
            continue
        s, n = surv(r), r['trials']
        tgt = TARGETS.get(key)
        verdict = ''
        if tgt:
            lo, hi, why = tgt
            w = 100 * s[100]
            verdict = f"{lo}-{hi}% ({why}): " + ('MET' if lo <= w <= hi else
                                                  'ABOVE' if w > hi else 'BELOW')
        print(f"   {name(key):22} {n:4} {s[20]:5.0%} {s[40]:5.0%} {s[60]:5.0%} {s[80]:5.0%} "
              f"{s[100]:5.0%} {100 * ci(s[100], n):3.0f}  {verdict}")


def section_ablation(cells):
    base = cells.get(('mastery', 1.0))
    if base is None:
        return
    b = surv(base)[100]
    print("\n2. ABLATION: mastery with one system taken away (points of wins lost)")
    print(f"   mastery wins {b:.0%}. Rule of 11-13: each costs >= 5 points, none more than ~30.")
    rows = []
    for (p, sp), r in cells.items():
        if p.startswith('m_no_') and sp == 1.0:
            w = surv(r)[100]
            rows.append((100 * (b - w), p, w, r['trials']))
    for loss, p, w, n in sorted(rows, reverse=True):
        flag = 'under 5' if loss < 5 else ('over 30' if loss > 30 else 'ok')
        print(f"   {p:16} wins {w:5.0%}  loses {loss:5.1f} points (+-{100 * ci(w, n):.0f})  {flag}")


def section_luck(cells):
    r = cells.get(('mastery', 1.0))
    if r is None:
        return
    st, n = r['stats'], r['trials']
    print("\n3. NO DUMB LUCK (mastery): first deaths, share of all runs")
    ordinary = [f for f in range(1, 100) if f not in GATES]
    worst = sorted(((st.get(f, {}).get('first_deaths', 0) / n, f) for f in ordinary), reverse=True)[:5]
    per = sum(st.get(f, {}).get('first_deaths', 0) for f in ordinary) / n / len(ordinary)
    deep = sum(st.get(f, {}).get('first_deaths', 0) for f in range(90, 100)) / n
    print(f"   ordinary floors: {per:.2%} a floor on average (target under 0.05%); worst "
          + ', '.join(f"F{f} {v:.0%}" for v, f in worst if v > 0))
    print(f"   floors 90-99 together: {deep:.1%} (target under 1%)")
    gates = {}
    for kind, floor, lab, atks, dmg, died, turns, stale, cons in r['boss_rows']:
        if floor in GATES:
            e = gates.setdefault((floor, kind, lab), [0, 0])
            e[0] += 1
            e[1] += died
    print("   the gates, a fresh hero at full health (target with the quest 1-2%):")
    for (floor, kind, lab), (m, died) in sorted(gates.items()):
        print(f"     F{floor:<3} {kind:22} {lab:9} P(die) {died / max(1, m):5.0%}  (n {m})")
    gate_deaths = {f: st.get(f, {}).get('first_deaths', 0) / n for f in GATES}
    print("   first deaths on the gate floors in the runs: "
          + ', '.join(f"F{f} {v:.0%}" for f, v in gate_deaths.items()))


def section_deaths(cells):
    print("\n4. FIRST DEATHS by band (share of all runs) and the top killers")
    for key in sorted(cells):
        r = cells[key]
        st, n = r['stats'], r['trials']
        row = []
        for lo, hi in BANDS + [(f, f) for f in GATES]:
            d = sum(st.get(f, {}).get('first_deaths', 0) for f in range(lo, hi + 1))
            row.append(((f"{lo}-{hi}" if lo != hi else f"F{lo}"), d / n))
        row.sort(key=lambda x: int(x[0].lstrip('F').split('-')[0]))
        kills = Counter()
        for fs in st.values():
            for k, v in (fs.get('killers') or {}).items():
                kills[k] += v
        tot = sum(kills.values()) or 1
        print(f"   {name(key):22} " + ' '.join(f"{b}:{v:.0%}" for b, v in row if v > 0))
        print(f"   {'':22} killers: " + ', '.join(f"{k} {v / tot:.0%}" for k, v in kills.most_common(5)))


def section_pace(cells):
    print("\n5. PACE: per floor visited, by band (turns on the floor, newcomers met, starvation HP,"
          " hungry ticks, share of floors ending Heavy / Burdened, pounds carried)")
    for key in (('mastery', 1.0), ('mastery_dex', 1.0), ('committed', 1.0), ('casual', 1.0)):
        r = cells.get(key)
        if r is None:
            continue
        st = r['stats']
        print(f"   {name(key)}")
        print(f"   {'band':8} {'turns':>6} {'newc':>5} {'starveHP':>8} {'ticks':>6} {'heavy':>6} {'burd':>5} {'lb':>5}")
        for lo, hi in [(1, 1), (2, 4), (5, 9)] + BANDS[1:]:
            fl = [st[f] for f in range(lo, hi + 1) if f in st and st[f]['visits']]
            if not fl:
                continue
            v = sum(x['visits'] for x in fl)

            def m(k):
                return sum(x.get(k, 0) for x in fl) / v
            print(f"   {lo:>3}-{hi:<4} {m('turns'):6.0f} {m('newcomers'):5.2f} {m('starve'):8.1f} "
                  f"{m('starved'):6.2f} {m('load_heavy'):6.0%} {m('load_burdened'):5.0%} {m('carried_lb'):5.0f}")


def main(argv):
    d = argv[0]
    sect = argv[1] if len(argv) > 1 else 'taldp'
    cells = load(d)
    if not cells:
        print('no pickles in', d)
        return 1
    if 't' in sect:
        section_targets(cells)
    if 'a' in sect:
        section_ablation(cells)
    if 'l' in sect:
        section_luck(cells)
    if 'd' in sect:
        section_deaths(cells)
    if 'p' in sect:
        section_pace(cells)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
