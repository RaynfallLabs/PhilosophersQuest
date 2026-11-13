"""Maths grade curve: audit the bank against its tier bands, then fix it.

Slice 9 of the winning-build plan (2026-11-13). Every maths question gets
a school-grade score (tools/balance/math_difficulty.py) and every tier a
band (tools/balance/math_grade_curve.json): T1 grades 1-2, T2 3-4, T3 4-5,
T4 6-7, T5 7-8. This tool:

1. scores the bank and flags every question outside its tier's band
   (too easy, too hard, trivial, or the same stem in two tiers);
2. MOVES an out-of-band question to the tier whose band fits it, when its
   topic has a grade band there and that tier has room (no tier grows
   by more than CAP_GROWTH of its size today);
3. otherwise REPLACES it, in place, with a new in-band question of the
   same topic (a tier's fill topics when the topic has no band there);
4. tops a tier that lost questions back up to its size today with new
   in-band questions of the topics that left (BACKFILL).

Everything is deterministic: same bank in, same bank out, and a curved
bank comes back unchanged (idempotent). New questions come from the
generators below, each checked by the shared scorer, and none repeats a
stem anywhere in the bank or spells out a sum from its topic's card.

Why a transform and not a rebuild: the shipped bank is no longer what
build_math_bank_v3.py produces (three bug bashes fixed the JSON by hand,
and the generator's random draws have shifted since), so a rebuild would
churn about 500 questions that are fine. build_math_bank_v3.py runs this
same curve after its own build, so a from-scratch rebuild is curved too.

    py -m tools.balance.math_grade_curve             # curve data/questions/math.json
    py -m tools.balance.math_grade_curve --dry-run   # report only
    py -m tools.balance.math_grade_curve --audit     # list what is out of band
    py -m tools.balance.math_grade_curve --doc       # print the docs band table
"""
from __future__ import annotations

import json
import math
import random
import re
import statistics
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

try:
    from tools.balance import math_difficulty as md
    from tools.balance.math_topics import topic_for_context
except ImportError:                                    # run as a plain script
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from tools.balance import math_difficulty as md
    from tools.balance.math_topics import topic_for_context

ROOT = Path(__file__).resolve().parent.parent.parent
MATH_BANK = ROOT / 'data' / 'questions' / 'math.json'
MATH_CARDS = ROOT / 'data' / 'question_contexts' / 'math.json'

SEED = 20261113
CAP_GROWTH = 0.08          # a tier may grow by at most 8% (the test allows 10%)
# The tier sizes before the curve (v3.4.0). A rebuild from scratch is held
# to these, since its raw draw has a slightly different mix.
TIER_SIZES = {1: 488, 2: 560, 3: 422, 4: 495, 5: 450}
EDGE = 0.05                # new questions sit at least this far below a band's top


# ---------------------------------------------------------------------------
# Building one question
# ---------------------------------------------------------------------------

def _fmt(v) -> str:
    if isinstance(v, Fraction):
        if v.denominator == 1:
            return str(v.numerator)
        return f'{v.numerator}/{v.denominator}'
    return str(v)


def _int_wrongs(ans: int, rng: random.Random, errors=()) -> list[str]:
    """Three plausible wrong whole numbers: up to two named slips (a lost
    carry, a sign flip ...) and near misses for the rest."""
    signed_ok = ans < 0
    picks: list[int] = []
    for e in errors:
        if e != ans and e not in picks and (signed_ok or e >= 0) and len(picks) < 2:
            picks.append(e)
    near = [ans + d for d in (1, -1, 2, -2, 10, -10, 5, -5)]
    if abs(ans) >= 10:
        rev = int(str(abs(ans))[::-1])
        near.append(rev if ans >= 0 else -rev)
    if ans < 0:
        near.append(-ans)
    near = [n for n in dict.fromkeys(near) if n != ans and n not in picks and (signed_ok or n >= 0)]
    rng.shuffle(near)
    for n in near:
        if len(picks) == 3:
            break
        picks.append(n)
    return [str(p) for p in picks]


class Pool:
    """Candidate questions for one (topic, tier) slice."""

    def __init__(self, topic: str, tier: int):
        self.topic, self.tier = topic, tier
        self.rng = random.Random(f'{SEED}:{topic}:{tier}')
        self.items: list[dict] = []
        self._stems: set[str] = set()

    def add(self, stem: str, answer, wrongs, context: str):
        if stem in self._stems:
            return
        answer = _fmt(answer)
        wrongs = [_fmt(w) for w in wrongs]
        choices = [answer] + [w for w in dict.fromkeys(wrongs) if w != answer][:3]
        if len(choices) != 4:
            return
        self.rng.shuffle(choices)
        topic = topic_for_context(context)
        if topic != self.topic:
            raise ValueError(f'tip {context!r} files under {topic!r}, not {self.topic!r}')
        q = {'tier': self.tier, 'question': stem, 'answer': answer,
             'choices': choices, 'context': context, 'topic': topic}
        bad = md.check_answer(q)
        if bad:
            raise ValueError(f'generator built a wrong question {stem!r}: {bad}')
        r = md.rate(q)
        lo, hi = md.tier_band(self.tier)
        if not (lo <= r.score < hi - EDGE) or r.trivial:
            return
        self._stems.add(stem)
        self.items.append(q)

    def add_int(self, stem: str, ans: int, context: str, errors=()):
        self.add(stem, ans, _int_wrongs(ans, self.rng, errors), context)


# ---------------------------------------------------------------------------
# Generators: one per (topic, tier) slice that may need new questions.
# Each draws from a fixed range in a fixed order, so the pools are the
# same on every run.
# ---------------------------------------------------------------------------

def _g_tens_t1(p: Pool):
    for a in range(11, 90):
        if a % 10 == 0:
            continue
        for b in (10, 20, 30, 40, 50):
            if a + b < 100:
                p.add_int(f'{a} + {b} = ?', a + b, 'Add multiples of 10.', (a + b - 10, a + b + 10))
            if a > b:
                p.add_int(f'{a} - {b} = ?', a - b, 'Subtract multiples of 10.', (a - b + 10, a - b - 10))


