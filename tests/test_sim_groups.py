"""The simulator's group fight (tools/balance/sim_groups.py, 2026-11-20).

difficulty_sim.fight meets a room's group `engagers` at a time; the rest wait
at the back. These tests put small scripted groups through the back rank's
turn and the fight's hooks, each mechanic with its knob on (it fires) and at
0 (it does not), and hold the simulator's world clock to the game's own turn
loop (Game._advance_turn): a creature of any speed gets the same turns in the
simulator as in a real Game over the same hero actions.
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

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


# ------------------------------------------------------------------ helpers

def _sim(knobs='', engagers=2, profile='unprepared', floor=5):
    import difficulty_sim as ds
    import sim_ai1
    import sim_ai2
    import sim_ai3
    run = ds.Run(ds.FloorCache(1), profile, 0.95, 1.0, 'greedy', engagers, ds.parse_knobs(knobs))
    for mod in (sim_ai1, sim_ai2, sim_ai3):
        mod.apply_flags(run.knobs)          # a worker's earlier cell may have left them off
    run.fs = ds.new_floor_stats()
    run.floor = floor
    run.turn = 100
    run.p.max_hp = run.p.hp = 5000
    return ds, run


def _mon(ds, run, kind, **kw):
    from monster import Monster
    proto = Monster({**MONS[kind], 'id': kind}, 0, 0)
    for k, v in kw.items():
        setattr(proto, k, v)
    return ds.fresh_monster(proto, run.knobs, run.floor)


def _turns(run, active, queue, n):
    import sim_groups
    for i, m in enumerate(active):
        m.x, m.y = sim_groups.SLOTS[i]
    for _ in range(n):
        run.turn += 1
        queue = sim_groups.back_rank(run, active, queue, {}, True)
    return queue


def _band(ds, run, leader_kind, roles):
    """A war-band of fresh copies, as the floor makes one (src/war_bands.py:
    the leader first; each follower's _band_leader is the floor's creature,
    the cached one the copies are made from)."""
    from monster import Monster
    uid = 'footpads@1,1'
    lead_proto = Monster({**MONS[leader_kind], 'id': leader_kind}, 0, 0)
    lead_proto._band, lead_proto._band_id, lead_proto._band_role = uid, 'footpads', 'leader'
    protos = [lead_proto]
    for kind, role in roles:
        o = Monster({**MONS[kind], 'id': kind}, 0, 0)
        o._band, o._band_id, o._band_role, o._band_leader = uid, 'footpads', role, lead_proto
        protos.append(o)
    return [ds.fresh_monster(p, run.knobs, run.floor) for p in protos]


# ------------------------------------------------------------------ the knobs

def test_every_group_knob_is_in_the_simulator_and_on():
    import difficulty_sim as ds
    import sim_groups
    for k in ('grp_heal', 'grp_summon', 'grp_book', 'grp_backrank', 'grp_orders',
              'grp_morale', 'grp_speed'):
        assert sim_groups.KNOBS[k] == 1
        assert ds.KNOB_DEFAULTS[k] == 1


def test_the_ground_has_the_front_the_engagers_name():
    import sim_groups
    for k, n in ((1, 1), (2, 3), (3, 3), (8, 8)):
        g = sim_groups.ground(sim_groups.shape_for(k))
        assert len(sim_groups.front_tiles(g)) == n
        back = sim_groups.back_tiles(g)
        assert back and all(max(abs(x - 5), abs(y - 5)) >= 2 for x, y in back)
    corridor = sim_groups.back_tiles(sim_groups.ground('corridor'))
    assert all(x >= 7 for x, _y in corridor)              # nothing behind the hero


# ------------------------------------------------------------------ grp_heal

def test_a_healer_at_the_back_mends_the_front_and_not_with_its_knob_off():
    import sim_groups
    for on in (1, 0):
        random.seed(3)
        ds, run = _sim(f'grp_heal={on}', engagers=1)
        front = _mon(ds, run, 'cult_initiate')
        front.hp = max(1, front.max_hp // 4)
        priest = _mon(ds, run, 'cult_priest')
        queue = sim_groups.fight_start(run, [front, priest], [priest])
        hp0 = front.hp
        _turns(run, [front], queue, 3)
        if on:
            assert front.hp > hp0 and run.fs.get('grp_heals', 0) >= 1
        else:
            assert front.hp == hp0 and not run.fs.get('grp_heals')


def test_a_seeded_group_fight_has_its_healer_mend():
    """Run.fight itself, the corridor (one at a time): the priest at the
    back mends the initiates in front of him."""
    for on in (1, 0):
        heals = 0
        for seed in range(6):
            random.seed(seed)
            ds, run = _sim(f'grp_heal={on}', engagers=1)
            run.p.max_hp = run.p.hp = 400
            group = [_mon(ds, run, 'cult_initiate', max_hp=60, hp=60) for _ in range(2)]
            group.append(_mon(ds, run, 'cult_priest'))
            run.fight(group)
            heals += run.fs.get('grp_heals', 0)
        assert (heals > 0) == bool(on), (on, heals)


# ------------------------------------------------------------------ grp_summon

def test_a_summoner_at_the_back_calls_its_dead_and_no_blow_breaks_the_chant():
    import sim_groups
    for on in (1, 0):
        random.seed(4)
        ds, run = _sim(f'grp_summon={on}', engagers=1, floor=11)
        front = _mon(ds, run, 'skeleton')
        nec = _mon(ds, run, 'skeleton_necromancer')
        queue = sim_groups.fight_start(run, [front, nec], [nec])
        queue = _turns(run, [front], queue, 12)
        made = [m for m in queue if m.__dict__.get('_summoned_by') is nec]
        if on:
            assert made and len(made) <= 2 and run.fs.get('grp_summons', 0) == len(made)
            assert queue.index(made[0]) < queue.index(nec)      # its dead come up before it
        else:
            assert not made and not run.fs.get('grp_summons')


# ------------------------------------------------------------------ grp_book

def test_a_caster_at_the_back_casts_from_its_book():
    import sim_groups
    for on in (1, 0):
        random.seed(6)
        ds, run = _sim(f'grp_book={on}', engagers=1)
        front = _mon(ds, run, 'goblin')
        shaman = _mon(ds, run, 'goblin_shaman')
        queue = sim_groups.fight_start(run, [front, shaman], [shaman])
        _turns(run, [front], queue, 4)
        if on:
            assert run.fs.get('grp_casts', 0) >= 1           # its curse, chanted then cast
        else:
            assert not run.fs.get('grp_casts') and not shaman.__dict__.get('_spells_cast')


# ------------------------------------------------------------------ grp_backrank

def test_an_archer_at_the_back_shoots_past_the_front_but_never_down_a_corridor():
    import sim_groups
    for engagers, on, shoots in ((2, 1, True), (2, 0, False), (1, 1, False)):
        random.seed(5)
        ds, run = _sim(f'grp_backrank={on}', engagers=engagers)
        front = _mon(ds, run, 'bandit_thug')
        archer = _mon(ds, run, 'bandit_archer')
        queue = sim_groups.fight_start(run, [front, archer], [archer])
        _turns(run, [front], queue, 8)
        assert (run.fs.get('grp_shots', 0) > 0) == shoots, (engagers, on, run.fs.get('grp_shots'))
        assert max(abs(archer.x - 5), abs(archer.y - 5)) >= 2    # never past the front


# ------------------------------------------------------------------ grp_orders

def test_the_captains_screen_sends_his_guards_first():
    import sim_groups
    for on, hurt, screened in ((1, False, True), (0, False, False), (1, True, False)):
        random.seed(7)
        ds, run = _sim(f'grp_orders={on}', engagers=1)
        if hurt:
            run.p.hp = run.p.max_hp // 4                 # a hurt hero: the captain calls the charge
        group = _band(ds, run, 'bandit_captain', [('bandit_archer', 'shooter'),
                                                  ('bandit_thug', 'guard'), ('brigand', 'guard')])
        queue = sim_groups.fight_start(run, group, list(group))
        roles = [m._band_role for m in queue]
        if screened:
            assert roles == ['guard', 'guard', 'leader', 'shooter']
        else:
            assert roles == ['leader', 'shooter', 'guard', 'guard']


def test_half_the_band_down_falls_back_and_waits_at_the_back():
    import sim_groups
    for on in (1, 0):
        random.seed(8)
        ds, run = _sim(f'grp_orders={on}', engagers=1)
        group = _band(ds, run, 'bandit_captain', [('bandit_thug', 'guard')] * 5)
        lead, guards = group[0], group[1:]
        sim_groups.fight_start(run, group, list(group))
        for g in guards[:4]:
            g.hp, g.alive = 0, False
        active, queue = [lead], [guards[4]]
        run.turn += 1
        queue = _turns(run, active, queue, 1)
        got = sim_groups.next_up(run, queue, active)
        if on:
            assert got is None and run.fs.get('grp_fall_back', 0) == 1
        else:
            assert got is guards[4]


# ------------------------------------------------------------------ grp_morale

def test_a_follower_answers_to_the_leader_in_this_fight():
    import morale
    import sim_groups
    for on in (1, 0):
        random.seed(9)
        ds, run = _sim(f'grp_morale={on}', engagers=1)
        lead, thug = _band(ds, run, 'bandit_captain', [('bandit_thug', 'guard')])
        sim_groups.fight_start(run, [lead, thug], [thug])
        assert (thug._band_leader is lead) == bool(on)
        lead.hp, lead.alive = 0, False
        sim_groups.deaths(run, [lead], [thug])
        if on:
            assert thug._under('feared') and run.fs.get('grp_band_rout') == 1
            assert not morale.held_by_others(thug, run.p)
        else:
            assert not thug._under('feared')
            assert morale.held_by_others(thug, run.p)     # the floor's leader never dies


def test_kin_falling_shakes_the_hurt_who_saw_it():
    import sim_groups
    for on in (1, 0):
        random.seed(10)
        ds, run = _sim(f'grp_morale={on}', engagers=2)
        a, b = _mon(ds, run, 'bandit_thug'), _mon(ds, run, 'bandit_thug')
        sim_groups.fight_start(run, [a, b], [])
        a.x, a.y, b.x, b.y = 6, 5, 5, 6
        b.hp = b.max_hp // 3
        a.hp, a.alive = 0, False
        sim_groups.deaths(run, [a, b], [])
        assert (b.__dict__.get('_morale_check') == 'kin') == bool(on)


def test_a_great_blow_on_the_captain_shakes_his_band():
    import sim_groups
    for on in (1, 0):
        random.seed(11)
        ds, run = _sim(f'grp_morale={on}', engagers=8)
        group = _band(ds, run, 'bandit_captain', [('bandit_thug', 'guard')] * 6)
        lead = group[0]
        sim_groups.fight_start(run, group, [])
        sim_groups.deaths(run, group, [])                # the marks: his health, the chain
        lead.hp -= 5
        run.quiz.chain_sum += 7                          # a chain of seven landed on him
        sim_groups.deaths(run, group, [])
        shaken = sum(1 for m in group[1:] if m._under('feared'))
        assert (shaken > 0) == bool(on) and bool(run.fs.get('grp_great_blows')) == bool(on)


# ------------------------------------------------------------------ grp_speed: the clock

_GAME = {}


def _game():
    """One real Game for the clock tests (Game._advance_turn as played)."""
    if 'g' in _GAME:
        return _GAME['g']
    import pygame
    pygame.init()
    from main import Game
    from game_states import STATE_PLAYER
    from dungeon import FLOOR
    random.seed(12)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_sim_groups__')
    g.state = STATE_PLAYER
    g.pets = []
    g.dungeon.traps = {}
    g._maybe_wander_spawn = lambda *a, **k: None
    g._autosave = lambda *a, **k: None
    x = min(max(g.player.x, 10), g.dungeon.width - 11)
    y = min(max(g.player.y, 10), g.dungeon.height - 11)
    for i in range(-9, 10):
        for j in range(-9, 10):
            g.dungeon.tiles[y + j][x + i] = FLOOR
    g.player.x, g.player.y = x, y
    p = g.player
    p.max_hp = p.hp = 10 ** 6
    p.max_sp = p.sp = 10 ** 6
    _GAME['g'] = g
    return g


def _skeleton(speed):
    from monster import Monster
    m = Monster({**MONS['skeleton'], 'id': 'skeleton'}, 0, 0)
    m.speed = speed
    m._aware = m._tracking = m._alerted = True
    return m


def _set_speed(p, hero):
    p.__dict__.pop('get_speed', None)
    p.status_effects.pop('hasted', None)
    if hero == 'hasted':
        p.status_effects['hasted'] = 10 ** 6
    else:
        p.get_speed = lambda slow=None, v=float(hero): v / 2 if slow else v


def _game_turns(mspeed, hero, n, slowed=0):
    g = _game()
    m = _skeleton(mspeed)
    m.x, m.y = g.player.x + 1, g.player.y
    if slowed:
        m.status_effects['slowed'] = slowed
    hits = []
    m.attack = lambda player: (hits.append(1), (0, ''))[1]
    g.monsters = [m]
    _set_speed(g.player, hero)
    g._world_clock = 0.0
    for _ in range(n):
        g._advance_turn()
    _set_speed(g.player, 10.0)
    return len(hits)


def _sim_turns(mspeed, hero, n, slowed=0, knobs=''):
    """The simulator's fight loop over n hero actions (Run.fight, to its
    MAX_FIGHT_TURNS): the blows the world's turns give the foe."""
    ds, run = _sim(knobs, engagers=1)
    m = ds.fresh_monster(_skeleton(mspeed), run.knobs, run.floor)
    m.max_hp = m.hp = 10 ** 6
    if slowed:
        m.status_effects['slowed'] = slowed
    hits = []
    in_world = []
    m.attack = lambda player: (hits.append(1) if in_world else None, (0, ''))[1]
    real_tick = run._world_tick

    def world_tick(active, ctx, ticks=True, acts=True):
        in_world.append(1)
        try:
            return real_tick(active, ctx, ticks=ticks, acts=acts)
        finally:
            in_world.pop()
    run._world_tick = world_tick
    run._player_attack = lambda target, active: None      # the hero leaves it be
    _set_speed(run.p, hero)
    old = ds.MAX_FIGHT_TURNS
    ds.MAX_FIGHT_TURNS = n
    try:
        assert run.fight([m]) == 'stalemate'
    finally:
        ds.MAX_FIGHT_TURNS = old
    return len(hits)


