"""Magic written for the real hero: the simulator's measurement knobs
(2026-11-21; LATE_GAME_PLAN_2026_11_21.md, change 6).

Why magic earned nothing (measured with a probe on floors 25-85):
  * a tier's best spell was written to land ONE floor_curve.one_attack, the
    blow of an ordinary kid before any levelling, but the careful kid's blow is
    3 to 5 times that, so a spell was half a sword blow to one;
  * a point of INT adds 1.5% to a spell (at most +40%, reached at INT 37), a
    point of STR 3% to the sword with no cap;
  * max MP is 10 + INT, so a deep spell (15 to 22 MP) is one or two a bar;
  * the Smite family says "holy fire" but deals plain damage;
  * the simulator cast only damage, healing, haste and slow.

Each knob here is a rule for every spell, and each defaults to the game as it
is, so a default run is the simulator as it was (tests/test_sim_magic.py):

  mg_int_per   what a point of INT over 10 adds to a spell's dice (the game:
               game_magic.INT_DAMAGE_PER_POINT, 0.015); M1 is 0.03, as STR.
  mg_int_cap   the most INT's step reaches (the game: INT_DAMAGE_CAP, 1.4);
               M1 has none (99).
  mg_anchor    0 = off. M2: a spell tier's damage is written against the
               careful kid's real blow, by spell tier (never by floor):
               game_magic.MAGIC_TIER_MULT[tier] x anchor x (the careful blow
               at the tier's floor / one_attack there; the careful blow is
               sim_late_blow.json's, the tier floors magic_audit.TIER_FLOOR).
               A stand-in for writing MAGIC_TIER_MULT again: measurement only.
  mg_holy      M3: the Smite family (effect 'smite') deals holy and ignores
               resistance, as its own comment in game_magic says it should.
  mg_mp_int    M4: max MP is BASE_MP + mg_mp_int x INT (the game: 1).
  mg_escape    M5: Blink and Teleport (effect teleport_self) are a sure way out
               of a losing fight; Phase Door (phase_self) a way out as from
               slow foes. One science question; the MP goes either way.
  mg_hold      M5: sleep and hold on the ordinary foes of a group, through the
               game's own handlers (game_magic._cast_spell_effect: a blow wakes
               a sleeper, a hold lasts through blows, nature and big foes
               refuse); the hero strikes the ones awake first.
  mg_bigfoe    with mg_hold: the "big foe" test (game_magic._is_big_foe,
               twice an ordinary floor's HP) reads a kind's health before the
               HP stand-in raised it. Under A+ every deep ordinary monster would
               otherwise count as a big foe and throw off a hold half the time,
               which the real health pass would fix with the test's yardstick.

The same old yardstick sized two more things, and the holistic pass moves
them with the rest (each a stand-in for writing its data again, by its own
level or depth, never by the floor it is met on):
  mg_pet_anchor    0 = off. A pet's bite (data/pet_growth.json, first written
                   as a quarter of one_attack at the matching depth) x anchor x
                   (the careful blow / one_attack) at its level; the simulator's
                   pet is level = floor, so the factor is read there.
  mg_flask_anchor  0 = off. A thrown flask's damage (data/arsenal.json, half of
                   one_attack at its 'sized_at' depth) x anchor x (the careful
                   blow / one_attack) at that depth, through coatings.thrown_damage.

What is still not modelled: Teleport Away, invisibility, levitation,
sanctuary, mapping, the world-shaping spells (there are none yet), wands
beyond the MONSTERS AND MAGIC block.
"""
from __future__ import annotations

import json
import math
import os
import random

KNOBS = {
    'mg_int_per': 0.015,
    'mg_int_cap': 1.4,
    'mg_anchor': 0.0,
    'mg_holy': 0,
    'mg_mp_int': 1,
    'mg_escape': 0,
    'mg_hold': 0,
    'mg_bigfoe': 1,
    'mg_pet_anchor': 0.0,
    'mg_flask_anchor': 0.0,
}

_HERE = os.path.dirname(os.path.abspath(__file__))
TIER_FLOOR = {1: 10, 2: 30, 3: 50, 4: 70, 5: 90}        # magic_audit.TIER_FLOOR
ESCAPE_EFFECTS = ('teleport_self', 'phase_self')
# The hold spells this module casts (effect -> single target or the room).
HOLD_EFFECTS = {'sleep_monster': 'one', 'paralyze_monster': 'one', 'sleep_area': 'near',
                'mass_sleep': 'room', 'mass_slow': 'room'}
HELD = ('sleeping', 'paralyzed', 'stunned', 'frozen')
_ANCHOR = {}


def k(run, name):
    return run.knobs.get(name, KNOBS[name])


def _fs(run, key, n=1):
    run.fs[key] = run.fs.get(key, 0) + n


# ---------------------------------------------------------------- M1, M2, M3
def int_factor(run) -> float:
    """game_magic.int_damage_factor with this run's M1 knobs."""
    step = 1.0 + (int(run.p.INT) - 10) * float(k(run, 'mg_int_per'))
    return 2.0 * max(0.7, min(float(k(run, 'mg_int_cap')), step))


