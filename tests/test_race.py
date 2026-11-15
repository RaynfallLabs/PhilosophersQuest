"""The Underway Run's scoring (src/race.py), pure: no pygame, no game.

Brandon, 2026-11-14 (RARE_PETS_PLAN 3): the race is a maths race. Pacing
well beats sprinting every leg, Varro's caltrops on leg 3 cost the inside
lane and the outside lane runs clean, a strong kid wins and a weak one
loses. Whether it FEELS right is Brandon's play-test.
"""
import json
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import race as R  # noqa: E402

with open(os.path.join(ROOT, 'data', 'bococho.json'), encoding='utf-8') as _f:
    CFG = json.load(_f)['race']


def run(chains, modes, lane3='outside', tier=3, seed=11, cfg=CFG):
    r = R.new_race(seed, tier, cfg)
    for i, (c, m) in enumerate(zip(chains, modes)):
        lane = lane3 if i + 1 == cfg['cheat_leg'] else 'inside'
        R.run_leg(r, c, m, lane, cfg)
    return r


def test_the_race_data_is_whole():
    for key in ('legs', 'max_chain', 'base_per_leg', 'stride', 'sprint_mult', 'winded_mult',
                'wind_start', 'wind_max', 'sprint_cost', 'pace_recover', 'final_kick',
                'cheat_leg', 'caltrops_mult', 'outside_mult', 'varro_pace', 'varro_luck',
                'photo_margin', 'lap_lengths'):
        assert key in CFG, key
    assert CFG['legs'] == 5 and len(CFG['varro_pace']) == CFG['legs']
    assert CFG['sprint_mult'] == 1.5
    assert set(CFG['stride']) == {'1', '2', '3', '4', '5'}
    assert len(CFG['taunts']) == CFG['legs']
    assert set(CFG['events']) >= {'winded', 'sprint', 'tired_sprint', 'pace', 'kick',
                                  'caltrops', 'outside'}


def test_a_leg_is_the_chain_times_her_stride():
    r = R.new_race(1, 3, CFG)
    out = R.run_leg(r, 4, 'pace', 'inside', CFG)
    want = CFG['base_per_leg'] + 4 * CFG['stride']['3']
    assert math.isclose(out['hero_run'], want)
    assert r['leg'] == 1 and not r['done']
    assert out['events'] == ['pace']


def test_a_sprint_goes_half_again_as_far_and_cuts_the_next_leg():
    r = R.new_race(1, 3, CFG)
    s = R.run_leg(r, 4, 'sprint', 'inside', CFG)
    base = CFG['base_per_leg'] + 4 * CFG['stride']['3']
    assert math.isclose(s['hero_run'], base * 1.5)
    assert r['winded'] and r['wind'] == CFG['wind_start'] - CFG['sprint_cost']
    nxt = R.run_leg(r, 4, 'pace', 'inside', CFG)
    assert nxt['events'][0] == 'winded'
    assert math.isclose(nxt['hero_run'], base * CFG['winded_mult'])


def test_pace_beats_sprint_sprint():
    """Two sprints in a row lose ground: the second is run winded and the
    third leg too. Pacing to the home straight and sprinting there wins."""
    chains = [4, 4, 4, 4, 4]
    paced = run(chains, ['pace', 'pace', 'pace', 'pace', 'sprint'])
    all_pace = run(chains, ['pace'] * 5)
    sprint_sprint = run(chains, ['sprint', 'sprint', 'pace', 'pace', 'pace'])
    all_sprint = run(chains, ['sprint'] * 5)
    assert paced['hero'] > all_pace['hero'] > sprint_sprint['hero']
    assert paced['hero'] > all_sprint['hero']
    # (the same chains: only the choices differ)
    assert paced['varro'] == all_sprint['varro']


def test_a_tired_sprint_gives_only_part_of_the_boost():
    r = R.new_race(1, 3, CFG)
    R.run_leg(r, 4, 'sprint', 'inside', CFG)
    R.run_leg(r, 4, 'sprint', 'inside', CFG)        # wind 100 -> 50 -> 0
    assert r['wind'] == 0
    third = R.run_leg(r, 4, 'sprint', 'inside', CFG)
    assert 'tired_sprint' in third['events'] and 'sprint' not in third['events']


