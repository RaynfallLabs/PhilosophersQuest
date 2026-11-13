"""Maths difficulty: one deterministic grade-level score per question.

Maths is the timed subject (combat chains), and its five tiers are meant
to climb a smooth school-grade curve of MENTAL maths (Brandon, 2026-11-13:
"legitimately tuned to tier ... a smooth grade progression curve for
mental math, and with practice, kids can get faster with higher tiers").

``rate(question)`` reads a question's stem (and answer) and returns a
``Rating``: the skill ``kind``, a ``score`` on a school-grade scale
(1.0 = the start of grade 1, 8.9 = the end of grade 8), and the plain
difficulty proxies behind it (digits handled, mental steps, carries or
borrows, and the "work" in fluent mental operations that the answer-time
model uses).

How the score is built, in plain words (docs/quiz/math_grade_curve.md has
the full table):

* Every kind of question starts at the grade where the standards first
  ask for it as mental work (Common Core first, the UK National
  Curriculum where it places a skill earlier; both named in the table).
* The numbers move it up inside that kind: more digits, a carry or a
  borrow, a harder times-table fact, a second step, a bigger answer.
* An item that needs no real work (times 0 or 1, plus 0, a power of 1,
  the root of 1) is marked ``trivial``.

The tier bands live in tools/balance/math_grade_curve.json, which this
module, the curve tool (math_grade_curve.py), the quiz pipeline gate
(tools/quizgen/deterministic/math_grade_band.py) and the tests all read.

Pure functions only: no randomness, no game imports.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CURVE_TABLE = ROOT / 'tools' / 'balance' / 'math_grade_curve.json'

TRIVIAL_SCORE = 2.0          # x 0, x 1, / 1: no real work
LADDER_TOP = 7.1             # a power harder than this is past the memorised ladders


@dataclass(frozen=True)
class Rating:
    kind: str                # skill kind, e.g. 'arithmetic', 'percent_of', 'root'
    score: float             # school-grade score (1.0 = start of grade 1)
    digits: int              # most digits in any number the kid handles
    steps: int               # separate mental operations
    regroups: int            # carries plus borrows
    work: float              # fluent mental operations, weighted (time model)
    trivial: bool = False

    def as_dict(self) -> dict:
        return {'kind': self.kind, 'score': self.score, 'digits': self.digits,
                'steps': self.steps, 'regroups': self.regroups,
                'work': self.work, 'trivial': self.trivial}


class UnratedQuestion(ValueError):
    """A stem shape the scorer does not know (a new generator must add one)."""


# ---------------------------------------------------------------------------
# The band table
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_table() -> dict:
    return json.loads(CURVE_TABLE.read_text(encoding='utf-8'))


def tier_band(tier: int) -> tuple[float, float]:
    """[low, high) score band for a tier."""
    lo, hi = load_table()['tiers'][str(tier)]['band']
    return float(lo), float(hi)


def in_band(score: float, tier: int) -> bool:
    lo, hi = tier_band(tier)
    return lo <= score < hi


def allowed_tiers(topic: str) -> tuple[int, ...]:
    """Tiers at which a topic has a grade band."""
    entry = load_table()['topics'].get(topic, {})
    return tuple(sorted(int(t) for t in entry.get('tiers', {})))


# ---------------------------------------------------------------------------
# Small number helpers
# ---------------------------------------------------------------------------

def _ndig(n) -> int:
    return len(str(abs(int(n))))


def _digits(n: int) -> list[int]:
    """Digits from the ones place upward."""
    return [int(c) for c in reversed(str(abs(int(n))))]


def _nonzero(n: int) -> int:
    return max(1, sum(1 for d in _digits(n) if d))


def add_carries(a: int, b: int) -> int:
    da, db = _digits(a), _digits(b)
    carry = count = 0
    for i in range(max(len(da), len(db))):
        s = (da[i] if i < len(da) else 0) + (db[i] if i < len(db) else 0) + carry
        carry = 1 if s >= 10 else 0
        count += carry
    return count


def sub_borrows(a: int, b: int) -> int:
    """Borrows in a - b (a >= b >= 0), column by column."""
    da, db = _digits(a), _digits(b)
    borrow = count = 0
    for i in range(len(da)):
        top = da[i] - borrow
        bot = db[i] if i < len(db) else 0
        if top < bot:
            borrow = 1
            count += 1
        else:
            borrow = 0
    return count


# How hard a single-digit times-table fact is to recall (0 easy .. 4 hard).
_FACT_H = {0: 0, 1: 0, 2: 1, 3: 2, 4: 2, 5: 1, 6: 3, 7: 4, 8: 4, 9: 3, 10: 0}


def fact_cost(p: int, q: int) -> float:
    """Recall cost of one single-digit product (2 x 2 = 0.5, 7 x 8 = 1.1)."""
    if p == 0 or q == 0:
        return 0.1
    if p == 1 or q == 1:
        return 0.15
    return 0.3 + 0.1 * _FACT_H[p] + 0.1 * _FACT_H[q]


def _strip_zeros(n: int) -> tuple[int, int]:
    z = 0
    while n and n % 10 == 0:
        n //= 10
        z += 1
    return n, z


# ---------------------------------------------------------------------------
# Whole-number operations: (grade, work, regroups)
# ---------------------------------------------------------------------------

def add_grade(a: int, b: int) -> tuple[float, float, int]:
    a, b = max(a, b), min(a, b)
    if b == 0:
        return 1.0, 0.3, 0
    if a <= 10:
        s = a + b
        if a == 10:
            return 1.3, 0.8, 0
        if s <= 10:
            return 1.0 + 0.04 * s, 1.0, 0
        g = 1.6 + 0.07 * (s - 11)          # make a ten
        return (g - 0.15 if a == b else g), 1.4, 1
    # In your head you add the simpler number (fewer non-zero digits) on to
    # the other: 15 + 30 is three tens added to 15.
    base, step = (a, b) if _nonzero(a) >= _nonzero(b) else (b, a)
    w = _nonzero(step)
    c = add_carries(a, b)
    extra = max(0, _ndig(base) - 2)
    g = 1.2 + 0.6 * w + 0.7 * c + 0.6 * extra
    return g, 1.2 * w + 0.9 * c + 0.5 * extra + 0.6 * (w - 1), c


def sub_grade(a: int, b: int) -> tuple[float, float, int]:
    if b == 0:
        return 1.0, 0.3, 0
    if a == b:
        return 1.1, 0.4, 0
    if a <= 20 and b <= 10:
        if a <= 10:
            return 1.1 + 0.04 * a, 1.0, 0
        if b <= a - 10:
            return 1.5, 1.0, 0
        return 1.8 + 0.05 * (a - b), 1.5, 1
    w = _nonzero(b)
    br = sub_borrows(a, b)
    extra = max(0, _ndig(a) - 2)
    g = 1.3 + 0.6 * w + 0.7 * br + 0.6 * extra
    return g, 1.2 * w + 1.0 * br + 0.5 * extra + 0.6 * (w - 1), br


def _table_fact(a: int, b: int) -> float:
    """Single-digit facts 2..10 (3.OA.C.7): 3.0 (2 x 2) to 3.6 (7 x 8)."""
    if a == 10 or b == 10:
        return 3.0
    return max(3.0, 3.0 + (fact_cost(a, b) - 0.5))


def _partials(a: int, b: int) -> tuple[float, int, int]:
    """Cost of a x b by place-value parts, splitting b. Returns
    (fact cost, carries adding the partial products, number of facts)."""
    facts = 0.0
    n = 0
    rows = []
    for i, db in enumerate(_digits(b)):
        if not db:
            continue
        for da in _digits(a):
            if da:
                facts += fact_cost(da, db)
                n += 1
        rows.append(a * db * 10 ** i)
    carries = 0
    total = 0
    for r in rows:
        carries += add_carries(total, r) if total else 0
        total += r
    # inside one row (a x single digit) the partial facts are also added
    for db in _digits(b):
        if not db:
            continue
        sub = [d * db * 10 ** j for j, d in enumerate(_digits(a)) if d]
        t = 0
        for s in sub:
            carries += add_carries(t, s) if t else 0
            t += s
    return facts, carries, n


def mul_grade(a: int, b: int) -> tuple[float, float, int]:
    a, b = max(a, b), min(a, b)
    if b == 0:
        return TRIVIAL_SCORE, 0.2, 0
    if b == 1:
        return TRIVIAL_SCORE + 0.2, 0.3, 0
    if a <= 10:
        return _table_fact(a, b), 0.6 + fact_cost(a, b), 0
    if a <= 12 and b <= 12:
        if b == 10:
            return 3.6, 1.0, 0
        if a == 11 and b <= 9:
            return 3.4 + 0.02 * b, 1.0, 0
        if a == 12 and b <= 9:
            return 3.5 + 0.5 * fact_cost(2, b), 1.2, 0
        return {(11, 11): 4.0, (12, 11): 4.1, (12, 12): 4.2}[(a, b)], 1.4, 0
    a0, za = _strip_zeros(a)
    b0, zb = _strip_zeros(b)
    z = za + zb
    if z:
        if a0 == 1 or b0 == 1:                    # times a power of ten
            return 2.8 + 0.2 * z, 0.6, 0
        g, w, c = mul_grade(a0, b0)
        return g + 0.35 + 0.1 * (z - 1), w + 0.4, c
    # no zeros: place-value parts (split whichever factor is cheaper)
    best = None
    for x, y in ((a, b), (b, a)):
        facts, carries, n = _partials(x, y)
        cost = facts + 0.35 * carries + 0.3 * (n - 1)
        if best is None or cost < best[0]:
            best = (cost, carries, n)
    cost, carries, n = best
    if min(_ndig(a), _ndig(b)) == 1:
        g = 3.4 + 0.6 * cost + 0.3 * max(0, _ndig(a) - 2)
    else:
        g = 4.4 + 0.75 * cost
    return g, 1.2 * n + 0.9 * carries + 0.8 * (n - 1), carries


def div_grade(a: int, b: int) -> tuple[float, float, int]:
    """a / b, exact."""
    if a == 0:
        return TRIVIAL_SCORE, 0.2, 0
    if b == 1 or a == b:
        return TRIVIAL_SCORE + 0.3, 0.3, 0
    q = a // b
    if b <= 12 and q <= 12:
        g, w, _ = mul_grade(b, q)
        return g + 0.2, w + 0.3, 0
    a0, za = _strip_zeros(a)
    if za and a0 % b == 0 and a0 // b <= 12 and b <= 12:
        g, w, _ = div_grade(a0, b)
        return g + 0.45, w + 0.4, 0
    if b <= 9:
        g = 4.3 + 0.5 * (_ndig(q) - 1) + 0.1 * _FACT_H[b]
        return g, 2.5 + 1.0 * _ndig(q), 1
    return 5.0 + 0.3 * (_ndig(q) - 1), 3.5 + _ndig(q), 1


def _whole(op: str, a: int, b: int) -> tuple[float, float, int]:
    if op == '+':
        return add_grade(a, b)
    if op == '-':
        return sub_grade(max(a, b), min(a, b))
    if op == '×':
        return mul_grade(a, b)
    return div_grade(a, b) if b and a % b == 0 else (5.0, 3.5, 1)


def _identity(op: str, x: Fraction, y: Fraction) -> bool:
    """No real work: + 0, - 0, n - n, x 0, x 1, / 1, n / n, 0 / n."""
    if op == '+':
        return x == 0 or y == 0
    if op == '-':
        return y == 0 or x == y
    if op == '×':
        return x in (0, 1) or y in (0, 1)
    return y == 1 or x == y or x == 0


# ---------------------------------------------------------------------------
# Fractions, decimals, negatives
# ---------------------------------------------------------------------------

def _is_int(v: Fraction) -> bool:
    return v.denominator == 1


def frac_op_grade(op: str, x: Fraction, y: Fraction) -> tuple[float, float]:
    """+ - x / with at least one fraction operand (5.NF / 6.NS.A.1 / 7.NS)."""
    neg = x < 0 or y < 0 or (op == '-' and x < y)
    if op in '+-':
        q1, q2 = x.denominator, y.denominator
        if q1 == q2:
            g, w = 4.2, 1.5
        else:
            lcd = q1 * q2 // math.gcd(q1, q2)
            both = lcd != max(q1, q2)                   # both fractions convert
            g = 5.0 + (0.3 if both else 0.0) + (0.15 if both and lcd != q1 * q2 else 0.0)
            g += 0.1 if lcd > 10 else 0.0
            w = 2.8 + (0.8 if both else 0.0)
        res = x + y if op == '+' else x - y
        raw_den = x.denominator * y.denominator // math.gcd(x.denominator, y.denominator)
        if res.denominator != raw_den and res != 0:
            g += 0.2
            w += 0.5
    elif op == '×':
        g, w = 5.0, 2.0
        if abs(x.numerator) != 1 or abs(y.numerator) != 1:
            g += 0.1
        res = x * y
        if res.denominator != x.denominator * y.denominator:
            g += 0.25
            w += 0.6
    else:  # '÷'
        g, w = 6.0, 2.8
        res = x / y
        if not _is_int(res):
            g += 0.2
            w += 0.4
        num, den = x.numerator * y.denominator, x.denominator * y.numerator
        if Fraction(num, den).denominator != abs(den):
            g += 0.2
            w += 0.4
    if neg:
        g = max(7.0, g + 2.0)                            # 7.NS.A.1-2
        w += 0.6
    return g, w


def _dp(text: str | None) -> int:
    if text and '.' in text:
        return len(text.split('.')[1])
    return 0


def dec_op_grade(op: str, x: Fraction, y: Fraction, xt: str, yt: str) -> tuple[float, float]:
    """Decimal arithmetic (5.NBT.B.7; dividing by a decimal 6.NS.B.3)."""
    dp = max(_dp(xt), _dp(yt))
    if op in '+-':
        g = 5.0 + 0.1 * max(0, dp - 1)
        res = x + y if op == '+' else x - y
        if _is_int(res) and not (_is_int(x) and _is_int(y)):
            g += 0.05
        return g, 1.6 + 0.3 * dp
    if op == '×':
        if x in (Fraction(1, 10), Fraction(1, 100)) or y in (Fraction(1, 10), Fraction(1, 100)):
            return 5.0 + 0.05 * dp, 1.2
        g = 5.1 + 0.1 * dp
        whole = y if _is_int(y) else x
        if _is_int(whole) and whole > 4:
            g += 0.1
        return g, 1.8 + 0.3 * dp
    g = 5.6 + (0.2 if dp >= 2 else 0.0)               # dividing by a decimal
    return g, 2.4 + 0.3 * dp


def _signed_magnitude(op: str, x: Fraction, y: Fraction) -> tuple[float, float, int]:
    """The bare arithmetic of x op y with the signs set aside: adding two
    numbers of one sign is an addition, of opposite signs a subtraction."""
    a, b = int(x), int(y)
    if op in '+-':
        if op == '-':
            b = -b
        if (a >= 0) == (b >= 0):
            return add_grade(abs(a), abs(b))
        return sub_grade(max(abs(a), abs(b)), min(abs(a), abs(b)))
    return _whole(op, abs(a), abs(b))


def neg_addsub_grade(op: str, x: Fraction, y: Fraction) -> tuple[float, float, int]:
    """Integers through zero (6.NS.C / 7.NS.A.1)."""
    g, w, r = _signed_magnitude(op, x, y)
    return 6.2 + 0.35 * (g - 1.0), w + 0.6, r


def sign_mul_grade(op: str, x: Fraction, y: Fraction) -> tuple[float, float, int]:
    """Products and quotients with signs (7.NS.A.2)."""
    g, w, r = _signed_magnitude(op, x, y)
    return 7.0 + 0.4 * max(0.0, g - 3.0), w + 0.6, r


# ---------------------------------------------------------------------------
# Powers and roots (memorised ladders)
# ---------------------------------------------------------------------------

def power_grade(b: int, e: int) -> float:
    if e == 1 or b in (0, 1):
        return TRIVIAL_SCORE + 0.5
    if e == 0:
        return TRIVIAL_SCORE + 1.0
    if b == 10:
        return 5.0 + 0.1 * (e - 2)                 # 5.NBT.A.2
    b0, z = _strip_zeros(b)
    if z:
        return power_grade(b0, e) + 0.35 + 0.1 * (z - 1)
    if e == 2:
        if b <= 10:
            return 4.2 + 0.08 * (b - 2)            # times-table squares
        if b <= 12:
            return {11: 5.0, 12: 5.2}[b]
        return mul_grade(b, b)[0] + 0.15
    if e == 3:
        if b <= 5:
            return 5.0 + 0.2 * (b - 2)
        if b <= 9:
            return 6.0 + 0.12 * (b - 6)
        return 7.5 + 0.1 * (b - 11)
    if b == 2:
        return 4.9 + 0.3 * (e - 3)
    return 5.6 + 0.5 * (e - 3) + 0.15 * (b - 2)


def power_work(g: float) -> float:
    return 0.8 + 0.6 * max(0.0, g - 4.2)


def sqrt_grade(r: int) -> float:
    if r in (0, 1):
        return TRIVIAL_SCORE + 0.5
    if r % 10 == 0:
        return 6.0 + 0.1 * (r // 10)
    if r <= 12:
        return 6.0 + 0.05 * (r - 2)
    if r == 25:
        return 7.4
    if r <= 20:
        return 7.0 + 0.1 * (r - 13)
    return 7.8 + 0.05 * (r - 21)


def cbrt_grade(r: int) -> float:
    if r in (0, 1):
        return TRIVIAL_SCORE + 0.5
    if r == 10:
        return 6.5
    if r <= 4:
        return 6.5 + 0.1 * (r - 2)
    return 7.0 + 0.1 * (r - 5)


# ---------------------------------------------------------------------------
# A tiny expression parser for "... = ?" stems
# ---------------------------------------------------------------------------

_TOKEN = re.compile(r'\s*(?:(\d+\.\d+|\.\d+|\d+)|(.))')


@dataclass
class _Val:
    v: Fraction
    kind: str            # 'int', 'dec', 'frac'
    text: str = ''


@dataclass
class _Op:
    kind: str            # '+', '-', '×', '÷' or 'pow'
    grade: float         # the step on its own (with its concept)
    base: float          # the bare arithmetic, concept set aside
    floor: float         # the concept this step brings to a longer sum
    work: float
    regroups: int
    trivial: bool


class _Expr:
    def __init__(self, text: str):
        self.toks = []
        for m in _TOKEN.finditer(text):
            if m.group(1):
                self.toks.append(('num', m.group(1)))
            elif m.group(2) and not m.group(2).isspace():
                self.toks.append(('op', m.group(2)))
        self.i = 0
        self.ops: list[_Op] = []
        self.has_pow = False
        self.has_neg = False
        self.brackets = False
        self.levels: set[str] = set()

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self):
        t = self.peek()
        self.i += 1
        return t

    def parse(self) -> _Val:
        v = self.expr()
        if self.i != len(self.toks):
            raise UnratedQuestion('trailing tokens')
        return v

    def expr(self) -> _Val:
        v = self.term()
        while self.peek() in (('op', '+'), ('op', '-'), ('op', '−')):
            op = '+' if self.take()[1] == '+' else '-'
            r = self.term()
            self.levels.add('add')
            v = self.apply(op, v, r)
        return v

    def term(self) -> _Val:
        v = self.factor()
        while self.peek() in (('op', '×'), ('op', '÷'), ('op', '*')):
            sym = self.take()[1]
            op = '÷' if sym == '÷' else '×'
            r = self.factor()
            self.levels.add('mul')
            v = self.apply(op, v, r)
        return v

    def factor(self) -> _Val:
        base = self.unary()
        t = self.peek()
        if t in (('op', '²'), ('op', '³')):
            self.take()
            return self.power(base, 2 if t[1] == '²' else 3)
        if t == ('op', '^'):
            self.take()
            e = self.unary()
            return self.power(base, int(e.v))
        return base

    def unary(self) -> _Val:
        if self.peek() in (('op', '-'), ('op', '−')):
            self.take()
            v = self.unary()
            self.has_neg = True
            return _Val(-v.v, v.kind, '-' + v.text)
        return self.atom()

    def atom(self) -> _Val:
        t = self.take()
        if t == ('op', '('):
            v = self.expr()
            if self.take() != ('op', ')'):
                raise UnratedQuestion('unbalanced brackets')
            self.brackets = True
            return v
        if t[0] != 'num':
            raise UnratedQuestion(f'unexpected token {t}')
        text = t[1]
        if self.peek() == ('op', '/') and '.' not in text:
            self.take()
            d = self.take()
            if d[0] != 'num':
                raise UnratedQuestion('bad fraction')
            return _Val(Fraction(int(text), int(d[1])), 'frac', f'{text}/{d[1]}')
        if '.' in text:
            return _Val(Fraction(text), 'dec', text)
        return _Val(Fraction(int(text)), 'int', text)

    def power(self, base: _Val, e: int) -> _Val:
        self.has_pow = True
        b = base.v
        if b < 0 or not _is_int(b):
            g = 7.0 + 0.2 * e
            self.has_neg = self.has_neg or b < 0
            self.ops.append(_Op('pow', g, 3.0, g, 1.5 + 0.5 * (e - 1), 0, False))
        else:
            g = power_grade(int(b), e)
            self.ops.append(_Op('pow', g, g, 0.0, power_work(g), 0, e == 1 or b in (0, 1)))
        return _Val(b ** e, base.kind, '')

    def apply(self, op: str, x: _Val, y: _Val) -> _Val:
        kinds = {x.kind, y.kind}
        if op == '÷' and y.v == 0:
            raise UnratedQuestion('division by zero')
        res = {'+': x.v + y.v, '-': x.v - y.v, '×': x.v * y.v, '÷': x.v / y.v if y.v else 0}[op]
        if 'frac' in kinds:
            g, w = frac_op_grade(op, x.v, y.v)
            step = _Op(op, g, 3.0, g, w, 0, False)
            kind = 'frac'
        elif 'dec' in kinds or not _is_int(res):
            g, w = dec_op_grade(op, x.v, y.v, x.text, y.text)
            step = _Op(op, g, 3.0, g, w, 0, False)
            kind = 'dec'
        elif x.v < 0 or y.v < 0 or res < 0:
            self.has_neg = True
            if op in '+-':
                g, w, r = neg_addsub_grade(op, x.v, y.v)
            else:
                g, w, r = sign_mul_grade(op, x.v, y.v)
            step = _Op(op, g, _signed_magnitude(op, x.v, y.v)[0], 0.0, w, r, False)
            kind = 'int'
        else:
            g, w, r = _whole(op, int(x.v), int(y.v))
            step = _Op(op, g, g, 0.0, w, r, _identity(op, x.v, y.v))
            kind = 'int'
        self.ops.append(step)
        return _Val(res, kind, '')


def _rate_expression(text: str) -> tuple[float, int, float, int, bool]:
    e = _Expr(text)
    e.parse()
    if not e.ops:
        raise UnratedQuestion('no operation')
    work = sum(op.work for op in e.ops)
    regroups = sum(op.regroups for op in e.ops)
    if len(e.ops) == 1:
        op = e.ops[0]
        return op.grade, 1, work, regroups, op.trivial
    # Several operations: the order of operations is the concept (its floor),
    # and every step's bare arithmetic adds to the load.
    floor = max(op.floor for op in e.ops)
    if 'add' in e.levels and 'mul' in e.levels or e.brackets:
        floor = max(floor, 5.0)                     # 5.OA.A.1
    if e.has_pow:
        floor = max(floor, 6.0)                     # 6.EE.A.2c
    if e.has_neg:
        floor = max(floor, 7.0)                     # 7.NS.A.3
    bases = [op.base for op in e.ops]
    top = max(bases)
    load = sum(max(0.0, b - 2.5) for b in bases)
    if top > floor:
        score = top + 0.15 * (load - (top - 2.5))
    else:
        score = floor + 0.15 * load
    score += 0.12 * (len(e.ops) - 1)
    work += 0.6 * (len(e.ops) - 1)
    return score, len(e.ops), work, regroups, False


# ---------------------------------------------------------------------------
# The named stem shapes
# ---------------------------------------------------------------------------

_BENCH_PCT = {50: 5.0, 10: 5.1, 1: 5.2, 25: 5.25, 20: 5.35, 5: 5.4, 75: 5.45}


def _pct_base(p: Fraction) -> float:
    if p > 100:
        return 7.0                                  # 7.RP.A.3 (over 100%)
    if not _is_int(p):
        return 7.1                                  # 12.5%, 2.5%, 0.5%
    p = int(p)
    if p in _BENCH_PCT:
        return _BENCH_PCT[p]
    if p % 10 == 0:
        return 6.0                                  # 30%, 40% ... (10% x k)
    if p % 5 == 0:
        return 6.3                                  # 15%, 35% ... (10% + 5%)
    return 6.6                                      # 12%, 4% ... (1% x k)


def _pct_steps(p: Fraction) -> int:
    base = _pct_base(p)
    return 1 if base < 5.5 else 2 if base < 6.2 or p > 100 else 3


def _pct_of_load(p: Fraction, n: int, ans: Fraction) -> float:
    load = 0.15 * max(0, _ndig(n) - 2)
    if n % 10:                                      # 10% of n is not whole
        load += 0.25
    if abs(ans) >= 100:
        load += 0.2
    if not _is_int(ans):
        load += 0.3
    # two pieces to add (35% = 30% + 5%) on a three-digit number
    if _is_int(p) and int(p) % 10 == 5 and int(p) not in (5, 25, 75) and _ndig(n) >= 3:
        load += 0.3
    return load


def _pct_of_work(p: Fraction, n: int, ans: Fraction) -> float:
    w = 1.2 + 1.2 * _pct_steps(p) + 0.4 * max(0, _ndig(n) - 2)
    if abs(ans) >= 100:
        w += 0.5
    if p > 100 or not _is_int(p):
        w += 0.5
    return w


def _rating(kind, score, digits, steps=1, regroups=0, work=1.0, trivial=False) -> Rating:
    return Rating(kind, round(float(score), 3), int(digits), int(steps), int(regroups),
                  round(float(work), 2), bool(trivial))


def _maxdig(*nums) -> int:
    best = 1
    for n in nums:
        try:
            f = Fraction(n)
        except (ValueError, TypeError):
            continue
        for part in (f.numerator, f.denominator):
            best = max(best, _ndig(part))
    return best


_FACTOR_TEST = {2: 0.05, 3: 0.15, 4: 0.15, 5: 0.05, 6: 0.25, 7: 0.4, 8: 0.3,
                9: 0.15, 10: 0.05, 11: 0.35, 12: 0.3}


def _rate_shape(stem: str, answer: str, choices: list[str]) -> Rating | None:
    s = stem.strip()

    m = re.fullmatch(r'Count by (\d+)s: (-?\d+), (-?\d+), (-?\d+), \?', s)
    if m:
        k = int(m.group(1))
        ans = int(m.group(4)) + k
        h = _FACT_H.get(k, 2)
        if k in (2, 5, 10):
            g = 1.3 + min(0.3, 0.004 * ans)
        elif k in (3, 4):
            g = 3.0 + min(0.3, 0.004 * ans)
        else:
            g = 3.2 + min(0.3, 0.004 * ans) + 0.05 * h
        return _rating('skip_count', g, _maxdig(ans), 1, 0, 1.0 + 0.1 * h)

    m = re.fullmatch(r'Double (\d+)\?', s)
    if m:
        n = int(m.group(1))
        g, w, r = add_grade(n, n)
        return _rating('double', g - 0.1 if n > 10 else g, _maxdig(n, 2 * n), 1, r, w)

    m = re.fullmatch(r'Half of (\d+)\?', s)
    if m:
        n = int(m.group(1))
        if n <= 20:
            return _rating('half', 1.5, _maxdig(n), 1, 0, 1.0)
        g, w, r = add_grade(n // 2, n // 2)
        return _rating('half', g + 0.1, _maxdig(n), 1, r, w + 0.3)

    m = re.fullmatch(r'Round (\d+) to nearest (10|100|1000)\?', s)
    if m:
        n, place = int(m.group(1)), int(m.group(2))
        up = (n % place) * 2 >= place
        rounded = place * ((n + place // 2) // place)
        roll = up and (_ndig(rounded) > _ndig(n) or (rounded // place) % 10 == 0)
        g = 3.0 + 0.1 * max(0, _ndig(n) - 2) + (0.1 if up else 0) + (0.15 if roll else 0)
        if _ndig(n) >= 4:
            g = max(g, 4.0)                          # 4.NBT.A.3: any place
        return _rating('round', g, _maxdig(n), 1, int(roll), 1.2 + 0.2 * _ndig(n))

    m = re.fullmatch(r'(\d+) \+ \? = (\d+)', s)
    if m:
        a, c = int(m.group(1)), int(m.group(2))
        g, w, r = add_grade(a, c - a)
        return _rating('missing_number', g + (0.35 if c <= 20 else 0.5), _maxdig(a, c), 1, r, w + 0.5)

    m = re.fullmatch(r'(\d+) - \? = (\d+)', s)
    if m:
        c, a = int(m.group(1)), int(m.group(2))
        g, w, r = sub_grade(c, c - a)
        return _rating('missing_number', g + (0.4 if c <= 20 else 0.5), _maxdig(a, c), 1, r, w + 0.5)

    m = re.fullmatch(r'(?:Which is a factor of|Which number divides) (\d+)(?: evenly)?\?', s)
    if m:
        n = int(m.group(1))
        cands = [int(c) for c in choices if str(c).isdigit()] or [int(answer)]
        tests = sum(_FACTOR_TEST.get(c, 0.4) for c in cands) / len(cands)
        g = 5.4 + 0.5 * max(0, _ndig(n) - 2) + 0.6 * tests
        return _rating('factor_test', g, _maxdig(n), len(cands), 0, 1.0 + 0.8 * len(cands))

    m = re.fullmatch(r'Pyth\. triple: legs (\d+), (\d+)\. Hypotenuse\?', s)
    if m:
        a, b = sorted((int(m.group(1)), int(m.group(2))))
        c = int(answer)
        g = 8.0 + 0.015 * (c - 5) + (0.15 if a * 4 != b * 3 else 0.0)   # not the 3-4-5 family
        return _rating('pythagoras', g, _maxdig(a, b, c), 3, 0, 1.2 + 1.5 * (g - 8.0))

    m = re.fullmatch(r'Pyth\. triple: leg (\d+), hypotenuse (\d+)\. Other leg\?', s)
    if m:
        a, c = int(m.group(1)), int(m.group(2))
        x, y = sorted((a, int(answer)))
        g = 8.3 + 0.015 * (c - 5) + (0.15 if x * 4 != y * 3 else 0.0)
        return _rating('pythagoras', g, _maxdig(a, c), 3, 0, 2.0 + 1.5 * (g - 8.3))

    m = re.fullmatch(r'1\+2\+3\+\.\.\.\+(\d+) = \?', s)
    if m:
        n = int(m.group(1))
        direct = 1.5 + 0.5 * n                       # just add them up
        formula = 7.0 + 0.35 * math.log10(n)         # n(n + 1)/2
        total = n * (n + 1) // 2
        if direct <= formula:
            return _rating('series', direct, _maxdig(total), n - 1, 0, 0.6 * (n - 1))
        return _rating('series', formula, _maxdig(total), 3, 0, 1.5 + 0.5 * _ndig(total))

    m = re.fullmatch(r'What % of (\d+) is (\d+)\?', s)
    if m:
        whole, part = int(m.group(1)), int(m.group(2))
        pct = Fraction(part * 100, whole)
        bench = pct in (10, 20, 25, 50, 75)
        g = (7.0 if pct > 100 else 6.0) + (0.0 if bench else 0.2) + 0.15 * max(0, _ndig(whole) - 2)
        w = 2.6 + (0.0 if bench else 0.6) + 0.3 * max(0, _ndig(whole) - 2)
        return _rating('find_percent', g, _maxdig(whole, part), 2, 0, w)

    m = re.fullmatch(r'From (\d+) to (\d+): % (increase|decrease)\?', s)
    if m:
        old, new = int(m.group(1)), int(m.group(2))
        pct = Fraction(abs(new - old) * 100, old)
        bench = pct in (10, 20, 25, 50, 75)
        dec = m.group(3) == 'decrease'
        g = 7.0 + (0.2 if dec else 0.0) + (0.0 if bench else 0.15) + 0.1 * max(0, _ndig(old) - 2)
        w = 3.4 + (0.0 if bench else 0.6) + (0.3 if dec else 0.0) + 0.3 * max(0, _ndig(old) - 2)
        return _rating('percent_change', g, _maxdig(old, new), 3, 0, w)

    m = re.fullmatch(r'(Increase|Decrease) (\d+) by (\d+(?:\.\d+)?)%\?', s)
    if m:
        n, p = int(m.group(2)), Fraction(m.group(3))
        ans = n * (100 + p if m.group(1) == 'Increase' else 100 - p) / 100
        base = 7.2 + (0.1 if m.group(1) == 'Decrease' else 0.0)
        g = base + max(0.0, _pct_base(p) - 5.0) * 0.4 + _pct_of_load(p, n, ans)
        return _rating('percent_change', g, _maxdig(n, ans), 3, 0, _pct_of_work(p, n, ans) + 1.0)

    m = re.fullmatch(r'(\d+(?:\.\d+)?)% of (\d+)\?', s)
    if m:
        p, n = Fraction(m.group(1)), int(m.group(2))
        ans = p * n / 100
        g = _pct_base(p) + _pct_of_load(p, n, ans)
        return _rating('percent_of', g, _maxdig(n, ans), _pct_steps(p), 0, _pct_of_work(p, n, ans))

    m = re.fullmatch(r'(\d+)/(\d+) as a percent\?', s)
    if m:
        return _rate_fdp(int(m.group(2)), int(m.group(1)) != 1, 'to_percent')

    m = re.fullmatch(r'(\d*\.\d+) as a percent\?', s)
    if m:
        dp = len(m.group(1).split('.')[1])
        return _rating('fdp_shift', 4.8 + 0.1 * (dp - 1), _maxdig(answer.rstrip('%')), 1, 0, 1.2)

    m = re.fullmatch(r'(\d+(?:\.\d+)?)% as a decimal\?', s)
    if m:
        dp = len(answer.split('.')[1]) if '.' in answer else 0
        return _rating('fdp_shift', 4.8 + 0.1 * max(0, dp - 1), _maxdig(m.group(1)), 1, 0, 1.2)

    m = re.fullmatch(r'(\d+)/(\d+) as (?:a )?decimal\?', s)
    if m:
        return _rate_fdp(int(m.group(2)), int(m.group(1)) != 1, 'to_decimal')

    m = re.fullmatch(r'(\d+):(\d+) simplified\?', s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        gcd = math.gcd(a, b)
        odd_gcd = gcd not in (2, 5, 10)
        g = 5.0 + (0.2 if odd_gcd else 0.0) + 0.15 * (_ndig(max(a, b)) - 1) + (0.1 if a // gcd != 1 else 0.0)
        return _rating('ratio', g, _maxdig(a, b), 2, 0, 2.2 + (0.4 if odd_gcd else 0.0))

    m = re.fullmatch(r'(\d+)/(\d+) of (\d+)/(\d+) of (\d+) = \?', s)
    if m:
        p1, q1, p2, q2, n = map(int, m.groups())
        first = Fraction(p2, q2) * n
        l1, w1 = _frac_of(p2, q2, n)
        l2, w2 = _frac_of(p1, q1, int(first)) if _is_int(first) else (1.0, 3.0)
        return _rating('fraction_of', 5.8 + 0.3 * (l1 + l2), _maxdig(n), 4, 0, 1.5 + w1 + w2)

    m = re.fullmatch(r'(\d+)/(\d+) (?:of|×) (\d+)(?: = )?\??', s)
    if m:
        p, q, n = map(int, m.groups())
        load, w = _frac_of(p, q, n)
        return _rating('fraction_of', 4.6 + load, _maxdig(n, p * n // q), 1 if p == 1 else 2, 0, 1.2 + w)

    m = re.fullmatch(r'(\d+)\^(\d+) ([×÷]) (\d+)\^(\d+) = \?', s)
    if m and m.group(1) == m.group(4):
        return _rate_exponent_rule(int(m.group(1)), int(m.group(2)), m.group(3), int(m.group(5)), answer)

    m = re.fullmatch(r'(\d+)(?:²| squared) = \?', s)
    if m:
        b = int(m.group(1))
        g = power_grade(b, 2)
        return _rating('power', g, _maxdig(b * b), 1, 0, power_work(g), b in (0, 1))

    m = re.fullmatch(r'(\d+)(?:³| cubed) = \?', s)
    if m:
        b = int(m.group(1))
        g = power_grade(b, 3)
        return _rating('power', g, _maxdig(b ** 3), 2, 0, power_work(g), b in (0, 1))

    m = re.fullmatch(r'(\d+)\^(\d+) = \?', s)
    if m:
        b, e = int(m.group(1)), int(m.group(2))
        g = power_grade(b, e)
        return _rating('power', g, _maxdig(b ** e), max(1, e - 1), 0, power_work(g), e == 1 or b in (0, 1))

    m = re.fullmatch(r'√(\d+) = \?', s)
    if m:
        r = int(answer)
        g = sqrt_grade(r)
        return _rating('root', g, _maxdig(m.group(1)), 1, 0, 1.1 + 0.6 * max(0.0, g - 6.0), r in (0, 1))

    m = re.fullmatch(r'Cube root of (\d+) = \?', s)
    if m:
        r = int(answer)
        g = cbrt_grade(r)
        return _rating('root', g, _maxdig(m.group(1)), 1, 0, 1.3 + 0.6 * max(0.0, g - 6.5), r in (0, 1))

    m = re.fullmatch(r'Solve: (.+)', s)
    if m:
        return _rate_equation(m.group(1), answer)

    return None


def _frac_of(p: int, q: int, n: int) -> tuple[float, float]:
    """(grade above the 4.6 floor, work) for p/q of n."""
    share = Fraction(n, q)
    if not _is_int(share):
        return 1.0, 3.0
    g_div, w_div, _ = div_grade(n, q)
    load = 0.5 * max(0.0, g_div - 3.2)
    work = w_div
    if p != 1:
        g_mul, w_mul, _ = mul_grade(int(share), p)
        load += 0.4 + 0.5 * max(0.0, g_mul - 3.0)
        work += w_mul + 0.5
    return load, work


def _rate_fdp(q: int, nonunit: bool, kind: str) -> Rating:
    if q in (2, 4, 5, 10, 20, 25, 50, 100):
        g = 5.1 + (0.1 if nonunit else 0.0) + (0.1 if q in (20, 25, 50) else 0.0)
        if kind == 'to_decimal':
            g -= 0.1
        w = 1.4
    elif q == 8:
        g, w = 6.0 + (0.1 if nonunit else 0.0), 2.0
    elif q == 3:
        g, w = 6.4 + (0.1 if nonunit else 0.0), 2.0
    else:                                            # 6, 9, 12, 7, 11: repeating
        g, w = 7.0 + (0.1 if q > 6 else 0.0) + (0.1 if nonunit else 0.0), 2.6
    return _rating('fdp_convert', g, _ndig(q), 1 if q in (2, 4, 5, 10) else 2, 0, w)


def _rate_exponent_rule(b: int, m: int, op: str, n: int, answer: str) -> Rating:
    """b^m x b^n or b^m / b^n (8.EE.A.1). Where one exponent is 1 the rule is
    not needed (it is one more multiplication); where the result is past the
    memorised ladders (3^7, 7^5 ...) it is no longer mental work."""
    k = m + n if op == '×' else m - n
    pg = power_grade(b, k) if k >= 2 else 3.0
    rule = 7.2 + 0.55 * max(0.0, pg - 4.2)
    if pg > LADDER_TOP:
        rule += 0.5
    if op == '×':
        direct = power_grade(b, k) + 0.3 if min(m, n) == 1 else 99.0
    else:
        direct = power_grade(b, m) + 0.4 if n == 1 else 99.0
    g = min(rule, direct)
    return _rating('exponent_rule', g, _maxdig(answer), 2, 0, 1.0 + 0.8 * max(0.0, pg - 3.2))


def _rate_equation(eq: str, answer: str) -> Rating:
    x = Fraction(answer)
    neg = x < 0
    m = re.fullmatch(r'(\d+)x = (-?\d+)', eq)
    if m:
        k, c = int(m.group(1)), int(m.group(2))
        g, w, _ = div_grade(abs(c), k)
        return _eq_rating(6.0 + 0.35 * max(0.0, g - 3.2), neg, 1, _maxdig(k, c, x), w)
    m = re.fullmatch(r'x \+ (\d+) = (-?\d+)', eq)
    if m:
        b, c = int(m.group(1)), int(m.group(2))
        g, w, _ = sub_grade(max(c, b), min(c, b)) if c >= 0 else add_grade(-c, b)
        return _eq_rating(6.0 + 0.3 * max(0.0, g - 1.5), neg, 1, _maxdig(b, c, x), w)
    m = re.fullmatch(r'x - (\d+) = (-?\d+)', eq)
    if m:
        b, c = int(m.group(1)), int(m.group(2))
        g, w, _ = add_grade(c, b) if c >= 0 else sub_grade(max(-c, b), min(-c, b))
        return _eq_rating(6.0 + 0.3 * max(0.0, g - 1.5), neg, 1, _maxdig(b, c, x), w)
    m = re.fullmatch(r'x/(\d+) = (-?\d+)', eq)
    if m:
        k, c = int(m.group(1)), int(m.group(2))
        g, w, _ = mul_grade(abs(c), k)
        return _eq_rating(6.1 + 0.35 * max(0.0, g - 3.0), neg, 1, _maxdig(k, c, x), w)
    m = re.fullmatch(r'(\d+)x ([+-]) (\d+) = (-?\d+)', eq)
    if m:
        k, sign, b, c = int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4))
        inner = c - b if sign == '+' else c + b
        # the first step on the magnitudes (c - b, or c + b), signs set aside
        if sign == '+':
            g1, w1, _ = sub_grade(max(c, b), min(c, b)) if c >= 0 else add_grade(-c, b)
        else:
            g1, w1, _ = add_grade(c, b) if c >= 0 else sub_grade(max(-c, b), min(-c, b))
        if inner and abs(inner) % k == 0:
            g2, w2, _ = div_grade(abs(inner), k)
        else:
            g2, w2 = 2.0, 0.5
        g = 7.0 + 0.3 * max(0.0, g1 - 1.5) + 0.3 * max(0.0, g2 - 3.2)
        return _eq_rating(g, neg or inner < 0, 2, _maxdig(k, b, c, x), w1 + w2)
    m = re.fullmatch(r'(\d+)\(x ([+-]) (\d+)\) = (-?\d+)', eq)
    if m:
        k, b, c = int(m.group(1)), int(m.group(3)), int(m.group(4))
        if c and c % k == 0:
            g1, w1, _ = div_grade(abs(c), k)
        else:
            g1, w1 = 4.0, 2.5
        g = 7.2 + 0.3 * max(0.0, g1 - 3.2) + 0.1 * (_ndig(c) - 1)
        return _eq_rating(g, neg, 2, _maxdig(k, b, c, x), w1 + 1.0)
    raise UnratedQuestion(f'unknown equation shape {eq!r}')


def _eq_rating(g: float, neg: bool, steps: int, digits: int, arithmetic: float) -> Rating:
    work = 0.8 * steps + arithmetic
    if neg:
        g = max(g, 7.0) + 0.2                        # a negative solution (7.NS + 7.EE)
        work += 0.6
    return _rating('equation', g, digits, steps, 0, work)


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

def rate(q: dict) -> Rating:
    """Rate one maths question (a bank dict with question / answer / choices)."""
    stem = str(q['question'])
    answer = str(q.get('answer', ''))
    choices = [str(c) for c in q.get('choices', [])]
    r = _rate_shape(stem, answer, choices)
    if r is not None:
        return r
    m = re.fullmatch(r'(.+?) = \?', stem.strip())
    if not m:
        raise UnratedQuestion(f'unknown stem shape {stem!r}')
    score, steps, work, regroups, trivial = _rate_expression(m.group(1))
    nums = re.findall(r'\d+(?:\.\d+)?', stem) + re.findall(r'\d+', answer)
    digits = max((len(n.split('.')[0]) for n in nums), default=1)
    if steps > 1:
        kind = 'order_of_ops'
    elif '/' in stem:
        kind = 'fraction_op'
    elif '.' in stem:
        kind = 'decimal_op'
    elif re.search(r'(^|[(×÷ ])-\d', stem) or answer.startswith('-'):
        kind = 'negatives'
    else:
        kind = 'arithmetic'
    return _rating(kind, score, digits, steps, regroups, work, trivial)


def score(q: dict) -> float:
    return rate(q).score


# ---------------------------------------------------------------------------
# The right answer, worked out from the stem (every shape the scorer knows)
# ---------------------------------------------------------------------------

def _dec_str(v: Fraction, places: int = 3) -> str:
    from decimal import ROUND_HALF_UP, Decimal
    d = (Decimal(v.numerator) / Decimal(v.denominator)).quantize(
        Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    s = format(d, 'f')
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s


def _pct_str(v: Fraction) -> str:
    return f'{v.numerator}%' if _is_int(v) else f'{_dec_str(v, 1)}%'


def _plain(v: Fraction) -> str:
    if _is_int(v):
        return str(v.numerator)
    if 10 ** 6 % v.denominator == 0:            # a terminating decimal
        return _dec_str(v, 6)
    return f'{v.numerator}/{v.denominator}'


def _eval_expression(text: str) -> Fraction:
    e = _Expr(text)
    return e.parse().v


def expected_answer(q: dict) -> str | None:
    """The key a question should have, worked out from its stem with exact
    fractions; None for 'which divides' (several shapes of right answer are
    checked by ``check_answer``)."""
    s = str(q['question']).strip()
    m = re.fullmatch(r'Count by (\d+)s: (-?\d+), (-?\d+), (-?\d+), \?', s)
    if m:
        return str(int(m.group(4)) + int(m.group(1)))
    m = re.fullmatch(r'Double (\d+)\?', s)
    if m:
        return str(2 * int(m.group(1)))
    m = re.fullmatch(r'Half of (\d+)\?', s)
    if m:
        return _plain(Fraction(int(m.group(1)), 2))
    m = re.fullmatch(r'Round (\d+) to nearest (10|100|1000)\?', s)
    if m:
        n, p = int(m.group(1)), int(m.group(2))
        return str(p * ((n + p // 2) // p))
    m = re.fullmatch(r'(\d+) \+ \? = (\d+)', s)
    if m:
        return str(int(m.group(2)) - int(m.group(1)))
    m = re.fullmatch(r'(\d+) - \? = (\d+)', s)
    if m:
        return str(int(m.group(1)) - int(m.group(2)))
    if re.fullmatch(r'(?:Which is a factor of|Which number divides) (\d+)(?: evenly)?\?', s):
        return None
    m = re.fullmatch(r'Pyth\. triple: legs (\d+), (\d+)\. Hypotenuse\?', s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        c = math.isqrt(a * a + b * b)
        return str(c) if c * c == a * a + b * b else 'not a triple'
    m = re.fullmatch(r'Pyth\. triple: leg (\d+), hypotenuse (\d+)\. Other leg\?', s)
    if m:
        a, c = int(m.group(1)), int(m.group(2))
        b = math.isqrt(c * c - a * a)
        return str(b) if b * b == c * c - a * a else 'not a triple'
    m = re.fullmatch(r'1\+2\+3\+\.\.\.\+(\d+) = \?', s)
    if m:
        n = int(m.group(1))
        return str(n * (n + 1) // 2)
    m = re.fullmatch(r'What % of (\d+) is (\d+)\?', s)
    if m:
        return _plain(Fraction(int(m.group(2)) * 100, int(m.group(1))))
    m = re.fullmatch(r'From (\d+) to (\d+): % (increase|decrease)\?', s)
    if m:
        old, new = int(m.group(1)), int(m.group(2))
        if (m.group(3) == 'increase') != (new > old):
            return 'wrong direction'
        return _plain(Fraction(abs(new - old) * 100, old))
    m = re.fullmatch(r'(Increase|Decrease) (\d+) by (\d+(?:\.\d+)?)%\?', s)
    if m:
        n, p = int(m.group(2)), Fraction(m.group(3))
        return _plain(n * (100 + p if m.group(1) == 'Increase' else 100 - p) / 100)
    m = re.fullmatch(r'(\d+(?:\.\d+)?)% of (\d+)\?', s)
    if m:
        return _plain(Fraction(m.group(1)) * int(m.group(2)) / 100)
    m = re.fullmatch(r'(\d+)/(\d+) as a percent\?', s)
    if m:
        return _pct_str(Fraction(int(m.group(1)) * 100, int(m.group(2))))
    m = re.fullmatch(r'(\d*\.\d+) as a percent\?', s)
    if m:
        return _pct_str(Fraction(m.group(1)) * 100)
    m = re.fullmatch(r'(\d+(?:\.\d+)?)% as a decimal\?', s)
    if m:
        return _dec_str(Fraction(m.group(1)) / 100)
    m = re.fullmatch(r'(\d+)/(\d+) as (?:a )?decimal\?', s)
    if m:
        return _dec_str(Fraction(int(m.group(1)), int(m.group(2))))
    m = re.fullmatch(r'(\d+):(\d+) simplified\?', s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        g = math.gcd(a, b)
        return f'{a // g}:{b // g}'
    m = re.fullmatch(r'(\d+)/(\d+) of (\d+)/(\d+) of (\d+) = \?', s)
    if m:
        p1, q1, p2, q2, n = map(int, m.groups())
        return _plain(Fraction(p1, q1) * Fraction(p2, q2) * n)
    m = re.fullmatch(r'(\d+)/(\d+) (?:of|×) (\d+)(?: = )?\??', s)
    if m:
        p, qq, n = map(int, m.groups())
        return _plain(Fraction(p, qq) * n)
    m = re.fullmatch(r'(\d+)(?:²| squared) = \?', s)
    if m:
        return str(int(m.group(1)) ** 2)
    m = re.fullmatch(r'(\d+)(?:³| cubed) = \?', s)
    if m:
        return str(int(m.group(1)) ** 3)
    m = re.fullmatch(r'√(\d+) = \?', s)
    if m:
        n = int(m.group(1))
        r = math.isqrt(n)
        return str(r) if r * r == n else 'not a square'
    m = re.fullmatch(r'Cube root of (\d+) = \?', s)
    if m:
        n = int(m.group(1))
        r = round(n ** (1 / 3))
        return str(r) if r ** 3 == n else 'not a cube'
    m = re.fullmatch(r'Solve: (.+)', s)
    if m:
        return _solve(m.group(1))
    m = re.fullmatch(r'(.+?) = \?', s)
    if m:
        v = _eval_expression(m.group(1))
        if '/' in s and not _is_int(v):                 # fraction sums keep fraction keys
            return f'{v.numerator}/{v.denominator}'
        return _plain(v)
    raise UnratedQuestion(f'unknown stem shape {s!r}')


def _solve(eq: str) -> str:
    """Solve a linear equation in x: the left side is a x + b."""
    lhs, rhs = (side.strip() for side in eq.split('='))
    c = Fraction(rhs)
    m = re.fullmatch(r'(\d+)\(x ([+-]) (\d+)\)', lhs)
    if m:
        k, b = int(m.group(1)), int(m.group(3)) * (1 if m.group(2) == '+' else -1)
        return _plain(c / k - b)
    m = re.fullmatch(r'x/(\d+)', lhs)
    if m:
        return _plain(c * int(m.group(1)))
    m = re.fullmatch(r'(\d*)x(?: ([+-]) (\d+))?', lhs)
    if m:
        k = int(m.group(1) or 1)
        b = int(m.group(3) or 0) * (1 if m.group(2) != '-' else -1)
        return _plain((c - b) / k)
    raise UnratedQuestion(f'unknown equation shape {eq!r}')


def check_answer(q: dict) -> str | None:
    """None when the key is right and no other choice is also right;
    otherwise a short reason."""
    choices = [str(c) for c in q.get('choices', [])]
    if q['answer'] not in choices or len(set(choices)) != len(choices):
        return 'the key is not one of four different choices'
    m = re.fullmatch(r'(?:Which is a factor of|Which number divides) (\d+)(?: evenly)?\?',
                     str(q['question']).strip())
    if m:
        n = int(m.group(1))
        right = [c for c in choices if c.isdigit() and n % int(c) == 0]
        return None if right == [q['answer']] else f'divisors among the choices: {right}'
    want = expected_answer(q)
    if want != q['answer']:
        return f'expected {want!r}, key is {q["answer"]!r}'
    try:
        key = Fraction(want.rstrip('%').replace(':', '/'))
    except (ValueError, ZeroDivisionError):
        return None
    for c in choices:
        if c == q['answer']:
            continue
        try:
            if Fraction(c.rstrip('%').replace(':', '/')) == key:
                return f'choice {c!r} has the same value as the key'
        except (ValueError, ZeroDivisionError):
            continue
    return None


# ---------------------------------------------------------------------------
# A rough answer-time model (for the simulator's practice curve)
# ---------------------------------------------------------------------------

READ_AND_PICK_S = 0.9        # read a one-line stem, find the key among 4, press it
SECONDS_PER_WORK = 0.6       # one fluent mental operation, practised 10-14 year-old
FIRST_TIME_FACTOR = 1.5      # a first-timer is about half again as slow


def practised_seconds(r: Rating) -> float:
    """Median answer time for a practised 10-14 year-old (a model, not a
    measurement; see docs/quiz/math_grade_curve.md)."""
    return READ_AND_PICK_S + SECONDS_PER_WORK * r.work
