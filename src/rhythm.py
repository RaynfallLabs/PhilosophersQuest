"""The Mooble's dance, scored: a pure module (no pygame, no Game).

The dance screen (game_mooble_dance.py) only draws and reads keys; every
judgement is made here, from real elapsed time in milliseconds, never from
turns or frames:

  * ``timeline`` lays the dance out on the beat: a count-in, then his phrase
    (the CALL: he dances the steps), then the same phrase again for the hero
    to echo (the RESPONSE). Every step has the time it is due.
  * ``judge`` takes the steps due in the response and the keys the hero
    pressed (each a time and a direction) and grades every step Perfect,
    Good or Miss. It reads the beat SCHEDULE, so a slow frame never steals
    a beat: a step is due when the schedule says, whatever the screen did.
  * ``passed`` is the pass mark (data/mooble.json ``dance``): a share of the
    steps hit, and no more than so many misses.
  * ``score`` and ``band`` turn a result into a strength: the share of the
    steps hit, Perfects worth extra and strays costing some, then the
    highest band of a written table that score reaches (the Mooble's Dance
    of the Dark: how many foes, how long, how far).

Nothing here knows about the Mooble: a phrase is any list of steps, and a
dance may have a CALL to echo (the Mooble's visits) or none (a count-in, then
the steps lit as they come: his special). Another dance-off (several rounds
of Simon-says) can lay out each round with ``timeline`` and judge it with
``judge``.

How a key is matched to a step: keys are taken in the order pressed. A key
belongs to the nearest step not yet decided whose time is within
``attach_ms`` of it (half a beat: closer to this step than to its
neighbours). The first key a step gets decides it: the right arrow within
``good_ms`` is a hit (within ``perfect_ms`` a Perfect), anything else a Miss
(too early, too late or the wrong arrow). A key that belongs to no step is a
stray, and a stray counts as a miss: mashing every arrow never wins. A step
no key reached is a Miss once its window has passed.
"""
from __future__ import annotations

import math

DIRS = ('left', 'right', 'up', 'down')

PERFECT = 'perfect'
GOOD = 'good'
MISS = 'miss'
PENDING = 'pending'


def beat_ms(bpm: float) -> float:
    """One beat, in milliseconds."""
    return 60000.0 / max(1.0, float(bpm))


def phrase(steps) -> list:
    """A written phrase as [(beat, direction)], in beat order. ``steps`` is
    [[beat, dir], ...] from the data (a beat counts from 0 at the bar's
    first beat; halves are allowed)."""
    out = []
    for s in steps or ():
        b, d = float(s[0]), str(s[1]).lower()
        if d not in DIRS:
            raise ValueError(f'not a dance step: {d!r}')
        out.append((b, d))
    out.sort(key=lambda s: s[0])
    return out


def timeline(steps, bpm: float, lead_beats: int = 4, phrase_beats: int = 8,
             call: bool = True) -> dict:
    """The dance laid out in ms from its start: ``lead_beats`` of count-in,
    then the CALL (``phrase_beats`` beats: he dances the steps), then the
    RESPONSE (the same beats: the hero echoes them). With ``call`` False
    there is no call: the response follows the count-in at once (the steps
    are danced as they light up).

    Returns {'beat_ms', 'lead', 'phrase_beats', 'call': [(t, dir)] (empty
    with no call), 'response': [(t, dir)], 'call_start', 'response_start',
    'response_end', 'beats': total beats, 'has_call'}."""
    ph = phrase(steps)
    bm = beat_ms(bpm)
    lead = int(lead_beats)
    pb = int(phrase_beats)
    calls = 1 if call else 0
    call_start = lead * bm
    resp_start = (lead + calls * pb) * bm
    return {
        'beat_ms': bm, 'lead': lead, 'phrase_beats': pb, 'has_call': bool(call),
        'call': [(call_start + b * bm, d) for b, d in ph] if call else [],
        'response': [(resp_start + b * bm, d) for b, d in ph],
        'call_start': call_start, 'response_start': resp_start,
        'response_end': (lead + (calls + 1) * pb) * bm,
        'beats': lead + (calls + 1) * pb,
    }


def attach_window(beat: float, good_ms: float) -> float:
    """How far from a step a key still belongs to it: half a beat, and never
    less than the Good window."""
    return max(float(good_ms), float(beat) / 2.0)


