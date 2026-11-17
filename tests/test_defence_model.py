"""The defence model (Brandon, 2026-11-16; src/defence.py, data/gear_rules.json
`defence` and `load`).

* AC comes from armour, the shield and magic only: no Dexterity in AC.
* Dodge: Dexterity, a point over 10, capped; light armour keeps all of it,
  medium half, heavy none; the load takes a share of what is left.
* Speed: Dexterity makes the hero quicker, a point over 10, capped; light
  armour keeps all of that quickness, medium half, heavy none. Medium and
  heavy armour cost speed and Strength pays it back: a STR-fit hero in
  plate is at 10, whatever his Dexterity. Only armour too heavy for his
  Strength and a load he chose to carry take him under 10.
* The load: Light over half the limit (a little less dodge), Heavy over 70%
  (half the dodge, slower), Burdened over 90% (no dodge, much slower),
  Overloaded past the limit (a wall). Speed replaces the old rule that every
  second Burdened step cost an extra turn. Constitution over 10 carries a
  little more.

Pure-function tests on src/defence.py, the Player's readers, the game's
scheduler, the data and the simulator's guards. Whether speed FEELS like an
advantage, not a tax, is Brandon's play-test.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
os.environ.setdefault('PQ_NO_BONES', '1')

import pytest  # noqa: E402

import defence  # noqa: E402
import gear  # noqa: E402
import items  # noqa: E402
from player import Player  # noqa: E402


def _rules():
    with open(os.path.join(ROOT, 'data', 'gear_rules.json'), encoding='utf-8') as f:
        return json.load(f)


def _wearing(tpl=None, mat=None, dex=10, str_=10, con=10):
    p = Player()
    p.DEX, p.STR, p.CON = dex, str_, con
    if tpl:
        p._apply_equip(items.instantiate_armor(tpl, mat))
    return p


def _weight(lb):
    it = items.instantiate_weapon('longsword', 'iron')
    it.weight = float(lb)
    return it


# ------------------------------------------------------------------ the data

def test_the_rules_are_in_the_data():
    r = _rules()
    d = r['defence']
    for key in ('dodge_per_dex', 'dodge_cap', 'speed_per_dex', 'speed_cap', 'speed_share',
                'armour_drag', 'str_payback', 'con_carry', 'min_speed_share'):
        assert key in d, key
    # Brandon's design: about 1% a point, capped near 35-40%; about +1% a
    # point, capped near +20%; heavy armour costs speed, Strength pays it.
    assert 0.008 <= d['dodge_per_dex'] <= 0.02 and 0.30 <= d['dodge_cap'] <= 0.40
    assert 0.008 <= d['speed_per_dex'] <= 0.02 and 0.15 <= d['speed_cap'] <= 0.25
    # Dexterity's quickness by weight class, as its dodge: a STR-fit hero in
    # plate is at 10, light armour and Dexterity go above it.
    assert d['speed_share']['light'] == 1.0 and d['speed_share']['heavy'] == 0.0
    drag = d['armour_drag']
    assert set(drag) == {'light', 'medium', 'heavy'}
    assert drag['light'] == 0.0 < drag['medium'] < drag['heavy']
    assert d['str_payback'] > 0 and d['con_carry'] > 0
    # Brandon's load tiers: Light at half, Heavy at 70%, Burdened at 90%.
    load = r['load']
    assert load['light']['share'] == 0.5
    assert load['heavy']['share'] == 0.7
    assert load['burdened']['share'] == 0.9
    # A minor dodge penalty, then larger ones; speed from Heavy on.
    assert 1.0 > load['light']['dodge'] > load['heavy']['dodge'] >= load['burdened']['dodge']
    assert load['burdened']['dodge'] >= load['overloaded']['dodge'] == 0.0
    assert load['light']['speed'] == 0.0
    assert 0.0 < load['heavy']['speed'] < load['burdened']['speed'] <= load['overloaded']['speed']
    # Gone: Dexterity's AC and the step rule.
    assert 'dex_ac_cap' not in r['armour_weight']
    for tier in load.values():
        if isinstance(tier, dict):
            assert 'dex_ac' not in tier and 'step_every' not in tier
    assert r['armour_weight']['dodge_share'] == {'light': 1.0, 'medium': 0.5, 'heavy': 0.0}


def test_the_noise_follows_the_four_tiers():
    with open(os.path.join(ROOT, 'data', 'senses.json'), encoding='utf-8') as f:
        n = json.load(f)['noise']
    assert 0 < n['light'] <= n['heavy'] <= n['burdened'] <= n['overloaded']


# --------------------------------------------------------- the pure sums: dodge

def test_dodge_is_a_point_over_ten_and_capped():
    r = defence.rules()
    assert defence.dex_dodge(10) == 0.0 and defence.dex_dodge(6) == 0.0
    assert defence.dex_dodge(20) == pytest.approx(10 * r['dodge_per_dex'])
    assert defence.dex_dodge(200) == pytest.approx(r['dodge_cap'])


def test_the_load_takes_a_share_of_the_dodge():
    lr = defence.load_rules()
    assert defence.load_dodge_share('') == 1.0
    for tier in ('light', 'heavy', 'burdened', 'overloaded'):
        assert defence.load_dodge_share(tier) == lr[tier]['dodge']


# --------------------------------------------------------- the pure sums: speed

def test_dexterity_makes_him_quicker_and_is_capped():
    r = defence.rules()
    assert defence.speed_rating(defence.speed_share(10, 10, 'light')) == 10.0
    assert defence.speed_rating(defence.speed_share(6, 6, 'light')) == 10.0    # clumsy: never under 10
    s20 = defence.speed_rating(defence.speed_share(20, 10, 'light'))
    assert s20 == pytest.approx(10 * (1 + 10 * r['speed_per_dex']))
    assert defence.speed_rating(defence.speed_share(200, 10, 'light')) == pytest.approx(
        10 * (1 + r['speed_cap']))


def test_a_strength_fit_hero_in_plate_is_at_ten_whatever_his_dexterity():
    fit = defence.fit_strength('heavy')
    for dex in (10, 20, 30, 50):
        assert defence.speed_rating(defence.speed_share(dex, fit, 'heavy')) == 10.0
        assert defence.speed_rating(defence.speed_share(dex, fit, 'light')) >= 10.0
    assert (defence.speed_share(30, 10, 'light') > defence.speed_share(30, 30, 'medium')
            > defence.speed_share(30, 30, 'heavy') == 1.0)


def test_strength_pays_the_armours_drag_back():
    for cls in ('medium', 'heavy'):
        fit = defence.fit_strength(cls)
        assert fit > 10
        # A STR-fit hero in this armour is at 10; one short of it is slower.
        assert defence.speed_rating(defence.speed_share(10, fit, cls)) == 10.0
        assert defence.speed_rating(defence.speed_share(10, fit - 1, cls)) < 10.0
        # More Strength never makes armour quicker than none.
        assert defence.speed_rating(defence.speed_share(10, fit + 10, cls)) == 10.0
    assert defence.fit_strength('light') == 10
    assert defence.fit_strength('medium') < defence.fit_strength('heavy')


def test_only_unpaid_armour_and_the_load_go_under_ten():
    """Every monster's damage was sized for a hero at speed 10."""
    for dex in (6, 10, 14, 20, 30):
        for str_ in (6, 10, 14, 18, 25):
            assert defence.speed_share(dex, str_, 'light') >= 1.0
            for cls in ('medium', 'heavy'):
                if str_ >= defence.fit_strength(cls):
                    assert defence.speed_share(dex, str_, cls) >= 1.0
    assert defence.speed_share(10, 30, 'heavy', 'heavy') < 1.0          # a Heavy load
    assert defence.speed_share(10, 30, 'heavy', 'light') == 1.0         # a Light one costs none