def _careful_blow(floor: float) -> float:
    """sim_late_blow.json's landed blow, between band middles (log)."""
    with open(os.path.join(_HERE, 'sim_late_blow.json'), encoding='utf-8') as f:
        bands = json.load(f)['bands']
    pts = [((b['lo'] + b['hi']) / 2.0, float(b['landed_mean'])) for b in bands]
    if floor <= pts[0][0]:
        return pts[0][1]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if a <= floor <= b:
            t = (floor - a) / (b - a)
            return math.exp(math.log(va) * (1 - t) + math.log(vb) * t)
    return pts[-1][1]


def anchor_table() -> dict:
    """tier -> the careful blow at the tier's floor / one_attack there."""
    if not _ANCHOR:
        import floor_curve
        for t, fl in TIER_FLOOR.items():
            _ANCHOR[t] = _careful_blow(fl) / floor_curve.one_attack(fl)
    return _ANCHOR


def tier_mult(run, tier: int) -> float:
    import game_magic
    m = game_magic.MAGIC_TIER_MULT.get(int(tier), 1.0)
    a = float(k(run, 'mg_anchor') or 0)
    if a > 0:
        m *= a * anchor_table().get(int(tier), 1.0)
    return m


def element(run, fx, el):
    if fx == 'smite' and k(run, 'mg_holy'):
        return 'holy'
    return el


def ignores_resistance(run, fx) -> bool:
    return fx == 'smite' and bool(k(run, 'mg_holy'))


# ---------------------------------------------------------------------- M4
def sync_mp(run) -> None:
    """Max MP = what the game made it + (mg_mp_int - 1) x INT."""
    p = run.p
    want = (int(k(run, 'mg_mp_int')) - 1) * int(p.INT)
    have = int(p.__dict__.get('_mg_mp_extra', 0))
    if want != have:
        p.max_mp = max(0, p.max_mp + want - have)
        p.mp = min(p.mp + max(0, want - have), p.max_mp)
        p.__dict__['_mg_mp_extra'] = want


# ---------------------------------------------------------------- learning
def _book(run) -> dict:
    b = run.__dict__.get('_mg_book')
    if b is None:
        b = run._mg_book = {}
    return b


def learn(run, item) -> bool:
    """A spellbook of escape or hold, when its knob is on: one grammar
    question to learn it. True when this module took the book."""
    if not run.prof.get('magic'):
        return False
    sid = getattr(item, 'spell_id', '') or ''
    import difficulty_sim as ds
    sp = ds.SPELLS.get(sid) or {}
    fx = sp.get('effect')
    want = ((fx in ESCAPE_EFFECTS and k(run, 'mg_escape'))
            or (fx in HOLD_EFFECTS and k(run, 'mg_hold') and sid not in ds.MM_SPELL_IDS))
    if not want:
        return False
    if sid not in _book(run) and run.quiz.one_question(item.quiz_tier):
        _book(run)[sid] = sp
    return True


def _reserve(run) -> int:
    p = run.p
    if run.spells and p.hp < 0.7 * p.max_hp:
        return min(c for c, _, _ in run.spells.values())
    return 0


# ---------------------------------------------------------------------- M5
def escape(run, slow: bool):
    """The flee, by a spell: None when no escape is known or affordable (the
    old roll then decides), else True / False."""
    if not k(run, 'mg_escape') or run.p.has_effect('silenced'):
        return None
    p = run.p
    best = None
    for sid, sp in _book(run).items():
        fx = sp.get('effect')
        if fx not in ESCAPE_EFFECTS:
            continue
        cost = p.spell_mp_cost(int(sp['mp_cost']))
        if p.mp < cost:
            continue
        rank = (0 if fx == 'teleport_self' else 1, cost)
        if best is None or rank < best[0]:
            best = (rank, sp, cost)
    if best is None:
        return None
    _rank, sp, cost = best
    p.mp -= cost
    _fs(run, 'mg_escape')
    if not run.quiz.one_question(int(sp.get('tier', 1))):
        return False
    if sp.get('effect') == 'teleport_self':
        _fs(run, 'mg_escaped')
        return True
    import difficulty_sim as ds
    ok = slow or random.random() < ds.FLEE_OK_SLOW
    if ok:
        _fs(run, 'mg_escaped')
    return ok


def _awake(ms):
    return [m for m in ms if m.alive and not any(m.has_effect(e) for e in HELD)]


def pick_target(run, reachable, target):
    """With mg_hold, strike the ones awake first (a blow wakes a sleeper)."""
    if not k(run, 'mg_hold') or not getattr(target, 'alive', False):
        return target
    if not any(target.has_effect(e) for e in HELD):
        return target
    awake = _awake(reachable)
    if not awake:
        return target
    import difficulty_sim as ds
    named = [m for m in awake if ds.is_named(m)]
    return named[0] if named else min(awake, key=lambda m: m.hp)