def judge(expected, presses, *, good_ms: float = 150, perfect_ms: float = 50,
          attach_ms: float | None = None, now_ms: float | None = None,
          stray_is_miss: bool = True) -> dict:
    """Grade the hero's keys against the steps due.

    ``expected``: [(t_ms, dir)] the steps due (the response). ``presses``:
    [(t_ms, dir)] the keys pressed, on the same clock. ``now_ms``: the time
    now (a step still inside its window is 'pending'); None when the dance
    is over (every step is decided).

    Returns {'steps': [{'t', 'dir', 'grade', 'offset', 'why'}], 'hits',
    'perfects', 'goods', 'missed_steps', 'strays', 'misses', 'total'}.
    ``offset`` is the key's time minus the step's (negative: early); ``why``
    for a Miss is 'early', 'late', 'wrong' or 'none' (no key)."""
    good = float(good_ms)
    perfect = min(float(perfect_ms), good)
    exp = sorted(((float(t), str(d)) for t, d in expected or ()), key=lambda e: e[0])
    if attach_ms is None:
        gaps = [b[0] - a[0] for a, b in zip(exp, exp[1:]) if b[0] > a[0]]
        attach_ms = attach_window(min(gaps) if gaps else 2 * good, good)
    attach = max(good, float(attach_ms))
    steps = [{'t': t, 'dir': d, 'grade': PENDING, 'offset': None, 'why': None} for t, d in exp]
    strays = 0
    for pt, pd in sorted(((float(t), str(d)) for t, d in presses or ()), key=lambda p: p[0]):
        open_steps = [s for s in steps if s['grade'] == PENDING and abs(pt - s['t']) <= attach]
        if not open_steps:
            strays += 1
            continue
        s = min(open_steps, key=lambda s: (abs(pt - s['t']), s['t']))
        off = pt - s['t']
        s['offset'] = off
        if pd != s['dir']:
            s['grade'], s['why'] = MISS, 'wrong'
        elif abs(off) <= perfect:
            s['grade'] = PERFECT
        elif abs(off) <= good:
            s['grade'] = GOOD
        else:
            s['grade'], s['why'] = MISS, ('early' if off < 0 else 'late')
    for s in steps:
        if s['grade'] == PENDING and (now_ms is None or float(now_ms) > s['t'] + good):
            s['grade'], s['why'] = MISS, 'none'
    perfects = sum(1 for s in steps if s['grade'] == PERFECT)
    goods = sum(1 for s in steps if s['grade'] == GOOD)
    missed = sum(1 for s in steps if s['grade'] == MISS)
    return {
        'steps': steps, 'hits': perfects + goods, 'perfects': perfects, 'goods': goods,
        'missed_steps': missed, 'strays': strays,
        'misses': missed + (strays if stray_is_miss else 0), 'total': len(steps),
    }


def hits_needed(total: int, pass_share: float) -> int:
    """The steps a pass needs: ``pass_share`` of them, rounded up."""
    return int(math.ceil(float(pass_share) * int(total) - 1e-9))


def passed(result: dict, pass_share: float = 0.75, max_misses: int = 2) -> bool:
    """Did the hero win? At least ``pass_share`` of the steps hit and no
    more than ``max_misses`` misses (a stray key counts as a miss)."""
    return (result['hits'] >= hits_needed(result['total'], pass_share)
            and result['misses'] <= int(max_misses))


def score(result: dict, perfect_worth: float = 1.0, stray_cost: float = 0.0) -> float:
    """How well a dance went, as one number: the steps hit over the steps
    due, a Perfect counting ``perfect_worth`` (more than a Good's 1), each
    stray key taking ``stray_cost`` off. 0 for nothing hit; 1 for every step
    Good; more with Perfects."""
    total = max(1, int(result.get('total', 0) or 0))
    v = (float(result.get('goods', 0)) + float(perfect_worth) * float(result.get('perfects', 0))
         - float(stray_cost) * float(result.get('strays', 0)))
    return max(0.0, v / total)


def band(value: float, bands, key: str = 'min_score') -> dict:
    """The highest band of ``bands`` (each a dict with ``key``) that
    ``value`` reaches; the lowest band when it reaches none."""
    ordered = sorted(bands or (), key=lambda b: float(b.get(key, 0)))
    if not ordered:
        return {}
    got = ordered[0]
    for b in ordered:
        if float(value) + 1e-9 >= float(b.get(key, 0)):
            got = b
    return got


def on_time(expected) -> list:
    """Every step pressed exactly on its time: [(t, dir)] (for tests and the
    QA hero)."""
    return [(float(t), str(d)) for t, d in expected]