def test_the_load_slows_from_heavy_on_and_marius_keeps_his_stride():
    base = defence.speed_share(15, 10, 'light')
    assert defence.speed_share(15, 10, 'light', 'light') == base
    heavy = defence.speed_share(15, 10, 'light', 'heavy')
    burd = defence.speed_share(15, 10, 'light', 'burdened')
    over = defence.speed_share(15, 10, 'light', 'overloaded')
    assert base > heavy > burd > over
    for tier in ('light', 'heavy', 'burdened'):
        assert defence.speed_share(15, 10, 'light', tier, ignore_load=True) == base
    assert defence.speed_share(15, 10, 'light', 'overloaded', ignore_load=True) == over


def test_speed_boots_and_haste_ride_on_top():
    assert defence.speed_rating(1.1, 0.0, False) == 11.0
    assert defence.speed_rating(1.1, 0.05, False) == pytest.approx(11.55)
    assert defence.speed_rating(1.1, 0.0, True) == 22.0
    assert defence.speed_rating(0.0) == 0.0
    assert defence.speed_share(10, 0, 'heavy', 'overloaded') >= defence.rules()['min_speed_share']


# --------------------------------------------------------- the pure sums: the load

def test_the_four_tiers_at_brandons_lines():
    assert defence.load_tier(50, 100) == ''
    assert defence.load_tier(50.1, 100) == 'light'
    assert defence.load_tier(70, 100) == 'light'
    assert defence.load_tier(70.1, 100) == 'heavy'
    assert defence.load_tier(90, 100) == 'heavy'
    assert defence.load_tier(90.1, 100) == 'burdened'
    assert defence.load_tier(100, 100) == 'burdened'
    assert defence.load_tier(100.1, 100) == 'overloaded'
    assert defence.load_lines() == (0.5, 0.7, 0.9)
    assert [defence.tier_rank(t) for t in defence.LOAD_TIERS] == [0, 1, 2, 3, 4]
    assert defence.tier_rank('stressed') == 0                # an old save's word


