"""The difficulty simulator plays the base game's real rules (2026-11-16).

tools/balance/difficulty_sim.py is how every balance number is measured, so
where it parts from the game the numbers lie. Brandon: "The simulator needs
to look at the base game and core systems, not every fringe." Four places it
parted, fixed and guarded here:

* pace: it left every floor at about 310 turns (a kid takes 700-950), so it
  never met a newcomer and was rarely hungry;
* weight: it carried about 100 lb of food and 55 lb of potions by floor 73,
  with no limit and no coin weight;
* the altar: rededication drained stats down to 10, where the game never
  takes a stat below where it began;
* area spells: it fights one monster at a time, so a fireball hit only that one.
"""
import os
import random
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
os.environ.setdefault('PQ_NO_BONES', '1')

import items  # noqa: E402


def _run(profile='mastery'):
    import difficulty_sim as ds
    run = ds.Run(ds.FloorCache(1), profile, 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
    run.fs = ds.new_floor_stats()
    return ds, run


def test_starvation_is_the_games_share():
    import difficulty_sim as ds
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    m = re.search(r'^STARVE_SHARE = ([0-9.]+)', src, re.M)
    assert m and float(m.group(1)) == ds.STARVE_SHARE


def test_hunger_is_read_from_the_games_dial(monkeypatch):
    import floor_curve
    ds, run = _run()
    assert abs(run._sp_need(100) - 100 / floor_curve.HUNGER_EVERY) < 1e-9
    run.p.status_effects['sustained'] = 50          # half of it Sustained: half the hunger
    assert abs(run._sp_need(100) - (50 / floor_curve.HUNGER_EVERY
                                    + 50 / (2 * floor_curve.HUNGER_EVERY))) < 1e-9


def test_walking_time_runs_down_a_dishs_power():
    ds, run = _run()
    run.p.status_effects['fire_resist'] = 100
    run.p.status_effects['in_pit'] = -1               # for good: untouched
    run._age_statuses(60)
    assert run.p.status_effects['fire_resist'] == 40
    run._age_statuses(60)
    assert 'fire_resist' not in run.p.status_effects
    assert run.p.status_effects['in_pit'] == -1


def test_a_floor_takes_a_kids_pace():
    """The floor's walking is floor_curve.kid_pace of its own explore tour
    (times the profile's pace and a spread), never a flat 300 turns."""
    import difficulty_sim as ds
    src = open(ds.__file__, encoding='utf-8').read()
    assert "explore_turns" not in src.split('def play_floor', 1)[1].split('def _boss_ctx', 1)[0]
    assert 'kid_pace' in src.split('def play_floor', 1)[1]
    random.seed(1)
    run = ds.Run(ds.FloorCache(1), 'mastery', 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
    run.play_floor(1)
    assert 450 <= run.stats[1]['turns'] <= 2500, run.stats[1]['turns']


def test_the_altar_never_takes_a_stat_below_where_it_began():
    ds, run = _run('mastery')
    p = run.p
    run.knobs = dict(run.knobs, altars=1, traders=0)
    start = dict(p.stats_at_start)
    run.quiz.escalator_chain = lambda n=5: 5        # a perfect chain: two points
    run.rededicate(1)
    assert all(getattr(p, s) >= start[s] for s in start), {s: getattr(p, s) for s in start}
    # Raised in a stat other gifts paid for: the ledger the kitchen reads.
    p.apply_stat_bonus('PER', 2)
    p.cooking_stat_gained['PER'] = 2
    run.rededicate(16)
    import rededication
    assert p.PER >= start['PER']
    assert rededication.taught(p, 'STR') == p.rededicated.get('STR', 0) + p.cooking_stat_gained['STR']
    assert p.rededicated.get('STR', 0) >= 1


def test_the_pack_stays_under_the_line_and_food_under_two_bellies():
    ds, run = _run('mastery')
    p = run.p
    bread = items.make_item_by_id('food', 'trail_rations')
    for _ in range(60):
        run.food.append(bread)
    potion = next(x for x in items.load_items('potion') if getattr(x, 'effect', '') == 'heal')
    for _ in range(200):
        run.potions.append(potion)
    run.gold = 50000
    run._sync_pack()
    assert p.get_current_weight() <= run._pack_line() + 1e-6
    assert sum(f.sp_restore for f in run.food) <= ds.FOOD_KEEP_BELLIES * p.max_sp
    assert p.purse_coins == int(run.gold)


def test_coin_that_will_not_fit_is_left_and_gems_weigh_nothing():
    import treasure
    ds, run = _run('mastery')
    p = run.p
    room = treasure.coins_in(run._pack_line() - p.get_current_weight())
    run._take_coin(room + 5000)
    assert run.gold <= room + 1 and run.fs['coin_left'] >= 4999
    run._coin_to_gems()
    assert run.gold <= ds.KEEP_COIN_LB * treasure.COINS_PER_LB
    assert run.gems > 0 and run._pay(run.gold + 10, 0)           # gems pay what coin cannot


def test_an_area_spell_hits_the_whole_fight_and_a_bolt_only_one():
    import difficulty_sim as ds
    from monster import Monster
    import json
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        defs = json.load(f)
    ds_, run = _run('mastery_mage')
    p = run.p
    p.mp = p.max_mp = 500
    group = [ds.fresh_monster(Monster({**defs['goblin'], 'id': 'goblin'}, 0, 0), run.knobs, 1)
             for _ in range(5)]
    for m in group:
        m.max_hp = m.hp = 10000
    run.quiz.one_question = lambda tier: True
    run.attack_spells = {'fireball_spell': (10, '5d6', 3, 'fire', 'mass_fire')}
    random.seed(2)
    assert run.cast_attack(group[0], group)
    assert all(m.hp < 10000 for m in group)
    for m in group:
        m.hp = 10000
    run.attack_spells = {'fire_bolt_spell': (6, '3d6', 2, 'fire', 'fire_bolt')}
    assert run.cast_attack(group[0], group)
    assert group[0].hp < 10000 and all(m.hp == 10000 for m in group[1:])
    assert set(ds.AREA_SPELLS) <= set(ds.ATTACK_SPELLS)