def hold(run, target, active, queue) -> bool:
    """Sleep or hold the ordinary foes beside him that are not his target,
    by the game's own handler. True when the turn went on it."""
    if not k(run, 'mg_hold') or not _book(run) or run.p.has_effect('silenced'):
        return False
    import difficulty_sim as ds
    import game_magic
    awake = _awake(active)
    others = [m for m in awake if m is not target and not ds.is_named(m)
              and not game_magic._is_big_foe(m)]
    if len(awake) < 2 or not others:
        return False
    in_sight = _awake([m for m in active + list(queue)])
    p = run.p
    res = _reserve(run)
    choice = None
    for sid, sp in _book(run).items():
        shape = HOLD_EFFECTS.get(sp.get('effect'))
        if shape is None:
            continue
        cost = p.spell_mp_cost(int(sp['mp_cost']))
        if p.mp - cost < res:
            continue
        if shape == 'one':
            n = 1
        elif shape == 'near':
            n = min(3, len(others))
        else:
            n = len([m for m in in_sight if not ds.is_named(m)])
            if n < 3:
                continue
        held = 'paralyzed' if (sp.get('effect') == 'paralyze_monster'
                               or sp.get('spell_family') == 'paralyze') else 'sleeping'
        score = (n, 1 if held == 'paralyzed' else 0, -cost)
        if choice is None or score > choice[0]:
            choice = (score, sid, sp, cost)
    if choice is None:
        return False
    _score, sid, sp, cost = choice
    tgt = max(others, key=lambda m: m.hp)
    p.mp -= cost
    _fs(run, 'mg_hold')
    if not run.quiz.one_question(int(sp.get('tier', 1))):
        return True
    foes = [m for m in active + list(queue) if m.alive]
    slots = [(6, 5), (5, 6), (6, 6), (4, 5), (5, 4), (4, 4), (6, 4), (4, 6)]
    seat = {}
    for i, m in enumerate(foes):
        seat[id(m)] = (m.x, m.y)
        if m not in active:
            m.x, m.y = slots[i % len(slots)][0] + 2, slots[i % len(slots)][1]
    try:
        g = ds._MMGame(p, foes, run.floor)
        g._apply_spell_effect(sp, tgt)
    finally:
        for m in foes:
            if id(m) in seat:
                m.x, m.y = seat[id(m)]
    _fs(run, 'mg_held', sum(1 for m in foes if any(m.has_effect(e) for e in HELD)))
    return True


# ------------------------------------------------------- pets and flasks
def ratio_at(floor: float) -> float:
    """The careful blow / floor_curve.one_attack at a depth."""
    import floor_curve
    return _careful_blow(floor) / floor_curve.one_attack(max(1, floor))


def pet_bite_mult(run) -> float:
    a = float(k(run, 'mg_pet_anchor') or 0)
    return a * ratio_at(run.floor) if a > 0 else 1.0


_FLASK = {}


def install_flasks(knobs: dict) -> None:
    """With mg_flask_anchor, coatings.thrown_damage reads each flask's damage
    written against the careful blow at its own sized_at depth."""
    import coatings
    orig = _FLASK.get('orig')
    if orig is None:
        orig = _FLASK['orig'] = coatings.thrown_damage
    a = float(knobs.get('mg_flask_anchor', 0) or 0)
    if a <= 0:
        coatings.thrown_damage = orig
        return

    def thrown_damage(item, monster, _orig=orig, _a=a):
        dmg, dtype = _orig(item, monster)
        spec = coatings.throw_spec(item) or {}
        at = spec.get('sized_at')
        if dmg > 0 and at:
            dmg = max(1, int(round(dmg * _a * ratio_at(float(at)))))
        return dmg, dtype
    coatings.thrown_damage = thrown_damage


# --------------------------------------------------------------- big foes
_BIG = {}


def install_bigfoe(knobs: dict) -> None:
    """With mg_hold and mg_bigfoe, game_magic._is_big_foe reads a kind's
    health before the HP stand-in raised it; otherwise the game's own test."""
    import game_magic
    import sim_late
    orig = _BIG.get('orig')
    if orig is None:
        orig = _BIG['orig'] = game_magic._is_big_foe
    want = bool(int(knobs.get('mg_hold', 0) or 0)) and bool(int(knobs.get('mg_bigfoe', 1) or 0))
    rows = sim_late._STATE.get('hp_rows') or ()
    if not want or not rows:
        game_magic._is_big_foe = orig
        return
    ratio = {kind: (new / max(1e-9, old)) for kind, _pk, _how, _st, old, new in rows}

    def _is_big_foe(m, _orig=orig, _ratio=ratio):
        r = _ratio.get(getattr(m, 'kind', ''), 1.0)
        if r <= 1.0:
            return _orig(m)
        mh = m.max_hp
        try:
            m.max_hp = max(1, int(round(mh / r)))
            return _orig(m)
        finally:
            m.max_hp = mh
    game_magic._is_big_foe = _is_big_foe