def test_constitution_carries_a_little():
    r = defence.rules()
    assert defence.carry_limit(10, 10, 20, 8) == 100
    assert defence.carry_limit(10, 20, 20, 8) == 100 + 10 * r['con_carry']
    assert defence.carry_limit(10, 6, 20, 8) == 100                  # never less
    assert r['con_carry'] < 8                                        # a little: Strength's is 8


# ------------------------------------------------------------------ the scheduler

def test_the_world_takes_a_turn_for_every_ten_of_his_speed():
    def run(speed, n):
        c, total = 0.0, 0
        for _ in range(n):
            k, c = defence.world_turns(c, speed)
            total += k
        return total
    assert run(10, 50) == 50
    assert run(20, 50) == 25                      # haste: every other action
    assert run(11, 110) == 100                    # a nimble hero: one in eleven waits
    assert run(9, 90) == 100                      # a slowed one: one in nine is two turns
    assert run(5, 10) == 20                       # half speed: two turns an action
    assert defence.world_turns(0.0, 20.0) == (0, 0.5)               # a fresh haste waits first
    assert defence.world_turns(0.7, 10.0) == (1, 0.0)               # at 10 the clock is clean


def test_the_game_gives_the_world_two_turns_when_he_is_slow():
    import pygame
    pygame.init()
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(5)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_defence_sched__')
    g.state = STATE_PLAYER
    g.monsters = []
    turns = []
    g._do_monster_turns = lambda: turns.append(1)
    g.player.get_speed = lambda: 9.0
    for _ in range(9):
        g._advance_turn()
    assert len(turns) == 10
    turns.clear()
    g.player.get_speed = lambda: 10.0
    for _ in range(9):
        g._advance_turn()
    assert len(turns) == 9
    turns.clear()
    g.player.get_speed = lambda: 11.0
    for _ in range(11):
        g._advance_turn()
    assert len(turns) == 10
    # No second turn of the world once the first has opened a popup.
    turns.clear()
    g._world_clock = 0.0
    g.player.get_speed = lambda: 5.0
    g._do_monster_turns = lambda: (turns.append(1), setattr(g, 'state', 'popup'))
    g._advance_turn()
    assert len(turns) == 1
    g.state = STATE_PLAYER


