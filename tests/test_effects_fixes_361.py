"""3.6.1's balance run (2026-11-22): the floor-20 gate got harder because
Asterion's Gore floored the hero as his Trample does, and the simulated kid
never took Guard or bought more than one Oil of Rue. A gore is a thrust,
not a trample; the careful kid meets a floorer or a stunner in Guard and
buys his Oil once a stone that kills has been met."""
import json
import os
import random
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import knockdown  # noqa: E402
import tells  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _atk(kind, name):
    return next(a for a in MONS[kind]['attacks'] if a['name'] == name)


def _mon(kind):
    return Monster({**MONS[kind], 'id': kind}, 1, 1)


def test_a_gore_is_a_thrust_and_floors_no_one():
    assert not knockdown.floors(_atk('asterion_minotaur', 'Gore'))
    assert knockdown.floors(_atk('asterion_minotaur', 'Trample'))
    assert knockdown.floors(_atk('centaur', 'Hoof Trample'))


def test_only_horns_tusks_and_antlers_are_thrusts():
    for kind, m in MONS.items():
        if not isinstance(m, dict):
            continue
        for a in m.get('attacks') or ():
            if a.get('floors') is False:
                assert a.get('delivery') == 'trample', (kind, a['name'])
                assert any(w in a['name'].lower() for w in ('gore', 'tusk', 'antler')), (kind, a['name'])


def test_a_thrust_is_still_a_trample_for_the_boots():
    import guards
    assert guards.delivery(_atk('asterion_minotaur', 'Gore')) == 'trample'


def test_a_landed_gore_asks_no_save(monkeypatch):
    p = Player()
    called = []
    import status_effects
    monkeypatch.setattr(status_effects, 'apply_debuff_with_save', lambda *a, **k: called.append(a) or (True, ''))
    assert knockdown.from_trample(_mon('minotaur'), p, _atk('minotaur', 'Gore'), 5) == ''
    assert not called


def test_the_tell_follows_the_rule():
    assert 'knocked_down' in tells.abilities(_mon('asterion_minotaur'))     # his Trample
    assert 'knocked_down' not in tells.abilities(_mon('peryton'))           # an antler gore alone
    assert 'knocked_down' not in tells.abilities(_mon('hell_bovine'))       # a gore alone


def _run(tactics=1, knows=True, mm=1):
    run = types.SimpleNamespace(knobs={'tactics': tactics}, fs={})
    run._knows = lambda kind: knows
    run._mm = lambda k: bool(mm)
    kit = {'potion': [], 'scroll': [], 'wand': [], 'spells': {}}
    run._mm_kit = lambda: kit
    run.paid = []
    run._pay = lambda cost, reserve, kind='goods': run.paid.append(cost) or True
    return run


def test_the_careful_kid_meets_a_floorer_in_guard():
    import sim_effects
    assert sim_effects.wants_guard(_run(), [_mon('asterion_minotaur')])
    assert not sim_effects.wants_guard(_run(knows=False), [_mon('asterion_minotaur')])
    assert not sim_effects.wants_guard(_run(tactics=0), [_mon('asterion_minotaur')])
    assert not sim_effects.wants_guard(_run(), [_mon('troll')])


def test_oil_of_rue_is_bought_once_a_stone_that_kills_is_met():
    import sim_effects
    run = _run()
    sim_effects.buy_rue(run, 25, {}, 0)
    assert not run._mm_kit()['potion']                      # nothing met yet
    sim_effects.note_stone(run, [_mon('troll')])
    sim_effects.buy_rue(run, 25, {}, 0)
    assert not run._mm_kit()['potion']
    sim_effects.note_stone(run, [_mon('basilisk')])
    sim_effects.buy_rue(run, 25, {}, 0)
    assert [x.effect for x in run._mm_kit()['potion']] == ['stoneproof', 'stoneproof']
    sim_effects.buy_rue(run, 25, {}, 0)
    assert len(run._mm_kit()['potion']) == 2               # two at most
