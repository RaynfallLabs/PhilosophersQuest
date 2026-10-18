#!/usr/bin/env python
"""Karma-budget Monte Carlo (DEEDS_KARMA_DESIGN.md sections 3.5 and 8.2).

Question it answers: with the karma gate ON (one +1 slot per 10-floor block,
kept oaths fill the earliest open block, constancy capped at +2), how often
does each kind of player end a run at the Sword of Michael (karma 8 or more)?

What is REAL and what is MODELLED
---------------------------------
REAL: the shipped encounter data (data/npc_encounters.json,
data/flavor_encounters.json and the hardcoded list, after
encounter_schema.normalise), every option's karma, karma_kind, quiz, naive,
side, villain, oath and requires; the visibility rule
(encounter_schema.visible_options, so hidden follow-ups such as Silas's
judgment appear only after the pass that reveals them); the deeds register
(deeds.py) and the single karma entry point (karma.adjust) with the gate
switched on for the simulation only, so block slots, the oath rule and the
constancy rules (temperance, faithful, discerning, steadfast) are the game's.

MODELLED (named constants below):
  * The Road (5.2, with the editor round's decision in
    ENCOUNTER_STORIES_DRAFT Part I): each block binds one anchor among its
    candidates, MEDIUM_SLOTS medium story encounters (two in odd bands, one in
    even) and, in even bands, one high one, drawn without repeats from the
    pools whose band overlaps the block. Callback-only content is placed
    only through oaths (below). Setne's Tomb is its own roll
    (data/setne_tomb.json). Light encounters give no karma and are skipped.
  * A quiz is answered by the style's ACCURACY per question; threshold modes
    stop at the first wrong answer (zero tolerance), play_all plays every
    round, chain modes pass at pass_at.
  * An oath sworn is kept with the style's KEEP chance a few floors later
    (its due_floors, else 3-12), broken with BREAK (-1 betray), or lapses.
  * Untyped (legacy) karma, which only today's pre-schema content carries,
    is mapped: a positive point in a quiz pass to 'judgment', any other
    positive to 'forgo', a negative to 'cruelty'. The report counts them.

    py tools/balance/karma_sim.py                 # 4000 runs per style
    py tools/balance/karma_sim.py --n 500 --seed 3 --json

The test (tests/test_karma_budget_sim.py) runs it small and asserts only that
it runs and reports; the section 8.2 bands are asserted from Phase 3b, once
the converted content ships.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'src')
for _p in (SRC, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SWORD_AT = 8
MEDIUM_SLOTS = {True: 2, False: 1}      # odd band -> 2, even -> 1
DEFAULT_OATH_SPAN = (3, 12)
STEPS_PER_ENCOUNTER = 3                 # 'then: options' follow-ups
STATS = {'STR': 12, 'CON': 12, 'DEX': 12, 'INT': 12, 'WIS': 12, 'PER': 12}

# Player styles (3.5, redefined so the Pragmatist and the Inconsistent differ).
STYLES = {
    'saint':        {'principled': 0.80, 'accuracy': 0.70, 'keep': 0.85, 'break': 0.00},
    'pragmatist':   {'greedy': 0.70, 'accuracy': 0.60, 'keep': 0.40, 'break': 0.30},
    'naive_helper': {'naive': 0.90, 'examine': 0.15, 'accuracy': 0.60, 'keep': 0.75,
                     'break': 0.05},
    'villain':      {'cruel': 0.75, 'accuracy': 0.50, 'keep': 0.10, 'break': 0.60},
    'inconsistent': {'accuracy': 0.60, 'keep': 0.50, 'break': 0.20},
}


# ------------------------------------------------------------------ content

def load_content(encounters=None) -> dict:
    """The pools the Road draws from, per block, from the shipped data (or
    the ``[(source, enc)]`` given)."""
    if encounters is None:
        from tools.encounters.validate import load_all
        encounters = load_all()
    encs = list(encounters)
    by_tag = {e.get('tag'): e for _s, e in encs}
    try:
        with open(os.path.join(ROOT, 'data', 'setne_tomb.json'), encoding='utf-8') as f:
            st = json.load(f)
        lo, hi = st.get('floors', [45, 65])
        setne = {'tag': st.get('encounter'),
                 'floors': [x for x in range(int(lo), int(hi) + 1) if x not in (20, 40, 60, 80)]}
    except (OSError, ValueError):
        setne = {'tag': None, 'floors': []}
    blocks = {}
    for b in range(1, 11):
        lo, hi = 10 * b - 9, 10 * b
        def overl(e):
            band = e.get('band') or [0, 0]
            return int(band[0]) <= hi and int(band[1]) >= lo
        blocks[b] = {
            'anchors': [e for s, e in encs if s == 'npc' and e.get('block') == b],
            'medium': [e for s, e in encs if s != 'npc' and not e.get('callback_only')
                       and e.get('stakes') == 'medium' and overl(e)],
            'high': [e for s, e in encs if s != 'npc' and not e.get('callback_only')
                     and e.get('stakes') == 'high' and overl(e)],
        }
    untyped = sum(1 for _s, e in encs for o in e.get('options') or ()
                  for br in _branches(o)
                  if int(br.get('karma', 0) or 0) and not br.get('karma_kind'))
    return {'blocks': blocks, 'by_tag': by_tag, 'setne': setne, 'untyped': untyped}


def _branches(o):
    from encounter_schema import option_branches
    return option_branches(o)


# ------------------------------------------------------------------ one run

class _Sim:
    def __init__(self, content, style: dict, rng: random.Random, table: dict):
        import deeds
        self.c = content
        self.s = style
        self.rng = rng
        self.table = table
        self.g = SimpleNamespace(karma=0, dungeon_level=1, turn_count=0,
                                 player=SimpleNamespace(deepest_floor_reached=1),
                                 _deeds=deeds.new_register())
        self.pending = []          # (floor, oath_id)
        self.karma_at_30 = None

    # -- helpers
    def at(self, floor: int):
        self.g.dungeon_level = floor
        self.g.player.deepest_floor_reached = max(self.g.player.deepest_floor_reached, floor)

    def ctx(self):
        f = self.g.dungeon_level
        return {'reg': self.g._deeds, 'karma': self.g.karma, 'stats': STATS, 'floor': f,
                'deepest': self.g.player.deepest_floor_reached, 'items': set()}

    def quiz_passes(self, q: dict) -> bool:
        acc = self.s['accuracy']
        mode = q.get('mode', 'threshold')
        thr = int(q.get('threshold', 1) or 1)
        total = int(q.get('total_qs', thr) or thr)
        if mode in ('chain', 'escalator_chain'):
            need = int(q.get('pass_at', 1) or 1)
            return all(self.rng.random() < acc for _ in range(need))
        if q.get('play_all'):
            return sum(self.rng.random() < acc for _ in range(total)) >= thr
        return all(self.rng.random() < acc for _ in range(thr))

    # -- choosing
    def classify(self, o):
        from encounter_schema import is_quiz, max_karma
        brs = _branches(o)
        good = max_karma(o) > 0 or any(isinstance(b.get('oath'), dict) for b in brs)
        bad = o.get('villain') or o.get('side') == 'wrong' or \
            any(int(b.get('karma', 0) or 0) < 0 for b in brs)
        from tools.encounters.validate import option_value
        return {'good': good, 'bad': bool(bad), 'naive': bool(o.get('naive')),
                'quiz': is_quiz(o), 'value': option_value(o, self.table),
                'low': min((int(b.get('karma', 0) or 0) for b in brs), default=0)}

    def choose(self, visible, name: str):
        rng = self.rng
        opts = [(i, o, self.classify(o)) for i, o in visible]
        def pick(cands):
            return rng.choice(cands) if cands else None
        if name == 'saint':
            if rng.random() < self.s['principled']:
                c = pick([x for x in opts if x[2]['good'] and not x[2]['bad']])
                if c:
                    return c
            return pick([x for x in opts if not x[2]['bad'] and not x[2]['naive']]) or pick(opts)
        if name == 'pragmatist':
            if rng.random() < self.s['greedy']:
                best = max(x[2]['value'] for x in opts)
                if best > 0:
                    return pick([x for x in opts if x[2]['value'] == best])
            return pick([x for x in opts if x[2]['quiz']] if rng.random() < 0.5 else opts) or pick(opts)
        if name == 'naive_helper':
            if rng.random() < self.s['naive']:
                c = pick([x for x in opts if x[2]['naive']])
                if c:
                    return c
            if rng.random() < self.s['examine']:
                c = pick([x for x in opts if x[2]['quiz']])
                if c:
                    return c
            return pick([x for x in opts if not x[2]['quiz'] and not x[2]['bad']]) or pick(opts)
        if name == 'villain':
            if rng.random() < self.s['cruel']:
                worst = min(x[2]['low'] for x in opts)
                if worst < 0:
                    return pick([x for x in opts if x[2]['low'] == worst])
            return pick(opts)
        return pick(opts)

    # -- applying
    def apply_branch(self, enc, o, b, *, passed: bool):
        import deeds
        import karma
        from encounter_schema import has_naive_sibling
        reg = self.g._deeds
        floor, deepest, block, turn = deeds.where(self.g)
        tag = enc.get('tag', 'enc')
        k = int(b.get('karma', 0) or 0)
        kind = b.get('karma_kind')
        if k and not kind:
            kind = ('judgment' if passed else 'forgo') if k > 0 else 'cruelty'
        if passed and has_naive_sibling(enc, o):
            deeds.record(reg, f'flag.judged.{deeds.slug(tag)}', floor=floor, block=block,
                         tags=['virtue:judged'], engine=True, deepest=deepest)
        if passed and enc.get('stakes') == 'high':
            deeds.record(reg, f'flag.steadfast.{deeds.slug(tag)}', floor=floor, block=block,
                         tags=['virtue:steadfast'], engine=True, deepest=deepest)
        if b.get('virtue') == 'forgo' or (kind == 'forgo' and k > 0):
            deeds.record(reg, f'flag.forgo.{deeds.slug(tag)}', floor=floor, block=block,
                         tags=['virtue:forgo'], engine=True, deepest=deepest)
        if k:
            karma.adjust(self.g, k, kind=kind, source=tag)
        for d in b.get('deeds') or ():
            did = d if isinstance(d, str) else (d or {}).get('id')
            if deeds.valid_id(did):
                try:
                    deeds.record(reg, did, floor=floor, block=block, source=tag, deepest=deepest)
                except ValueError:
                    pass
        oath = b.get('oath')
        if isinstance(oath, dict) and oath.get('id'):
            deeds.swear(reg, oath['id'], to=oath.get('to', ''), what='', floor=floor,
                        block=block, source=tag)
            r = self.rng.random()
            if r < self.s['keep']:
                span = oath.get('due_floors') or DEFAULT_OATH_SPAN
                self.pending.append((min(98, deepest + self.rng.randint(int(span[0]), int(span[1]))),
                                     oath['id'], 'keep'))
            elif r < self.s['keep'] + self.s['break']:
                self.pending.append((min(98, deepest + self.rng.randint(*DEFAULT_OATH_SPAN)),
                                     oath['id'], 'break'))
            else:
                self.pending.append((min(98, deepest + self.rng.randint(*DEFAULT_OATH_SPAN)),
                                     oath['id'], 'lapse'))
        return b.get('then') == 'options'

    def meet(self, enc, name: str):
        from encounter_schema import is_quiz, visible_options
        used = []
        for _step in range(STEPS_PER_ENCOUNTER):
            vis = visible_options(enc, self.ctx(), used)
            if not vis:
                return
            choice = self.choose(vis, name)
            if choice is None:
                return
            idx, o, _cls = choice
            used.append(idx)
            if is_quiz(o):
                passed = self.quiz_passes(o['quiz'])
                b = o.get('pass' if passed else 'fail') or {}
            else:
                passed, b = False, o
            if not self.apply_branch(enc, o, b, passed=passed):
                return

    def settle_oaths(self, upto: int):
        import deeds
        import karma
        due = sorted([p for p in self.pending if p[0] <= upto])
        self.pending = [p for p in self.pending if p[0] > upto]
        for floor, oid, how in due:
            self.at(floor)
            reg = self.g._deeds
            f, d, block, turn = deeds.where(self.g)
            o = reg['oaths'].get(oid) or {}
            if how == 'keep' and deeds.keep_oath(reg, oid, floor=f, block=block):
                karma.adjust(self.g, 1, kind='oath', source=oid, made_block=o.get('made_block'))
            elif how == 'break' and deeds.break_oath(reg, oid, floor=f, block=block):
                karma.adjust(self.g, -1, kind='betray', source=oid)
            else:
                deeds.lapse_oath(reg, oid, floor=f, block=block)

    def run(self, name: str):
        rng = self.rng
        used = set()
        setne = self.c['setne']
        setne_floor = rng.choice(setne['floors']) if setne['floors'] else None
        for b in range(1, 11):
            lo, hi = 10 * b - 9, min(98, 10 * b)
            pools = self.c['blocks'][b]
            events = []
            if pools['anchors']:
                events.append(rng.choice(pools['anchors']))
            for stake, n in (('medium', MEDIUM_SLOTS[b % 2 == 1]), ('high', 1 if b % 2 == 0 else 0)):
                cands = [e for e in pools[stake] if e.get('tag') not in used]
                rng.shuffle(cands)
                events.extend(cands[:n])
            if setne_floor is not None and lo <= setne_floor <= hi:
                enc = self.c['by_tag'].get(setne['tag'])
                if enc is not None:
                    events.append(enc)
            placed = sorted(((rng.randint(lo, hi), i, e) for i, e in enumerate(events)),
                            key=lambda t: (t[0], t[1]))
            for floor, _i, enc in placed:
                self.settle_oaths(floor)
                if floor > 30 and self.karma_at_30 is None:
                    self.karma_at_30 = self.g.karma
                self.at(floor)
                used.add(enc.get('tag'))
                self.meet(enc, name)
            self.settle_oaths(hi)
            if hi >= 30 and self.karma_at_30 is None:
                self.karma_at_30 = self.g.karma
        self.settle_oaths(99)
        return self.g.karma, self.karma_at_30 if self.karma_at_30 is not None else self.g.karma


# ------------------------------------------------------------------ driver

def _pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return 0
    return xs[min(len(xs) - 1, int(q * (len(xs) - 1) + 0.5))]


def oracle_max(content) -> int:
    """The most karma the data could ever give before clamping: one slot per
    block that has any +1 path, plus the constancy cap (8.2: at most 12)."""
    from tools.encounters.validate import has_plus_one_path
    import karma
    cap = int(karma.rules().get('constancy_cap', 2))
    blocks = sum(1 for b, p in content['blocks'].items()
                 if any(has_plus_one_path(e) for e in p['anchors'] + p['medium'] + p['high']))
    return blocks + cap


def run(n: int = 4000, seed: int = 1, encounters=None, styles=None) -> dict:
    """Simulate ``n`` runs per style with the gate on; return the report."""
    import karma
    from tools.encounters.validate import _rules
    content = load_content(encounters)
    table = _rules().get('reward_value', {})
    saved = karma._RULES
    karma._RULES = dict(karma.rules(), gate_enabled=True)
    try:
        report = {'n': n, 'seed': seed, 'untyped_karma_options': content['untyped'],
                  'oracle_max': oracle_max(content), 'styles': {}}
        for i, name in enumerate(styles or STYLES):
            rng = random.Random((seed * 1000003) ^ (i * 7919))
            finals, at30 = [], []
            for _ in range(n):
                k, k30 = _Sim(content, STYLES[name], rng, table).run(name)
                finals.append(k)
                at30.append(k30)
            report['styles'][name] = {
                'mean': round(sum(finals) / n, 2),
                'p10': _pct(finals, 0.1), 'p50': _pct(finals, 0.5), 'p90': _pct(finals, 0.9),
                'sword': round(sum(k >= SWORD_AT for k in finals) / n, 4),
                'scales': round(sum(1 <= k < SWORD_AT for k in finals) / n, 4),
                'silence': round(sum(k == 0 for k in finals) / n, 4),
                'below_zero': round(sum(k < 0 for k in finals) / n, 4),
                'below_zero_at_30': round(sum(k < 0 for k in at30) / n, 4),
            }
    finally:
        karma._RULES = saved
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--n', type=int, default=4000)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    rep = run(args.n, args.seed)
    if args.json:
        print(json.dumps(rep, indent=2))
        return 0
    print(f"karma_sim: {rep['n']} runs per style, seed {rep['seed']}, gate ON (simulated)")
    print(f"oracle max before clamping: {rep['oracle_max']} (must be <= 12)")
    if rep['untyped_karma_options']:
        print(f"note: {rep['untyped_karma_options']} option branches carry untyped (legacy) karma; "
              'mapped to judgment / forgo / cruelty')
    print(f"{'style':<14}{'mean':>6}{'p10':>5}{'p50':>5}{'p90':>5}{'Sword':>8}{'Scales':>8}"
          f"{'<0':>7}{'<0@30':>7}")
    for name, r in rep['styles'].items():
        print(f"{name:<14}{r['mean']:>6.1f}{r['p10']:>5}{r['p50']:>5}{r['p90']:>5}"
              f"{r['sword']:>8.1%}{r['scales']:>8.1%}{r['below_zero']:>7.1%}"
              f"{r['below_zero_at_30']:>7.1%}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