# ------------------------------------------------------------ the Player's readers

def test_dexterity_gives_no_ac():
    for tpl, mat in ((None, None), ('leather', 'leather'), ('chain_shirt', 'chain_steel'),
                     ('plate', 'chain_steel')):
        assert _wearing(tpl, mat, dex=30).get_ac() == _wearing(tpl, mat, dex=10).get_ac()
        assert _wearing(tpl, mat, dex=5).get_ac() == _wearing(tpl, mat, dex=10).get_ac()
    assert _wearing('plate', 'chain_steel').get_ac() == 10 - 7
    assert _wearing('leather', 'leather', dex=22).get_ac() == 10 - 2


def test_the_heros_dodge_by_weight_class():
    per = defence.rules()['dodge_per_dex']
    assert _wearing('leather', 'leather', dex=20).dodge_chance() == pytest.approx(10 * per)
    assert _wearing('chain_shirt', 'chain_steel', dex=20).dodge_chance() == pytest.approx(5 * per)
    assert _wearing('plate', 'chain_steel', dex=20).dodge_chance() == 0.0


def test_the_heros_speed():
    per = defence.rules()['speed_per_dex']
    assert Player().get_speed() == 10.0
    nimble = _wearing('leather', 'leather', dex=20)
    assert nimble.get_speed() == pytest.approx(10 * (1 + 10 * per))
    fit = defence.fit_strength('heavy')
    knight = _wearing('full_plate', 'chain_steel', str_=fit + 4)
    assert knight.get_speed() == 10.0                          # STR-fit in plate: 10
    weak = _wearing('plate', 'chain_steel', str_=10)
    assert weak.get_speed() < 10.0                             # too heavy for him
    parts = weak.speed_parts()
    assert parts['armour'] > 0 and parts['load'] == 0.0 and parts['dex'] == 0.0
    weak.add_effect('hasted', 5)
    assert weak.get_speed() == pytest.approx(2 * 10 * (1 - parts['armour']), abs=0.02)


def test_the_load_slows_and_marius_mule_keeps_the_stride():
    p = Player()                                     # limit 100
    p.inventory.append(_weight(60))
    assert p.load_tier() == 'light' and p.get_speed() == 10.0
    p.inventory.append(_weight(20))                  # 80: Heavy
    assert p.load_tier() == 'heavy' and p.get_speed() < 10.0
    slow = p.get_speed()
    p.inventory.append(_weight(15))                  # 95: Burdened
    assert p.load_tier() == 'burdened' and p.get_speed() < slow
    p.quirk_progress = {'marius_active': True}
    assert p.keeps_stride() and p.get_speed() == 10.0
    p.inventory.append(_weight(10))                  # 105: Overloaded
    assert p.load_tier() == 'overloaded' and p.get_speed() < 10.0


def test_constitution_raises_the_limit_and_strength_more():
    p = Player()
    assert p.get_carry_limit() == 100
    p.CON = 20
    assert p.get_carry_limit() == 100 + 10 * defence.rules()['con_carry']
    p.STR = 11
    assert p.get_carry_limit() == 108 + 10 * defence.rules()['con_carry']


def test_the_card_says_the_speed_cost():
    plate = items.instantiate_armor('plate', 'chain_steel')
    assert gear.weight_line(plate).startswith(
        f"Heavy metal: no dodge or quickness, slower below Strength {defence.fit_strength('heavy')}")
    mail = items.instantiate_armor('chain_shirt', 'chain_steel')
    assert (f"half dodge and quickness, slower below Strength {defence.fit_strength('medium')}"
            in gear.weight_line(mail))
    leather = items.instantiate_armor('leather', 'leather')
    assert gear.weight_line(leather) == "Light: full dodge and quickness; scorches."