def _g_double_t1(p: Pool):
    for n in range(11, 45):
        if n % 10 <= 4:
            p.add_int(f'Double {n}?', 2 * n, 'Doubling a 2-digit — double tens, double ones.', (2 * n + 10, n + 2))
    for n in range(22, 90, 2):
        if (n // 10) % 2 == 0:
            p.add_int(f'Half of {n}?', n // 2, 'Halving — split into tens and ones.', (n // 2 + 5, n // 2 - 5))


def _g_times_t2(p: Pool):
    for d in range(2, 10):
        for m in range(20, 100, 10):
            ans = d * m
            p.add_int(f'{d} × {m} = ?', ans, 'Times-table fact, then add the zero.',
                      (ans + m, ans - m, d * (m // 10)))
            p.add_int(f'{m} × {d} = ?', ans, 'Times-table fact, then add the zero.',
                      (ans + d * 10, ans - d * 10))


def _g_division_t2(p: Pool):
    for d in range(2, 10):
        for q in range(20, 100, 10):
            n = d * q
            p.add_int(f'{n} ÷ {d} = ?', q,
                      'Division = inverse of multiplication: drop the zero, divide, put it back.',
                      (q // 10, q + 10, q - 10))


def _g_tens_t2(p: Pool):
    rng = random.Random(f'{SEED}:tens2')
    starts = list(range(103, 900))
    rng.shuffle(starts)
    for a in starts:
        if a % 10 == 0:
            continue
        for b in (20, 30, 40, 50, 60, 70, 80, 90):
            if (a // 10) % 10 + b // 10 >= 10 and a + b < 1000:
                p.add_int(f'{a} + {b} = ?', a + b, 'Add multiples of 10.', (a + b - 100, a + b + 10))
            if (a // 10) % 10 < b // 10 and a > b:
                p.add_int(f'{a} - {b} = ?', a - b, 'Subtract multiples of 10.', (a - b + 100, a - b - 10))
        if len(p.items) > 400:
            break


def _g_double_t2(p: Pool):
    for n in range(51, 100):
        p.add_int(f'Double {n}?', 2 * n, 'Doubling a 2-digit — double tens, double ones.', (2 * n - 10, 2 * n + 10))
    for n in range(101, 500):
        if n % 10:
            p.add_int(f'Double {n}?', 2 * n, 'Doubling — double hundreds, tens and ones, then combine.',
                      (2 * n - 10, 2 * n + 100))
    for n in range(102, 1000, 2):
        p.add_int(f'Half of {n}?', n // 2, 'Halving — split into hundreds, tens and ones.',
                  (n // 2 + 5, n // 2 - 5, n // 2 + 50))


def _g_twodigit_t2(p: Pool):
    for a in range(15, 90):
        for b in range(15, 90):
            if (a % 10) + (b % 10) >= 10 and (a + b) % 7 == 0:
                p.add_int(f'{a} + {b} = ?', a + b, 'Add tens, add ones (with carry), combine.', (a + b - 10, a + b + 10))
            if a - b >= 15 and (a % 10) < (b % 10) and (a + 2 * b) % 7 == 0:
                p.add_int(f'{a} - {b} = ?', a - b, 'Subtract with borrow: unwrap a ten.', (a - b + 10, a - b - 10))


def _g_twodigit_t3(p: Pool):
    rng = random.Random(f'{SEED}:add3')
    pairs = [(a, b) for a in range(112, 900, 7) for b in range(17, 99, 3)]
    rng.shuffle(pairs)
    for a, b in pairs:
        if add_carries_ok(a, b):
            p.add_int(f'{a} + {b} = ?', a + b, 'Add tens, add ones (with carry), then the hundreds.',
                      (a + b - 10, a + b - 100, a + b + 10))
        if a - b > 99 and md.sub_borrows(a, b) >= 2:
            p.add_int(f'{a} - {b} = ?', a - b, 'Subtract with borrow: unwrap a ten (or a hundred).',
                      (a - b + 10, a - b + 100, a - b - 10))
        if len(p.items) > 500:
            break


def add_carries_ok(a: int, b: int) -> bool:
    return md.add_carries(a, b) >= 2 and a + b < 1000


def _g_parts_t3(p: Pool):
    for a in range(13, 100):
        if a % 10 == 0:
            continue
        for b in range(2, 10):
            ans = a * b
            p.add_int(f'{a} × {b} = ?', ans, 'Multiply by parts: tens×b + ones×b.',
                      (ans + b, ans - 10, (a // 10) * 10 * b + (a % 10)))
    for a in range(13, 50):
        if a % 10 == 0:
            continue
        for b in (20, 30, 40):
            ans = a * b
            p.add_int(f'{a} × {b} = ?', ans, 'Multiply by parts: tens×b + ones×b.', (ans + b, ans - 100, a * (b // 10)))


def _g_fraction_of_t3(p: Pool):
    for q in (2, 3, 4, 5, 6, 8, 10):
        for pnum in range(1, q):
            if math.gcd(pnum, q) != 1:
                continue
            for n in range(q * 3, q * 25, q):
                ans = n // q * pnum
                p.add_int(f'{pnum}/{q} of {n}?', ans, 'Fraction of qty: divide by q, times p.',
                          (n // q, ans + n // q))


def _g_squares_t3(p: Pool):
    for b in (20, 30, 40, 50, 60, 70, 80, 90):
        p.add_int(f'{b}² = ?', b * b, 'Squares 1-15 — memorize; then add two zeros.', (b * b // 10, b * 2, b * b + 100))
        p.add_int(f'{b} squared = ?', b * b, 'Squares 1-15 — memorize; then add two zeros.', (b * b * 10, b * 2))
    for k in range(4, 7):
        p.add_int(f'10^{k} = ?', 10 ** k, 'Powers of 10 — count the zeros.', (10 ** (k - 1), 10 ** (k + 1), 10 * k))


def _g_divis_t3(p: Pool):
    pool = [3, 4, 6, 7, 8, 9, 11, 12]
    for n in range(24, 100):
        divs = [d for d in pool if n % d == 0]
        non = [d for d in pool if n % d]
        if len(divs) == 1 and len(non) >= 3:
            d = divs[0]
            p.add(f'Which number divides {n} evenly?', d, p.rng.sample(non, 3),
                  f'Try each divisibility rule ({d} divides {n}).')


def _g_fraction_of_t4(p: Pool):
    for q2 in (2, 3, 4, 5, 6):
        for p2 in range(1, q2):
            for q1 in (2, 3, 4, 5):
                for p1 in range(1, q1):
                    if math.gcd(p1, q1) != 1 or math.gcd(p2, q2) != 1:
                        continue
                    for n in (60, 72, 84, 90, 96, 120, 144, 150, 180, 240, 300, 360):
                        first = Fraction(p2, q2) * n
                        if first.denominator != 1:
                            continue
                        ans = Fraction(p1, q1) * first
                        if ans.denominator != 1:
                            continue
                        p.add_int(f'{p1}/{q1} of {p2}/{q2} of {n} = ?', int(ans),
                                  'Multiply the fractions first, then × the whole.',
                                  (int(first), int(ans) * 2))
    for q in (6, 7, 8, 9, 12):
        for pnum in range(2, q):
            if math.gcd(pnum, q) != 1:
                continue
            for n in range(q * 11, q * 30, q):
                ans = n // q * pnum
                p.add_int(f'{pnum}/{q} of {n}?', ans, 'Fraction of qty: divide by q, times p.', (n // q, ans + n // q))


def _g_percent_t4(p: Pool):
    for pct in (15, 30, 35, 40, 45, 60, 65, 70, 80, 85, 90, 12, 8, 4, 36):
        for n in range(120, 1000, 20):
            ans = Fraction(pct * n, 100)
            if ans.denominator == 1:
                tip = f'{pct}% shortcut — decompose or use 10% × k.'
                p.add_int(f'{pct}% of {n}?', int(ans), tip, (int(ans) + n // 10, int(ans) - n // 20))


def _g_negatives_t4(p: Pool):
    for a in range(2, 40):
        for b in range(2, 40):
            if a == b:
                continue
            p.add_int(f'-{a} + {b} = ?', b - a, 'Negative arithmetic — track the sign.', (a - b, a + b))
            if a < b:
                p.add_int(f'{a} - {b} = ?', a - b, 'Negative arithmetic — track the sign.', (b - a, -(a + b)))
            p.add_int(f'-{a} - {b} = ?', -a - b, 'Negative arithmetic — track the sign.', (a + b, b - a))
    for a in range(2, 13):
        for b in range(2, 16):
            p.add_int(f'-{a} × {b} = ?', -a * b, 'Sign rule: same → +, different → -.', (a * b, -a * b - a))
            p.add_int(f'-{a} × -{b} = ?', a * b, 'Sign rule: same → +, different → -.', (-a * b, a * b + a))


def _g_onestep_t4(p: Pool):
    for k in range(3, 10):
        for x in range(12, 30):
            p.add_int(f'Solve: {k}x = {k * x}', x, 'One-step algebra: divide.', (x + 1, k * x - k))
    for b in range(12, 60, 3):
        for x in range(14, 80, 7):
            p.add_int(f'Solve: x + {b} = {x + b}', x, 'One-step algebra: subtract.', (x + 2 * b, x + 10))
            p.add_int(f'Solve: x - {b} = {x}', x + b, 'One-step algebra: add.', (x - b, x + b - 10))
    for k in range(3, 10):
        for c in range(6, 20):
            p.add_int(f'Solve: x/{k} = {c}', k * c, 'One-step with fraction: multiply both sides by k.', (c + k, k * c - k))


def _g_twostep_t4(p: Pool):
    for k in range(3, 10):
        for x in range(4, 16):
            for b in (3, 5, 7, 9, 11, 14):
                c = k * x + b
                p.add_int(f'Solve: {k}x + {b} = {c}', x, 'Two-step algebra: undo add/sub, then divide.', (x + 1, (c + b) // k))
                c2 = k * x - b
                if c2 > 0:
                    p.add_int(f'Solve: {k}x - {b} = {c2}', x, 'Two-step algebra: undo add/sub, then divide.', (x - 1, max(0, (c2 - b) // k)))


def _g_squares_t4(p: Pool):
    for b in range(13, 21):
        p.add_int(f'{b}² = ?', b * b, 'Squares to 20 — memorize.', (b * b + 10, b * b - b, b * 2))
        p.add_int(f'{b} squared = ?', b * b, 'Squares to 20 — memorize.', (b * b + 10, b * b - b))
    for b, e in ((2, 11), (3, 6), (4, 5), (6, 4), (11, 3), (12, 3)):
        v = b ** e
        p.add_int(f'{b}^{e} = ?', v, 'Exponent recall — memorize the ladder.', (v + b, v - b, v * 2 if b == 2 else v + 10))
    for a in range(2, 13):
        for b in range(a + 1, 13):
            if b * b - a * a > 0:
                p.add_int(f'{b}² - {a}² = ?', b * b - a * a, 'Substitute the memorized square/cube, then compute.',
                          ((b - a) ** 2, b * b - a * a + 10))
            p.add_int(f'{a}² + {b}² = ?', a * a + b * b, 'Substitute the memorized square/cube, then compute.',
                      ((a + b) ** 2, a * a + b * b + 10))


def _g_divis_t4(p: Pool):
    pool = [3, 4, 6, 7, 8, 9, 11, 12]
    rng = random.Random(f'{SEED}:divis4')
    ns = list(range(101, 900))
    rng.shuffle(ns)
    for n in ns:
        divs = [d for d in pool if n % d == 0]
        non = [d for d in pool if n % d]
        if len(divs) == 1 and len(non) >= 3:
            d = divs[0]
            p.add(f'Which number divides {n} evenly?', d, p.rng.sample(non, 3),
                  f'Try each divisibility rule ({d} divides {n}).')


def _g_roots_t4(p: Pool):
    for r in range(2, 16):
        p.add_int(f'√{r * r} = ?', r, 'Perfect-square root — inverse of memorized squares.', (r + 1, r - 1, r * 2))
    for r in (20, 30, 40, 50):
        p.add_int(f'√{r * r} = ?', r, 'Perfect-square root — inverse of memorized squares.', (r * 10, r + 10, r // 2))
    for r in (2, 3, 4, 10):
        p.add_int(f'Cube root of {r ** 3} = ?', r, 'Memorized cube root.', (r + 1, r * r, r - 1))


def _g_find_pct_t4(p: Pool):
    for whole in (20, 40, 50, 60, 80, 120, 150, 160, 200, 240, 250, 300, 400, 500, 600, 800):
        for pct in (5, 10, 15, 20, 25, 30, 35, 40, 45, 60, 65, 70, 75, 80, 85, 90):
            part = Fraction(whole * pct, 100)
            if part.denominator == 1 and part > 0:
                p.add_int(f'What % of {whole} is {int(part)}?', pct, 'Percent = (part / whole) × 100.',
                          (pct + 5, pct - 5, 100 - pct))


def _g_fracdiv_t4(p: Pool):
    fracs = [Fraction(a, b) for b in (2, 3, 4, 5, 6, 8) for a in range(1, b) if math.gcd(a, b) == 1]
    for x in fracs:
        for y in fracs:
            if x == y:
                continue
            ans = x / y
            wrongs = [x * y, y / x, Fraction(x.numerator * y.numerator, x.denominator + y.denominator) or 1]
            wrongs = [w for w in wrongs if w != ans and w > 0]
            wrongs += [ans + Fraction(1, 2), ans * 2]
            p.add(f'({_fmt(x)}) ÷ ({_fmt(y)}) = ?', ans, [w for w in wrongs if w != ans][:3],
                  'Fraction op: find common denom or invert-multiply.')


def _g_fdp_t4(p: Pool):
    table = [('1/8', '0.125'), ('3/8', '0.375'), ('5/8', '0.625'), ('7/8', '0.875'),
             ('1/3', '0.333'), ('2/3', '0.667')]
    decs = [d for _f, d in table]
    for f, d in table:
        p.add(f'{f} as decimal?', d, p.rng.sample([x for x in decs if x != d], 3),
              'Extended F↔D — divide the numerator by denominator.')


def _g_oo_t4(p: Pool):
    for a in range(2, 10):
        for b in range(2, 7):
            for c in range(2, 30, 3):
                ans = a * b * b + c
                p.add_int(f'{a} × {b}² + {c} = ?', ans, 'Order of ops: powers first, then multiply, then add.',
                          ((a * b) ** 2 + c, a * b * 2 + c))


def _g_series_t4(p: Pool):
    for n in (9, 10, 11, 12, 13, 14):
        ans = n * (n + 1) // 2
        p.add_int(f'1+2+3+...+{n} = ?', ans, 'Sum formula: n(n+1)/2.', (ans + n, ans - n, n * n))


# --- tier 5 ------------------------------------------------------------------

def _g_exp_t5(p: Pool):
    for b in (2, 3, 4, 5, 6, 7, 10):
        for m in range(2, 9):
            for n in range(2, 9):
                k = m + n
                if b ** k > 10 ** 8 or (b == 10 and k > 6):
                    continue
                v = b ** k
                times = b ** (m * n) if m * n != k and b ** (m * n) < 10 ** 9 else v * b * b
                p.add(f'{b}^{m} × {b}^{n} = ?', v, [times, v // b, v * b],
                      f'Exponent rule: a^m × a^n = a^(m+n) = {b}^{k}.')
        for m in range(4, 13):
            for n in range(2, m):
                k = m - n
                v = b ** k
                if b ** m > 10 ** 9 or (b == 10 and m > 6):
                    continue
                wrong = [v * b, v // b if v // b > 1 else v * b * b, b * k if b * k != v else v + b]
                p.add(f'{b}^{m} ÷ {b}^{n} = ?', v, wrong,
                      f'Exponent rule: a^m ÷ a^n = a^(m-n) = {b}^{k}.')


def _g_pct_t5(p: Pool):
    for pct in (110, 120, 125, 150, 175, 200, 250, 300):
        for n in range(8, 200, 4):
            ans = Fraction(pct * n, 100)
            if ans.denominator == 1:
                p.add_int(f'{pct}% of {n}?', int(ans), f'{pct}% shortcut: 100% is the whole, then add the rest.',
                          (int(ans) - n, n + pct // 10))
    for pct in ('12.5', '2.5', '0.5', '37.5', '62.5', '7.5', '1.5'):
        f = Fraction(pct)
        for n in range(40, 1000, 8):
            ans = f * n / 100
            if ans.denominator == 1 and ans > 1:
                p.add_int(f'{pct}% of {n}?', int(ans), 'Fractional percent: build it from 10%, 5% and 1%.',
                          (int(ans) * 10, int(ans) + 1, int(ans) * 2))
    for pct in (5, 10, 15, 20, 25, 30, 40, 50, 60, 75):
        for n in range(40, 600, 20):
            up = Fraction(n * (100 + pct), 100)
            down = Fraction(n * (100 - pct), 100)
            if up.denominator == 1:
                p.add_int(f'Increase {n} by {pct}%?', int(up), 'Markup: find the percent, then add it on.',
                          (int(up) - n * pct // 100 * 2 if pct else int(up) + 1, n + pct, int(down)))
            if down.denominator == 1:
                p.add_int(f'Decrease {n} by {pct}%?', int(down), 'Discount: find the percent, then take it off.',
                          (n - pct, int(up), int(down) + n * pct // 100))


def _g_parts_t5(p: Pool):
    rng = random.Random(f'{SEED}:parts5')
    pairs = [(a, b) for a in range(21, 60) for b in range(a, 60) if a % 10 and b % 10]
    rng.shuffle(pairs)
    for a, b in pairs:
        ans = a * b
        p.add_int(f'{a} × {b} = ?', ans, 'Distribute: a×tens + a×ones (then combine).',
                  (ans + 10, ans - 10 * (b % 10), ans + a))
        if len(p.items) > 400:
            break


def _g_oo_t5(p: Pool):
    for a in range(2, 20):
        for b in range(2, 10):
            for c in range(2, 10):
                v = a - b * c
                if v < 0:
                    p.add_int(f'{a} - {b} × {c} = ?', v, 'Order of ops: multiply first, then track the sign.',
                              (-v, (a - b) * c))
                v2 = b * -c + a
                if a > 9:
                    p.add_int(f'{b} × (-{c}) + {a} = ?', v2, 'Order of ops: multiply first, then track the sign.',
                              (b * c + a, -(b * c + a)))
    for a in range(2, 9):
        for b in range(2, 6):
            for c in range(2, 30, 5):
                v = c - a * b * b
                if v < 0:
                    p.add_int(f'{c} - {a} × {b}² = ?', v, 'Order of ops: powers first, multiply, then track the sign.',
                              (-v, (c - a) * b * b))


def _g_find_pct_t5(p: Pool):
    for old in range(20, 500, 10):
        for pct in (5, 10, 15, 20, 25, 30, 40, 50, 60, 75):
            new_up = Fraction(old * (100 + pct), 100)
            new_dn = Fraction(old * (100 - pct), 100)
            if new_up.denominator == 1:
                p.add_int(f'From {old} to {int(new_up)}: % increase?', pct, '% change = (new − old) / old × 100.',
                          (pct + 5, int(round(100 * (new_up - old) / new_up))))
            if new_dn.denominator == 1:
                p.add_int(f'From {old} to {int(new_dn)}: % decrease?', pct, '% change = (new − old) / old × 100.',
                          (pct + 5, int(round(100 * (old - new_dn) / new_dn))))
    for whole in (20, 40, 50, 60, 80, 120, 200, 250, 400):
        for pct in (110, 120, 125, 150, 175, 200, 250):
            part = Fraction(whole * pct, 100)
            if part.denominator == 1:
                p.add_int(f'What % of {whole} is {int(part)}?', pct, 'Percent = (part / whole) × 100.',
                          (pct - 100, pct + 10))


def _g_frac_t5(p: Pool):
    fracs = [Fraction(a, b) for b in (2, 3, 4, 5, 6, 8) for a in range(1, b) if math.gcd(a, b) == 1]
    for x in fracs:
        for y in fracs:
            if x >= y:
                continue
            ans = x - y
            wrongs = [y - x, Fraction(x.numerator - y.numerator, x.denominator + y.denominator), ans - Fraction(1, 2)]
            p.add(f'{_fmt(x)} - {_fmt(y)} = ?', ans, [w for w in wrongs if w != ans][:3],
                  'Fraction op: find common denom or invert-multiply; then the sign.')
    for x in fracs:
        for y in fracs:
            ans = -x * y
            wrongs = [x * y, -(x + y), -x / y]
            p.add(f'(-{_fmt(x)}) × ({_fmt(y)}) = ?', ans, [w for w in wrongs if w != ans][:3],
                  'Fraction op: find common denom or invert-multiply; then the sign.')


def _g_roots_t5(p: Pool):
    for r in range(16, 30):
        if r % 10 == 0:
            continue
        p.add_int(f'√{r * r} = ?', r, 'Memorized square root.', (r + 1, r - 1, r + 2))
    for r in range(5, 10):
        p.add_int(f'Cube root of {r ** 3} = ?', r, 'Memorized cube root.', (r + 1, r - 1, r * r))


def _g_squares_t5(p: Pool):
    for b in range(21, 30):
        if b % 10 == 0 or b == 25:
            continue
        p.add_int(f'{b}² = ?', b * b, 'Squares — use (n-1)² + 2n - 1, or split the number.', (b * b + 10, b * b - b, (b - 1) ** 2))
        p.add_int(f'{b} squared = ?', b * b, 'Squares — use (n-1)² + 2n - 1, or split the number.', (b * b + 10, b * b - b))
    for b in (11, 12, 13):
        p.add_int(f'{b}³ = ?', b ** 3, 'Cubes — square first, then multiply once more.', (b ** 3 + b, b ** 3 - 10 * b, b * b * 10))
    for a in range(11, 26):
        for b in range(a + 1, min(a + 5, 30)):
            v = b * b - a * a
            p.add_int(f'{b}² - {a}² = ?', v, 'Squares — difference of squares: b² - a² = (b - a)(b + a).',
                      ((b - a) ** 2, v + 10, 2 * (b - a)))


def _g_series_t5(p: Pool):
    for n in (15, 16, 18, 20, 24, 25, 30, 36, 40, 45, 48, 50, 80, 90, 99, 100, 120, 150, 200):
        ans = n * (n + 1) // 2
        p.add_int(f'1+2+3+...+{n} = ?', ans, 'Sum formula: n(n+1)/2.', (ans + n, n * n // 2, ans - n))


def _g_pyth_t5(p: Pool):
    prims = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29), (12, 35, 37), (9, 40, 41)]
    triples = []
    for a, b, c in prims:
        for k in range(1, 11):
            if c * k <= 60:
                triples.append((a * k, b * k, c * k))
    for a, b, c in triples:
        p.add_int(f'Pyth. triple: legs {a}, {b}. Hypotenuse?', c, 'Memorize the classic triples + scaled versions.',
                  (a + b, c + 1, c - 1))
        p.add_int(f'Pyth. triple: leg {a}, hypotenuse {c}. Other leg?', b, 'Memorize the classic triples + scaled versions.',
                  (c - a, b + 1, b - 1))
        p.add_int(f'Pyth. triple: leg {b}, hypotenuse {c}. Other leg?', a, 'Memorize the classic triples + scaled versions.',
                  (c - b, a + 1, a - 1))


def _g_twostep_t5(p: Pool):
    for k in range(2, 8):
        for x in range(-12, 16):
            for b in (4, 6, 9, 12, 15, 20):
                c = k * x + b
                if x < 0:
                    p.add_int(f'Solve: {k}x + {b} = {c}', x, 'Two-step algebra: undo add/sub, then divide.', (-x, x + 1))
    for k in range(3, 9):
        for x in range(3, 18):
            for b in (2, 3, 4, 5, 6, 7):
                p.add_int(f'Solve: {k}(x + {b}) = {k * (x + b)}', x, 'Distribute first, or divide both sides by k first.',
                          (x + b, k * (x + b) // k - 1 + b))
                if x > b:
                    p.add_int(f'Solve: {k}(x - {b}) = {k * (x - b)}', x, 'Divide both sides by k, then add b.',
                              (x - b, x - 2 * b if x > 2 * b else x + 1))


def _g_negatives_t5(p: Pool):
    for d in range(3, 10):
        for q in range(6, 16):
            n = d * q
            p.add_int(f'-{n} ÷ {d} = ?', -q, 'Sign rule: same → +, different → -.', (q, -q - 1))
            p.add_int(f'-{n} ÷ -{d} = ?', q, 'Sign rule: same → +, different → -.', (-q, q + 1))
    for a in range(13, 30):
        for b in range(3, 9):
            p.add_int(f'-{a} × {b} = ?', -a * b, 'Sign rule: same → +, different → -.', (a * b, -a * b - 10))


def _g_fdp_t5(p: Pool):
    table = [('1/6', '0.167'), ('5/6', '0.833'), ('1/12', '0.083'), ('5/12', '0.417'), ('7/12', '0.583'),
             ('11/12', '0.917'), ('1/9', '0.111'), ('2/9', '0.222'), ('4/9', '0.444'), ('5/9', '0.556'),
             ('7/9', '0.778'), ('8/9', '0.889'), ('1/7', '0.143'), ('2/7', '0.286'), ('1/11', '0.091')]
    decs = [d for _f, d in table]
    for f, d in table:
        p.add(f'{f} as decimal?', d, p.rng.sample([x for x in decs if x != d], 3),
              'Extended F↔D — divide the numerator by denominator.')


GENERATORS = {
    ('Adding and Subtracting Tens', 1): _g_tens_t1,
    ('Doubling and Halving', 1): _g_double_t1,
    ('Times Tables', 2): _g_times_t2,
    ('Division Facts', 2): _g_division_t2,
    ('Adding and Subtracting Tens', 2): _g_tens_t2,
    ('Doubling and Halving', 2): _g_double_t2,
    ('Two-Digit Addition and Subtraction', 2): _g_twodigit_t2,
    ('Two-Digit Addition and Subtraction', 3): _g_twodigit_t3,
    ('Multiplying by Parts', 3): _g_parts_t3,
    ('Fraction of a Quantity', 3): _g_fraction_of_t3,
    ('Squares, Cubes and Powers', 3): _g_squares_t3,
    ('Divisibility Rules', 3): _g_divis_t3,
    ('Fraction of a Quantity', 4): _g_fraction_of_t4,
    ('Percent of a Number', 4): _g_percent_t4,
    ('Negative Numbers', 4): _g_negatives_t4,
    ('One-Step Equations', 4): _g_onestep_t4,
    ('Two-Step Equations', 4): _g_twostep_t4,
    ('Squares, Cubes and Powers', 4): _g_squares_t4,
    ('Divisibility Rules', 4): _g_divis_t4,
    ('Square and Cube Roots', 4): _g_roots_t4,
    ('Finding the Percent', 4): _g_find_pct_t4,
    ('Fraction Arithmetic', 4): _g_fracdiv_t4,
    ('Fractions, Decimals and Percents', 4): _g_fdp_t4,
    ('Order of Operations', 4): _g_oo_t4,
    ('Sum of 1 to N', 4): _g_series_t4,
    ('Exponent Rules', 5): _g_exp_t5,
    ('Percent of a Number', 5): _g_pct_t5,
    ('Multiplying by Parts', 5): _g_parts_t5,
    ('Order of Operations', 5): _g_oo_t5,
    ('Finding the Percent', 5): _g_find_pct_t5,
    ('Fraction Arithmetic', 5): _g_frac_t5,
    ('Square and Cube Roots', 5): _g_roots_t5,
    ('Squares, Cubes and Powers', 5): _g_squares_t5,
    ('Sum of 1 to N', 5): _g_series_t5,
    ('Pythagorean Triples', 5): _g_pyth_t5,
    ('Two-Step Equations', 5): _g_twostep_t5,
    ('Negative Numbers', 5): _g_negatives_t5,
    ('Fractions, Decimals and Percents', 5): _g_fdp_t5,
}


# ---------------------------------------------------------------------------
# The card-leak rule (tests/test_math_contexts.py): a topic card must not
# contain the exact sum of a question in its own class.
# ---------------------------------------------------------------------------

def _load_cards() -> dict:
    try:
        return json.loads(MATH_CARDS.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {}


def leaks_card(q: dict, cards: dict) -> bool:
    core = q['question'].replace(' = ?', '').rstrip('?').strip()
    if len(core) < 3 or not any(c.isdigit() for c in core):
        return False
    blurb = cards.get(q['topic'], {}).get('context_blurb', '')
    pat = r'(?<![\d.,^/])' + re.escape(core) + r'(?![\d.,^/])'
    return bool(re.search(pat, blurb))


# ---------------------------------------------------------------------------
# The audit
# ---------------------------------------------------------------------------

def _homes(topic: str, score: float, origin: int) -> list[int]:
    tiers = [t for t in md.allowed_tiers(topic) if md.in_band(score, t)]
    return sorted(tiers, key=lambda t: (abs(t - origin), t))


def _center(t: int) -> float:
    lo, hi = md.tier_band(t)
    return (lo + hi) / 2


def audit(bank: list[dict]) -> list[dict]:
    """One row per question: score, status and the tiers that would fit it.

    status: 'ok' | 'below' | 'above' | 'trivial' | 'duplicate' | 'topic'
    ('topic' = in band, but the topic has no grade band at that tier)."""
    rows = []
    for i, q in enumerate(bank):
        r = md.rate(q)
        t = int(q['tier'])
        lo, hi = md.tier_band(t)
        topic_ok = t in md.allowed_tiers(q['topic'])
        if r.trivial and not md.in_band(r.score, t):
            status = 'trivial'
        elif r.score < lo:
            status = 'below'
        elif r.score >= hi:
            status = 'above'
        elif not topic_ok:
            status = 'topic'
        else:
            status = 'ok'
        rows.append({'idx': i, 'tier': t, 'topic': q['topic'], 'question': q['question'],
                     'score': r.score, 'rating': r, 'status': status,
                     'homes': _homes(q['topic'], r.score, t)})
    # the same stem in two tiers: keep the copy that fits best, flag the rest
    by_stem = defaultdict(list)
    for row in rows:
        by_stem[row['question'].strip()].append(row)
    for copies in by_stem.values():
        if len(copies) < 2:
            continue
        fits = [c for c in copies if c['status'] == 'ok']
        if fits:
            keep = min(fits, key=lambda c: (abs(_center(c['tier']) - c['score']), c['tier']))
        else:
            keep = min(copies, key=lambda c: (min([abs(h - c['tier']) for h in c['homes']] or [9]), c['tier']))
        for c in copies:
            if c is not keep:
                c['status'] = 'duplicate'
    return rows


# ---------------------------------------------------------------------------
# The curve
# ---------------------------------------------------------------------------

SHAPE_SLACK = 0.25         # grade units a draw may give up for a fresher stem shape


def _shape(stem: str) -> str:
    """A stem with its numbers blanked: '12.5% of 112?' -> 'D% of N?'."""
    return re.sub(r'\d+', 'N', re.sub(r'\d+\.\d+', 'D', stem))


def _distance_out(row) -> float:
    lo, hi = md.tier_band(row['tier'])
    s = row['score']
    return lo - s if s < lo else s - hi + 1e-9 if s >= hi else 0.0


def curve(bank: list[dict], sizes: dict[int, int] | None = None) -> tuple[list[dict], dict]:
    """Return (curved bank, report). Pure: the input list is not changed.

    ``sizes``: the tier sizes to cap growth at and backfill to (default:
    the input bank's own sizes)."""
    bank = [dict(q) for q in bank]
    rows = audit(bank)
    cards = _load_cards()
    orig = Counter(int(q['tier']) for q in bank)
    base = {t: (sizes or orig)[t] for t in orig}
    cap = {t: int(base[t] * (1 + CAP_GROWTH)) for t in orig}
    net = Counter()

    # 1. moves into tiers with room. A topic with no grade band at its tier
    #    would vanish from the bank if replaced, so it moves first; then the
    #    most out of band.
    cands = [r for r in rows if r['status'] in ('below', 'above', 'topic') and r['homes']]
    cands.sort(key=lambda r: (r['tier'] in md.allowed_tiers(r['topic']), -_distance_out(r),
                              r['tier'], r['topic'], r['idx']))
    moved: dict[int, int] = {}
    changed = True
    while changed:
        changed = False
        for r in cands:
            if r['idx'] in moved:
                continue
            for home in r['homes']:
                if orig[home] + net[home] + 1 <= cap[home]:
                    moved[r['idx']] = home
                    net[home] += 1
                    net[r['tier']] -= 1
                    changed = True
                    break

    # 2. what is left out of band is replaced in place
    replace = [r for r in rows if r['status'] != 'ok' and r['idx'] not in moved]

    # 3. pools, built lazily; every stem in the bank is taken
    taken = {q['question'].strip() for q in bank}
    pools: dict[tuple[str, int], list[dict]] = {}

    def pool(topic: str, tier: int) -> list[dict]:
        key = (topic, tier)
        if key not in pools:
            gen = GENERATORS.get(key)
            if gen is None or tier not in md.allowed_tiers(topic):
                pools[key] = []
            else:
                p = Pool(topic, tier)
                gen(p)
                items = [q for q in p.items if not leaks_card(q, cards)]
                items.sort(key=lambda q: (md.score(q), q['question']))
                pools[key] = items
        return pools[key]

    # Variety: among candidates about as close to the target score, take the
    # stem shape the tier's topic holds least of (counting what it keeps).
    shapes: dict[tuple[str, int], Counter] = defaultdict(Counter)
    for r in rows:
        if r['status'] == 'ok':
            shapes[(r['topic'], r['tier'])][_shape(r['question'])] += 1

    def draw(topic: str, tier: int, target: float) -> dict | None:
        items = [q for q in pool(topic, tier) if q['question'] not in taken]
        if not items:
            return None
        dist = {q['question']: abs(md.score(q) - target) for q in items}
        near = min(dist.values()) + SHAPE_SLACK
        held = shapes[(topic, tier)]
        best = min((q for q in items if dist[q['question']] <= near),
                   key=lambda q: (held[_shape(q['question'])], dist[q['question']], q['question']))
        taken.add(best['question'])
        held[_shape(best['question'])] += 1
        return dict(best)

    def draw_for(topic: str, tier: int, target: float) -> tuple[dict | None, str]:
        q = draw(topic, tier, target)
        if q is not None:
            return q, topic
        fills = md.load_table()['fill_topics'][str(tier)]
        for k in range(len(fills)):
            alt = fills[(int(target * 100) + k) % len(fills)]
            q = draw(alt, tier, target)
            if q is not None:
                return q, alt
        raise RuntimeError(f'no in-band question left for tier {tier} ({topic})')

    def spread_targets(group: list[dict], tier: int) -> list[float]:
        """Spread a group's replacements over the band, easiest first, in
        the order of the scores they replace."""
        lo, hi = md.tier_band(tier)
        n = len(group)
        return [lo + (hi - lo - EDGE) * (k + 0.5) / n for k in range(n)]

    replaced_with: dict[int, dict] = {}
    log_replace = Counter()
    groups = defaultdict(list)
    for r in replace:
        groups[(r['tier'], r['topic'])].append(r)
    for (tier, topic), group in sorted(groups.items()):
        group.sort(key=lambda r: (r['score'], r['idx']))
        targets = spread_targets(group, tier)
        for r, target in zip(group, targets):
            q, used = draw_for(topic, tier, target)
            replaced_with[r['idx']] = q
            log_replace[(tier, topic, r['status'], used)] += 1

    # 4. backfill a tier that lost more than it gained
    left = defaultdict(Counter)
    for idx, home in moved.items():
        left[bank[idx]['tier']][bank[idx]['topic']] += 1
    backfill: dict[int, list[dict]] = defaultdict(list)
    log_backfill = Counter()
    for tier in sorted(orig):
        deficit = base[tier] - (orig[tier] + net[tier])
        if deficit <= 0:
            continue
        topics = []
        for topic, n in left[tier].most_common():
            topics.extend([topic] * n)
        fills = md.load_table()['fill_topics'][str(tier)]
        while len(topics) < deficit:                  # a short raw draw
            topics.append(fills[len(topics) % len(fills)])
        topics = topics[:deficit]
        by_topic = Counter(topics)
        for topic, n in sorted(by_topic.items()):
            lo, hi = md.tier_band(tier)
            for k in range(n):
                target = lo + (hi - lo - EDGE) * (k + 0.5) / n
                q, used = draw_for(topic, tier, target)
                backfill[tier].append(q)
                log_backfill[(tier, topic, used)] += 1

    # 5. assemble, tier by tier: kept and replaced in their old places,
    #    then the questions that moved in, then the backfill
    out = []
    for tier in sorted(orig):
        for i, q in enumerate(bank):
            if q['tier'] != tier or i in moved:
                continue
            out.append(replaced_with.get(i, q))
        for i in sorted(moved):
            if moved[i] == tier:
                q = dict(bank[i])
                q['tier'] = tier
                out.append(q)
        out.extend(backfill[tier])

    report = {
        'before': dict(orig),
        'after': dict(Counter(q['tier'] for q in out)),
        'moved': Counter((bank[i]['tier'], t, bank[i]['topic']) for i, t in moved.items()),
        'replaced': log_replace,
        'backfill': log_backfill,
        'flagged': Counter((r['tier'], r['status']) for r in rows if r['status'] != 'ok'),
    }
    return out, report


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def tier_summary(bank: list[dict]) -> list[dict]:
    by = defaultdict(list)
    for q in bank:
        by[int(q['tier'])].append(md.rate(q))
    out = []
    for t in sorted(by):
        rs = by[t]
        sc = sorted(r.score for r in rs)
        secs = sorted(md.practised_seconds(r) for r in rs)
        out.append({
            'tier': t, 'n': len(rs),
            'score_min': sc[0], 'score_p10': _quantile(sc, 0.1), 'score_median': statistics.median(sc),
            'score_p90': _quantile(sc, 0.9), 'score_max': sc[-1],
            'digits_median': statistics.median(r.digits for r in rs),
            'steps_median': statistics.median(r.steps for r in rs),
            'regroups_mean': round(statistics.mean(r.regroups for r in rs), 2),
            'work_median': statistics.median(r.work for r in rs),
            'seconds_median': round(statistics.median(secs), 2),
            'seconds_p25': round(_quantile(secs, 0.25), 2),
            'seconds_p75': round(_quantile(secs, 0.75), 2),
        })
    return out


def _quantile(sorted_vals, p: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * p
    f = math.floor(k)
    c = min(f + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def doc_table() -> str:
    table = md.load_table()
    lines = ['| Topic | Tier | Grades | Standard | In plain words |', '|---|---|---|---|---|']
    for topic, entry in table['topics'].items():
        for t, slot in sorted(entry['tiers'].items()):
            lines.append(f"| {topic} | {t} | {slot['grades']} | {slot['standard']} | {slot['plain']} |")
    return '\n'.join(lines)


def _print_report(before: list[dict], after: list[dict], report: dict) -> None:
    print('Tier counts:', {t: f"{report['before'][t]} -> {report['after'].get(t, 0)}" for t in sorted(report['before'])})
    print('\nFlagged (tier, status):')
    for k, n in sorted(report['flagged'].items()):
        print(f'  T{k[0]} {k[1]:10s} {n}')
    print('\nMoved (from -> to, topic):')
    for (a, b, topic), n in sorted(report['moved'].items()):
        print(f'  T{a} -> T{b}  {topic:36s} {n}')
    print('\nReplaced in place (tier, topic, why, new topic):')
    for (t, topic, why, used), n in sorted(report['replaced'].items()):
        extra = '' if used == topic else f'  -> {used}'
        print(f'  T{t} {topic:36s} {why:10s} {n}{extra}')
    print('\nBackfill (tier, topic that left, new topic):')
    for (t, topic, used), n in sorted(report['backfill'].items()):
        extra = '' if used == topic else f'  -> {used}'
        print(f'  T{t} {topic:36s} {n}{extra}')
    for label, bank in (('BEFORE', before), ('AFTER', after)):
        print(f'\n{label}: tier  n  min  p10  median  p90  max | digits steps regroups work | practised s (p25 med p75)')
        for s in tier_summary(bank):
            print(f"  T{s['tier']} {s['n']:4d} {s['score_min']:.2f} {s['score_p10']:.2f} {s['score_median']:.2f} "
                  f"{s['score_p90']:.2f} {s['score_max']:.2f} | {s['digits_median']} {s['steps_median']} "
                  f"{s['regroups_mean']} {s['work_median']} | {s['seconds_p25']} {s['seconds_median']} {s['seconds_p75']}")


def main(argv: list[str]) -> int:
    if '--doc' in argv:
        print(doc_table())
        return 0
    bank = json.loads(MATH_BANK.read_text(encoding='utf-8'))
    if '--audit' in argv:
        for r in audit(bank):
            if r['status'] != 'ok':
                print(f"T{r['tier']} {r['score']:.2f} {r['status']:9s} {r['topic']:34s} {r['question']}  homes={r['homes']}")
        return 0
    curved, report = curve(bank)
    _print_report(bank, curved, report)
    target = MATH_BANK
    if '--out' in argv:
        target = Path(argv[argv.index('--out') + 1])
    if '--dry-run' not in argv:
        target.write_text(json.dumps(curved, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'\nwrote {len(curved)} questions to {target}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
