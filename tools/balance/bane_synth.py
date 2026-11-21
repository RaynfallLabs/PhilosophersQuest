#!/usr/bin/env python
"""A synthetic bane overlay (2026-11-20), so the late-game sweep can run before
the lore research lands (_mm_2026_11_19/late/banes/BANE_SPEC.md).

The research will give deep kinds particular banes from their own myths in
place of the families' generic fire, cold and holy. This writes a STAND-IN of
that shape for tools/balance/sim_late.py's `overlay` knob: for the kinds that
peak at `from_floor` or deeper (no boss, mini-boss, seal demon, quest or
allied kind; spawning kinds only), a share `particular` of them (chosen by a
hash of the kind, so a kind converted at 0.5 is converted at 0.7 too) lose
their generic fire, cold and lightning weaknesses, and holy as well unless
`keep_holy` and the kind is a demon or one of the restless dead (the families
in `holy_families`; the frame of BANE_SPEC: holy stays a demon's weakness),
and take one or two particular banes in their place. The banes come from a
pool of `pool` substance ids per 20-floor domain (41-60, 61-80, 81-100), drawn
by a hash of the domain from SUBSTANCES (the game's silver, cold_iron, iron,
acid, poison and placeholder new ids bane_a, bane_b ...), and each kind's by a
hash of the kind (uniform, or Zipf-weighted with `zipf` > 0; a second bane
with share `two`). A bane the kind resists or shrugs off is taken off those
lists. Weapon forms (slash, pierce, blunt) and every other weakness stay.

It prints, per domain and spawn-weighted by `frequency` (variety_today.py's
reading): the share of kinds with any weakness, the top answer and its share,
and how many answers (greedy) cover 80% of the kinds with a weakness, before
and after. Deterministic: the same arguments write the same file.

    py tools/balance/bane_synth.py OUT.json [--from-floor 41] [--particular 1.0]
        [--pool 6] [--no-keep-holy] [--two 0.35] [--zipf 0] [--seed 0]
    then: --knobs overlay=OUT.json (difficulty_sim / balance_study)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))

GENERIC = ('fire', 'cold', 'lightning')
PLACEHOLDERS = tuple(f'bane_{c}' for c in 'abcdefghijkl')
SUBSTANCES = ('silver', 'cold_iron', 'iron', 'acid', 'poison') + PLACEHOLDERS
HOLY_FAMILIES = ('demons', 'restless_dead', 'ghosts', 'vampires_liches')
NAMED = ('is_boss', 'is_mini_boss', 'is_seal_demon', 'quest_only', 'unique', 'is_allied')
DOMAINS = ((21, 40), (41, 60), (61, 80), (81, 100))


def _h(*parts) -> float:
    """A fraction in [0, 1) from a hash of the parts (stable across runs)."""
    d = hashlib.sha256(':'.join(str(p) for p in parts).encode('utf-8')).digest()
    return int.from_bytes(d[:8], 'big') / float(1 << 64)


def load_defs() -> dict:
    with open(os.path.join(_REPO, 'data', 'monsters.json'), encoding='utf-8') as f:
        return json.load(f)


def peak(d) -> int:
    return int(d.get('peak_floor') or d.get('min_level') or 1)


def ordinary(d) -> bool:
    return (isinstance(d, dict) and not any(d.get(f) for f in NAMED)
            and float(d.get('peak_weight', 0) or 0) > 0)


def domain_of(pk: int) -> int:
    return (max(1, min(100, pk)) - 1) // 20


def domain_pool(dom: int, pool: int, seed, subs=SUBSTANCES) -> list:
    """The domain's `pool` substance ids: SUBSTANCES ordered by a hash of the
    domain, the first `pool` of them."""
    order = sorted(subs, key=lambda s: _h('pool', seed, dom, s))
    return order[:max(1, min(len(order), int(pool)))]


def _weighted_pick(cands: list, u: float, zipf: float) -> str:
    w = [1.0 / ((i + 1) ** zipf) if zipf > 0 else 1.0 for i in range(len(cands))]
    t = u * sum(w)
    acc = 0.0
    for c, x in zip(cands, w):
        acc += x
        if t < acc:
            return c
    return cands[-1]


def synth(defs: dict = None, from_floor: int = 41, particular: float = 1.0, pool: int = 6,
          keep_holy: bool = True, seed=0, two: float = 0.35, zipf: float = 0.0,
          subs=SUBSTANCES, holy_families=HOLY_FAMILIES) -> dict:
    """The overlay {kind: {weaknesses, resistances, shrugs_off}, '_meta': ...}."""
    defs = load_defs() if defs is None else defs
    out = {}
    used = set()
    for kind in sorted(defs):
        d = defs[kind]
        if not ordinary(d) or peak(d) < from_floor:
            continue
        if _h('convert', seed, kind) >= particular:
            continue
        dom = domain_of(peak(d))
        cands = domain_pool(dom, pool, seed, subs)
        keep_h = keep_holy and str(d.get('family', '')) in holy_families
        weak = [w for w in (d.get('weaknesses') or ())
                if w not in GENERIC and not (w == 'holy' and not keep_h)]
        n = 2 if _h('two', seed, kind) < two else 1
        banes = []
        for i in range(n):
            left = [c for c in cands if c not in banes]
            if not left:
                break
            banes.append(_weighted_pick(left, _h('bane', seed, kind, i), zipf))
        for b in banes:
            if b not in weak:
                weak.append(b)
        used |= set(b for b in banes if b in PLACEHOLDERS)
        out[kind] = dict(weaknesses=weak,
                         resistances=[r for r in (d.get('resistances') or ()) if r not in banes],
                         shrugs_off=[r for r in (d.get('shrugs_off') or ()) if r not in banes])
    meta = dict(tool='tools/balance/bane_synth.py', from_floor=from_floor, particular=particular,
                pool=pool, keep_holy=keep_holy, seed=seed, two=two, zipf=zipf,
                holy_families=list(holy_families), new_substances=sorted(used),
                pools={f'{lo}-{hi}': domain_pool(domain_of(lo), pool, seed, subs)
                       for lo, hi in DOMAINS if hi >= from_floor},
                kinds=len(out))
    return dict(out, _meta=meta)


def apply(defs: dict, overlay: dict) -> dict:
    out = dict(defs)
    for k, v in overlay.items():
        if not k.startswith('_'):
            out[k] = dict(defs[k], **v)
    return out


def concentration(defs: dict, lo: int, hi: int) -> dict:
    """Spawn-weighted (frequency) answers of a domain's ordinary kinds."""
    ks = [(k, d) for k, d in defs.items() if ordinary(d) and lo <= peak(d) <= hi]
    if not ks:
        return {}
    fw = {k: float(d.get('frequency', 1) or 1) for k, d in ks}
    tot = sum(fw.values())
    weak = {k: set(d.get('weaknesses') or ()) for k, d in ks}
    share = {}
    for k, ws in weak.items():
        for x in ws:
            share[x] = share.get(x, 0.0) + fw[k]
    withw = [k for k in weak if weak[k]]
    wtot = sum(fw[k] for k in withw)
    left, picks = list(withw), []
    while left and (wtot - sum(fw[k] for k in left)) < 0.8 * wtot - 1e-9:
        c = {}
        for k in left:
            for x in weak[k]:
                c[x] = c.get(x, 0.0) + fw[k]
        best = max(sorted(c), key=lambda x: c[x])
        picks.append(best)
        left = [k for k in left if best not in weak[k]]
    top = sorted(share.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    return dict(kinds=len(ks), weak_any=100.0 * wtot / tot,
                top=[(x, 100.0 * v / tot) for x, v in top], cover80=picks)


def report(before: dict, after: dict, from_floor: int, out=sys.stdout) -> None:
    w = out.write
    w("domain   kinds  any weakness %    top answers (spawn-weighted share of the domain)"
      "             answers to cover 80%\n")
    for lo, hi in DOMAINS:
        if hi < from_floor:
            continue
        for tag, defs in (('now', before), ('synth', after)):
            c = concentration(defs, lo, hi)
            if not c:
                continue
            top = ', '.join(f"{x} {v:.0f}%" for x, v in c['top'])
            w(f"{lo:>3}-{hi:<3} {tag:<5} {c['kinds']:>4}  {c['weak_any']:6.0f}           {top:<52} "
              f"{len(c['cover80'])} ({', '.join(c['cover80'])})\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='A synthetic bane overlay for sim_late.')
    ap.add_argument('out')
    ap.add_argument('--from-floor', type=int, default=41)
    ap.add_argument('--particular', type=float, default=1.0)
    ap.add_argument('--pool', type=int, default=6)
    ap.add_argument('--no-keep-holy', action='store_true')
    ap.add_argument('--two', type=float, default=0.35)
    ap.add_argument('--zipf', type=float, default=0.0)
    ap.add_argument('--seed', default='0')
    ap.add_argument('--subs', default='', help='comma list in place of SUBSTANCES')
    ap.add_argument('--holy-families', default=','.join(HOLY_FAMILIES))
    a = ap.parse_args(argv)
    subs = tuple(s for s in a.subs.split(',') if s) or SUBSTANCES
    defs = load_defs()
    ov = synth(defs, a.from_floor, a.particular, a.pool, not a.no_keep_holy, a.seed, a.two,
               a.zipf, subs, tuple(s for s in a.holy_families.split(',') if s))
    report(defs, apply(defs, ov), a.from_floor)
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(ov, f, indent=1, sort_keys=True)
    print(f"{ov['_meta']['kinds']} kinds -> {a.out}; pools: {ov['_meta']['pools']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