def test_no_old_defence_terms_left_in_the_code():
    """The system-change sweep: Dexterity's AC and the Burdened step rule."""
    import glob
    for path in glob.glob(os.path.join(ROOT, 'src', '*.py')):
        src = open(path, encoding='utf-8').read()
        for word in ('dex_ac_cap', 'load_dex_ac_share', 'burden_step', 'load_step_every',
                     'BURDENED_STEP_EVERY', 'OVERLOADED_STEP_EVERY', '_burden_extra_turn',
                     'every second step'):
            assert word not in src, (os.path.basename(path), word)
    for path in glob.glob(os.path.join(ROOT, 'data', 'ui', '*.json')) + [
            os.path.join(ROOT, 'data', 'hints.json')]:
        txt = open(path, encoding='utf-8').read()
        for phrase in ('every second step', 'Dexterity guards you', 'Dexterity no longer guards',
                       'Dexterity to AC', 'Over three quarters'):
            assert phrase not in txt, (os.path.basename(path), phrase)


# ------------------------------------------------------------------ old saves

def test_an_old_saves_load_fields_do_not_matter():
    p = Player()
    p.inventory.append(_weight(80))
    p._load_tier = 'burdened'                    # a pre-2026-11-16 save at its old line
    p._burden_steps = 1                          # the old step counter: read by nothing
    assert p.update_burden() == ('burdened', 'heavy')
    assert p.get_speed() < 10.0


# --------------------------------------------------------- the simulator's guards