def test_the_cheat_leg_salts_the_inside_and_the_outside_runs_clean():
    chains = [4, 4, 4, 4, 4]
    modes = ['pace'] * 5
    inside = run(chains, modes, lane3='inside')
    outside = run(chains, modes, lane3='outside')
    leg3_in = inside['history'][2]
    leg3_out = outside['history'][2]
    assert 'caltrops' in leg3_in['events'] and 'outside' in leg3_out['events']
    assert leg3_out['hero_run'] > leg3_in['hero_run'] * 2
    # only leg 3 is salted: the other legs are the same
    for i in (0, 1, 3, 4):
        assert math.isclose(inside['history'][i]['hero_run'], outside['history'][i]['hero_run'])
    # the lane chosen on another leg does nothing
    r = R.new_race(1, 3, CFG)
    out = R.run_leg(r, 4, 'pace', 'outside', CFG)
    assert out['events'] == ['pace']


def test_varro_runs_a_written_pace_with_a_little_seeded_luck():
    r = R.new_race(99, 3, CFG)
    legs = [R.varro_leg(r, i, CFG) for i in range(5)]
    assert legs == [R.varro_leg(r, i, CFG) for i in range(5)]      # a leg run again is the same
    for i, v in enumerate(legs):
        assert abs(v - CFG['varro_pace'][i]) <= CFG['varro_luck'] + 1e-9
    other = R.new_race(100, 3, CFG)
    assert [R.varro_leg(other, i, CFG) for i in range(5)] != legs


def _kid_chain(rng, acc, med, clock, cap):
    t, c = 0.0, 0
    while True:
        a = rng.lognormvariate(math.log(med), 0.30)
        if t + a > clock:
            return c
        t += a
        if rng.random() >= acc:
            return c
        c += 1
        if c >= cap:
            return c


def _win_rate(acc, med, clock, modes, lane3, tier=3, n=1500):
    wins = 0
    for seed in range(n):
        rng = random.Random(seed)
        r = R.new_race(seed, tier, CFG)
        for i in range(5):
            c = _kid_chain(rng, acc, med, clock, CFG['max_chain'])
            R.run_leg(r, c, modes[i], lane3 if i + 1 == CFG['cheat_leg'] else 'inside', CFG)
        wins += R.outcome(r, CFG)['won']
    return wins / n


GOOD_PLAN = ['pace', 'pace', 'pace', 'pace', 'sprint']


def test_a_strong_kid_who_paces_well_wins_most_races():
    """A mastery-level kid (92% right, quick: tools/balance answer times)
    who paces and takes the outside lane on the cheat leg."""
    assert _win_rate(0.92, 4.5 * 0.75, 20, GOOD_PLAN, 'outside') >= 0.8


def test_a_strong_kid_who_runs_sloppily_loses():
    assert _win_rate(0.92, 4.5 * 0.75, 20, ['sprint'] * 5, 'inside') <= 0.15


def test_a_weak_kid_loses():
    assert _win_rate(0.75, 4.5 * 1.1, 16, GOOD_PLAN, 'outside') <= 0.1


def test_the_finish_a_photo_and_a_dead_heat_goes_to_her():
    r = R.new_race(1, 3, CFG)
    r.update({'hero': 50.0, 'varro': 50.0, 'leg': 5, 'done': True})
    res = R.outcome(r, CFG)
    assert res['won'] and res['photo']
    r['varro'] = 50.5
    assert not R.outcome(r, CFG)['won'] and R.outcome(r, CFG)['photo']
    r['varro'] = 40.0
    assert R.outcome(r, CFG) == {'won': True, 'photo': False, 'gap': 10.0}


def test_positions_round_the_oval():
    r = R.new_race(1, 3, CFG)
    assert R.positions(r, 100, CFG) == (0, 0)                     # at the line
    r.update({'hero': CFG['lap_lengths'] / 2, 'varro': CFG['lap_lengths'] / 4})
    h, v = R.positions(r, 100, CFG)
    assert h == 50 and v == 25
    r.update({'hero': CFG['lap_lengths'] * 3})                     # nobody on the line before the finish
    assert R.positions(r, 100, CFG)[0] == 100 - CFG['short_of_line']
    r.update({'hero': 70.0, 'varro': 63.0, 'done': True})          # the finish: the winner on the line
    h, v = R.positions(r, 100, CFG)
    assert h == 0 and 85 <= v < 100


def test_standing_words():
    r = R.new_race(1, 3, CFG)
    r.update({'hero': 10.0, 'varro': 10.2})
    assert R.standing(r, CFG) == 'level'
    r['hero'] = 13.0
    assert R.standing(r, CFG) == 'lead'
    r['hero'] = 30.0
    assert R.standing(r, CFG) == 'lead_big'
    r['hero'] = 5.0
    assert R.standing(r, CFG) == 'behind'
    assert R.lengths(0.2) == 1 and R.lengths(-3.6) == 4