@pytest.mark.parametrize('mspeed', [10, 13, 14, 20])
@pytest.mark.parametrize('hero', [10.0, 'hasted', 9.0, 12.5])
def test_a_creature_gets_the_games_turns_at_any_speed(mspeed, hero):
    """Over 90 hero actions, a creature beside him strikes as often in the
    simulator as in the real Game: its own speed gives it no extra turns
    (none at 13, 14 or 20), the hero's sets the world's."""
    n = 90
    got = _game_turns(mspeed, hero, n)
    assert got == _sim_turns(mspeed, hero, n)
    want = {10.0: n, 'hasted': n // 2, 9.0: n * 10 // 9, 12.5: n * 4 // 5}[hero]
    assert abs(got - want) <= 1, (got, want)


def test_a_slow_creature_loses_the_games_share_of_its_turns():
    n = 600
    got, sim = _game_turns(5, 10.0, n), _sim_turns(5, 10.0, n)
    assert abs(got - 0.7 * n) < 0.07 * n and abs(sim - 0.7 * n) < 0.07 * n, (got, sim)


def test_a_slowed_foe_and_a_hasted_hero_tick_once_an_action():
    """Slowed for 20 turns, beside a hasted hero: the game counts the 20
    down by his actions (Game._advance_turn ticks the statuses once an
    action), so it is slowed for 10 world turns, not 20. The simulator does
    the same with grp_speed, and did not without it."""
    n = 40
    game = _game_turns(10, 'hasted', n, slowed=20)
    assert game == _sim_turns(10, 'hasted', n, slowed=20)
    assert game != _sim_turns(10, 'hasted', n, slowed=20, knobs='grp_speed=0')


def test_a_slowed_hero_loses_no_blow_every_action_takes_two_turns(monkeypatch):
    """The effects pass (2026-11-22): Slowed is the world's clock for every
    key (Player.get_speed halves), no longer every other step or blow lost."""
    import combat
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    move = src.split('def _do_move', 1)[1].split('\n    def ', 1)[0]
    assert '_slow_skip' not in move
    blows = []
    monkeypatch.setattr(combat, 'player_attack', lambda *a, **k: blows.append(1))
    ds, run = _sim('')
    foe = _mon(ds, run, 'skeleton')
    fast = run.p.get_speed()
    run.p.status_effects['slowed'] = 10
    assert run.p.get_speed() == pytest.approx(fast / 2)
    assert all(run.player_can_act() for _ in range(4))
    for _ in range(6):
        run._player_attack(foe, [foe])
    assert len(blows) == 6


def test_a_quick_creature_strikes_on_arrival_half_the_time_it_closes():
    """Monster._standard_move: at speed 14 it takes two steps, and strikes
    in the turn it arrives only when the first of them brings it beside the
    hero. Closing on a waiting hero from three to eight tiles off, that is
    about half the time (sim_groups.FAST_OPENING_BLOW); from two tiles off
    (the queue behind the front), always."""
    import sim_groups
    g = _game()
    x, y = g.player.x, g.player.y
    blows = []
    for d in range(2, 9):
        m = _skeleton(14)
        m.x, m.y = x + d, y
        g.monsters = [m]
        got = False
        for _ in range(10):
            got = m.take_turn(g.player, g.dungeon, g.monsters)
            if m._adjacent_to(g.player):
                break
        assert m._adjacent_to(g.player)
        if d == 2:
            assert got is True
        else:
            blows.append(bool(got))
    share = sum(blows) / len(blows)
    assert abs(share - sim_groups.FAST_OPENING_BLOW) <= 0.2, (share, blows)
    for on in (1, 0):
        random.seed(13)
        ds, run = _sim(f'grp_speed={on}')
        quick = _skeleton(14)
        firsts = [sim_groups.arrival(run, quick, 1, True) for _ in range(400)]
        later = [sim_groups.arrival(run, quick, 1, False) for _ in range(20)]
        assert all(later)
        if on:
            assert abs(sum(firsts) / 400 - sim_groups.FAST_OPENING_BLOW) < 0.08
        else:
            assert all(firsts)


# ------------------------------------------------------------------ all off

def test_with_every_group_knob_off_the_fight_is_the_old_one(monkeypatch):
    """Every knob at 0: the same seeded fights, hit for hit, as with the
    group fight's hooks taken out of the loop (no back rank, no reordering,
    the clock's ticks every world turn): the ablation is the old simulator."""
    import difficulty_sim as ds
    import sim_groups
    off = ','.join(f'{k}=0' for k in sim_groups.KNOBS)

    def fights():
        out = []
        for seed in range(4):
            random.seed(100 + seed)
            _ds, run = _sim(off, engagers=2)
            run.p.max_hp = run.p.hp = 300
            run.p.status_effects['slowed'] = 30
            group = _band(ds, run, 'bandit_captain', [('bandit_archer', 'shooter'),
                                                      ('bandit_thug', 'guard'), ('cult_priest', 'healer'),
                                                      ('goblin_shaman', 'caster')])
            group.append(_mon(ds, run, 'skeleton_necromancer'))
            group.append(_mon(ds, run, 'skeleton', speed=15))
            res = run.fight(group)
            out.append((res, run.p.hp, [m.hp for m in group], run.turn,
                        sorted(k for k in run.fs if k.startswith('grp_'))))
            random.random()
        return out
    with_hooks = fights()
    assert all(r[4] == [] for r in with_hooks)          # no group mechanic counted anything
    monkeypatch.setattr(sim_groups, 'fight_start', lambda run, group, queue: queue)
    monkeypatch.setattr(sim_groups, 'deaths', lambda run, active, queue: None)
    monkeypatch.setattr(sim_groups, 'next_up', lambda run, queue, active: queue.pop(0))
    monkeypatch.setattr(sim_groups, 'back_rank', lambda run, active, queue, ctx, tick=True, act=True: queue)
    monkeypatch.setattr(sim_groups, 'arrival', lambda run, m, free, opening: free)
    monkeypatch.setattr(sim_groups, 'ticks_now', lambda run, w: True)
    monkeypatch.setattr(sim_groups, 'tick_alone', lambda run, n: False)
    assert fights() == with_hooks