def test_the_simulator_plays_the_games_defence():
    import difficulty_sim as ds
    src = open(ds.__file__, encoding='utf-8').read()
    fight = src.split('def fight(', 1)[1].split('def _between_rounds', 1)[0]
    assert 'defence_mod.world_turns' in fight                  # the game's scheduler rule
    assert 'max(10.0' not in fight                             # under 10 is no longer 10
    body = src.split('def _body_value', 1)[1].split('def _spell_mult', 1)[0]
    assert 'get_speed' in body and 'dodge_chance' in body and 'get_ac' in body
    run = ds.Run(ds.FloorCache(1), 'mastery', 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
    assert type(run.p).get_ac is not Player.get_ac             # only the 'ac' knob's wrapper
    assert type(run.p).get_speed is Player.get_speed
    assert type(run.p).dodge_chance is Player.dodge_chance
    assert type(run.p).load_tier is Player.load_tier


def test_the_simulators_defence_knobs_change_the_rules_and_go_back():
    import difficulty_sim as ds
    file_per = defence.rules()['dodge_per_dex']
    try:
        ds.apply_defence_knobs(ds.parse_knobs('dodge_per_dex=0.03,heavy_drag=0.2,heavy_speed=0.3'))
        assert defence.rules()['dodge_per_dex'] == 0.03
        assert defence.rules()['armour_drag']['heavy'] == 0.2
        assert defence.rules()['armour_drag']['medium'] == _rules()['defence']['armour_drag']['medium']
        assert defence.load_rules()['heavy']['speed'] == 0.3
        ds.apply_defence_knobs(ds.parse_knobs(''))
        assert defence.rules()['dodge_per_dex'] == file_per
    finally:
        defence.reset()


def test_the_simulators_kids_keep_under_the_line_that_slows():
    import difficulty_sim as ds
    run = ds.Run(ds.FloorCache(1), 'mastery', 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
    assert run._pack_line() == run.p.heavy_threshold() == run._need_line()
    dex = ds.Run(ds.FloorCache(1), 'mastery_dex', 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
    assert dex._pack_line() == dex.p.light_threshold()
    assert dex._need_line() == dex.p.heavy_threshold()


def test_the_simulators_dexterity_kid_wears_light_armour_and_the_plate_kid_chooses():
    import difficulty_sim as ds
    assert ds.PROFILES['mastery_dex']['armour_class'] == 'light'
    assert ds.PROFILES['b_hermes']['armour_class'] == 'light'
    assert 'armour_class' not in ds.PROFILES['mastery']
    dex = ds.Run(ds.FloorCache(1), 'mastery_dex', 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
    dex.fs = ds.new_floor_stats()
    dex.consider(items.instantiate_armor('full_plate', 'chain_steel'))
    assert gear.body_class(dex.p) == 'light'                    # plate left on the floor
    dex.consider(items.instantiate_armor('studded_leather', 'studded_leather'))
    assert gear.body_armour(dex.p) is not None and gear.body_class(dex.p) == 'light'
    plate = ds.Run(ds.FloorCache(1), 'mastery', 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
    plate.fs = ds.new_floor_stats()
    plate.p.STR = 20
    plate.consider(items.instantiate_armor('full_plate', 'chain_steel'))
    assert gear.body_class(plate.p) == 'heavy'


def test_importing_the_simulator_patches_nothing():
    """The simulator's item cache and bones stub are installed by run_cell
    (install_caches), never at import: a test that imported it for one check
    handed every later test in its process the same shared item objects
    (the ring-appearance tests failed under xdist, 2026-11-16)."""
    import subprocess
    code = ("import sys; sys.path[:0] = ['src', 'tools/balance']; import items, level_manager; "
            "real = items.load_items; bones = level_manager.LevelManager._maybe_spawn_bones; "
            "import difficulty_sim as ds; "
            "assert items.load_items is real and not ds._CACHES_ON; "
            "assert level_manager.LevelManager._maybe_spawn_bones is bones; "
            "ds.install_caches(); assert items.load_items is not real; print('ok')")
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', PQ_NO_BONES='1')
    out = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env,
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0 and 'ok' in out.stdout, out.stderr[-2000:]


def test_the_simulators_kitchen_parts_weigh_nothing():
    """Brandon, 2026-11-16: ingredients weigh nothing (food keeps its
    weight). A pantry of two hundred parts tips no load line, and none of
    it is left behind to lighten one."""
    import copy
    import difficulty_sim as ds
    import food_system
    import kitchen
    run = ds.Run(ds.FloorCache(1), 'mastery_dex', 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
    run.fs = ds.new_floor_stats()
    iid = next(i for i in kitchen.ingredients() if kitchen.is_harvested(i))
    part = ds.weightless_part(food_system.load_ingredient_for(iid))
    assert run._wt(part) == 0.0 and float(part.weight) == 0.0
    before = run.p.get_current_weight()
    run.pantry = [copy.copy(part) for _ in range(200)]
    run._sync_pack()
    assert len(run.pantry) == 200
    assert run.p.get_current_weight() == pytest.approx(before)
    assert run.p.load_tier() == ''


def test_the_simulator_plays_the_kids_builds_without_their_easter_eggs():
    import difficulty_sim as ds
    for cell, (build, base) in ds.BUILD_CELLS.items():
        b = ds.secret_builds()[build]
        run = ds.Run(ds.FloorCache(1), cell, 0.95, 1.0, 'greedy', 1, ds.parse_knobs(''))
        for s in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'):
            assert getattr(run.p, s) == b[s], (cell, s)
        assert run.p.weapon is not None, cell
        carried = [getattr(i, 'id', '') for i in run.p.worn_items() + run.p.inventory]
        for egg in ('dreamspun_sketchbook', 'unusual_soul_sphere', 'charmander_stuffie',
                    'caviar', 'tater_tots'):
            assert egg not in carried, (cell, egg)
    assert set(ds.BUILD_CELLS) == {'b_fianna', 'b_fluffs', 'b_corwin', 'b_cain',
                                   'b_hermes', 'b_odysseus'}
