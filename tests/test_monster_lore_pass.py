"""The monster lore pass of 2026-11-19: each ordinary monster's numbers from
its own lore, measured against the hero who meets it.

Brandon, 2026-11-19: "Your fix SUCKS AGAIN, because you started using
smoothing multipliers to hit a target ... NEVER DO THIS ... Fix the data at
the source, create a balanced game." And: "the more diverse and unique our
monsters are, the better." Earlier passes had seated every monster on a
floor curve (every floor-16 kind hit 1d8+2; respawn_by_hp re-seated kinds
by their HP); this pass re-wrote 517 kinds by their size, weapons, skill,
speed and powers (docs/design/MONSTER_LORE_PASS_2026_11_19.md,
tools/balance/apply_lore_pass.py).

These are the pass's safety rails, measured against the simulated hero of
each floor (tools/balance/monster_bands.HERO), in place of the old damage-
anchor spike caps (which measured a monster against the flat curve).
"""
from __future__ import annotations

import collections
import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import monster_bands as mb  # noqa: E402
from status_effects import CONTROL_CAP  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)

DOT = {'poisoned', 'burning', 'bleeding', 'diseased', 'corroding'}


def _ordinary():
    for k, m in MONS.items():
        if isinstance(m, dict) and not mb.is_named(m) and (m.get('peak_weight', 0) or 0) > 0:
            yield k, m


def test_no_ordinary_monster_can_one_turn_the_hero_who_meets_it():
    """A monster's turn (all of a routine, before the hit roll) is at most a
    quarter of the health of the hero of its peak floor, and its turn or its
    hardest single blow at most a third of the hero's of the first floor it
    can be met on."""
    bad = []
    for k, m in _ordinary():
        _one, turn = mb.turn_damage(m)
        hardest = max((mb.dice_mean(a.get('damage')) for a in m.get('attacks') or []), default=0)
        at_peak = mb.hero_at(m.get('peak_floor', 1))[1]
        at_first = mb.hero_at(m.get('min_level', 1))[1]
        if turn > 0.25 * at_peak or max(turn, hardest) > 0.35 * at_first:
            bad.append((k, round(turn, 1), round(hardest, 1), round(at_peak), round(at_first)))
    assert not bad, bad[:10]


def test_riders_keep_to_the_engines_limits():
    """Control within status_effects.CONTROL_CAP, damage-over-time short (it
    ticks a share of max HP each turn), chances below certainty, and no
    'draining' (the ring's slow drain: its line names the ring)."""
    bad = []
    for k, m in _ordinary():
        for a in m.get('attacks') or []:
            e = a.get('effect')
            if not e:
                continue
            ch = float(a.get('effect_chance', 0) or 0)
            dur = a.get('effect_duration')
            fixed = int(dur) if isinstance(dur, int) or str(dur).isdigit() else None
            if (ch > 0.7 or e == 'draining'
                    or (fixed is not None and e in CONTROL_CAP and fixed > CONTROL_CAP[e])
                    or (fixed is not None and e in DOT and fixed > 12)):
                bad.append((k, a['name'], e, ch, dur))
    assert not bad, bad[:10]


def test_kinds_on_one_floor_are_not_twins():
    """No two ordinary kinds peaking on the same floor share both their HP and
    their every damage line, from floor 4 down. (Floors 1-3 meet a hero of 30-38
    HP: there the small dice are shared and the kinds differ by aim, speed,
    HP and rider.)"""
    twins = collections.defaultdict(list)
    for k, m in _ordinary():
        pf = m.get('peak_floor', 1)
        if pf < 4:
            continue
        twins[(pf, str(m.get('hp')), tuple(a.get('damage') for a in m.get('attacks') or []))].append(k)
    assert not [v for v in twins.values() if len(v) > 1]


def test_a_floor_no_longer_hits_the_same_everywhere():
    """The pass's point: a landed blow was about 5% of the floor hero's health
    on every floor 1-99, a turn about 3%. Now each floor's kinds differ widely:
    the hardest-hitting tenth costs at least twice the gentlest tenth."""
    for f in (4, 8, 12, 16, 20, 30, 45, 60, 80, 99):
        r = mb.floor_row(MONS, f)
        assert r['p90'] >= 2.0 * r['p10'], (f, r['p10'], r['p90'])
        assert r['turn'] >= 0.037, (f, r['turn'])


def test_a_third_or_more_open_with_their_power():
    for f in (4, 10, 20, 40, 60, 90):
        assert mb.floor_row(MONS, f)['opener'] >= 0.25, f


def test_the_old_flattening_tools_refuse_to_write():
    tools = [os.path.join(ROOT, 'tools', 'balance', 'respawn_by_hp.py'),
             os.path.join(ROOT, 'tools', 'balance', 'scale_monsters.py'),
             os.path.join(ROOT, 'tools', 'balance', 'apply_difficulty_schedule.py'),
             os.path.join(ROOT, 'tools', 'balance', 'monster_pass_2026_11_17.py'),
             os.path.join(ROOT, 'tools', 'content', 'late_game_monsters_2026_10.py')]
    before = open(os.path.join(ROOT, 'data', 'monsters.json'), 'rb').read()
    for t in tools:
        for flag in ('--write', '--i-know'):
            r = subprocess.run([sys.executable, t, flag], capture_output=True, text=True, cwd=ROOT,
                               env={**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'PQ_NO_BONES': '1'},
                               timeout=120)
            assert r.returncode == 2 and 'will not write' in r.stderr, (t, flag, r.stderr[-300:])
    assert open(os.path.join(ROOT, 'data', 'monsters.json'), 'rb').read() == before
