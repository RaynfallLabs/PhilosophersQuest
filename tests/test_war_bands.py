"""Dungeon Alive slice 5: war-bands with roles and morale, and the tells
that show what a dangerous creature can do (src/war_bands.py, src/tells.py).
"""
import json
import os
import random
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import senses  # noqa: E402
import tells  # noqa: E402
import war_bands  # noqa: E402
from dungeon import FLOOR, WALL, Dungeon, Room, _floor_pool  # noqa: E402
from monster import Monster  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))


def _m(kind, x=5, y=5):
    return Monster({**MONS[kind], 'id': kind}, x, y)


def test_band_data_names_real_kinds_and_lines():
    d = war_bands.data()
    for bid, b in d['bands'].items():
        for role in ('leader',) + war_bands.ROLES:
            for k in b.get(role, ()):
                assert k in MONS, (bid, k)
        assert b['morale'] in ('rout', 'crumble', 'quarrel'), bid
        for key in ('line', 'known_line', 'rout_line', 'break_line', 'name'):
            assert b.get(key, '').strip(), (bid, key)
        assert '{roster}' in b['known_line'], bid
        lo, hi = b['floors']
        assert 1 <= lo < hi <= 100, bid


def test_a_band_uses_only_kinds_its_floor_allows():
    for level in (5, 15, 30, 50, 75, 95):
        pool = _floor_pool(level)
        for seed in range(20):
            got = war_bands.pick_band(level, pool, random.Random(seed))
            if not got:
                continue
            bid, roster = got
            assert roster['leader'] in pool
            for role in war_bands.ROLES:
                assert all(k in pool for k in roster[role]), (level, bid, role)


def _hall():
    w, h = 30, 16
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, 15):
        for x in range(1, 29):
            tiles[y][x] = FLOOR
    rooms = [Room(0, 0, 6, 6), Room(4, 1, 25, 15)]
    return Dungeon(tiles, rooms, w, h, 12)


def _band(monkeypatch=None, level=12, seed=3):
    d = _hall()
    rng = random.Random(seed)
    old = war_bands.data()['chance']
    war_bands.data()['chance'] = 1.0
    try:
        for _ in range(40):
            mons = []
            members = war_bands.place_band(d, mons, level, rng)
            if members:
                return d, mons, members
    finally:
        war_bands.data()['chance'] = old
    raise AssertionError('no band placed')


def test_a_band_makes_camp_with_a_leader_and_roles():
    d, mons, members = _band()
    roles = [m._band_role for m in members]
    assert roles.count('leader') == 1
    assert len(members) >= 3
    leader = war_bands.leader_of(mons, members[0]._band)
    assert all(getattr(m, '_band_leader', None) is leader for m in members if m is not leader)
    assert d.band['uid'] == members[0]._band
    assert all(m.__dict__.get('_job_fixed') for m in members)


def test_one_spotting_the_hero_rouses_the_band():
    d, mons, members = _band()
    for m in members:
        m.status_effects.pop('sleeping', None)
        m._tracking = False
        m._goal = None
    sentry = members[0]

    class Hero:
        x, y = sentry.x + 1, sentry.y
        status_effects = {}
        equipped_accessories = []
        boons_taken = {}
        DEX = 10

        def has_effect(self, n):
            return False
    assert senses.notice(sentry, Hero(), d, mons, set())
    others = [m for m in members if m is not sentry]
    assert all(m._alerted and m._goal == (Hero.x, Hero.y) for m in others)


def test_the_leader_falls_and_the_band_breaks():
    d, mons, members = _band()
    leader = war_bands.leader_of(mons, members[0]._band)
    leader.alive = False
    out = war_bands.on_death(mons, leader)
    assert out['line']
    rest = [m for m in members if m is not leader]
    b = war_bands.data()['bands'][leader._band_id]
    if b['morale'] == 'rout':
        assert all(m.has_effect('feared') or m.fearless for m in rest)
    assert all(not war_bands.holds_nerve(m) for m in rest)


def test_a_necromancers_dead_crumble_with_him():
    lead = _m('pale_master')
    lead._band, lead._band_id, lead._band_role = 'u', 'necro_procession', 'leader'
    bones = [_m('skeleton', 6, 5), _m('zombie', 7, 5)]
    for b in bones:
        b._band, b._band_id, b._band_role, b._band_leader = 'u', 'necro_procession', 'guard', lead
    lead.alive = False
    out = war_bands.on_death([lead] + bones, lead)
    assert out['effect'] == 'crumble'
    assert set(map(id, out['fall'])) == set(map(id, bones))


def test_devils_turn_on_one_another():
    lead = _m('demon_knight')
    lead._band, lead._band_id, lead._band_role = 'u', 'demon_warband', 'leader'
    dev = _m('bearded_devil', 6, 5)
    dev._band, dev._band_id, dev._band_role, dev._band_leader = 'u', 'demon_warband', 'guard', lead
    lead.alive = False
    war_bands.on_death([lead, dev], lead)
    assert dev.quarrelsome and dev.has_effect('confused')


def test_a_great_blow_on_the_leader_shakes_them():
    random.seed(1)
    lead = _m('hobgoblin_captain')
    lead._band, lead._band_id, lead._band_role = 'u', 'goblin_raiders', 'leader'
    gobs = [_m('goblin', 6 + i, 5) for i in range(8)]
    for g in gobs:
        g._band, g._band_id, g._band_role, g._band_leader = 'u', 'goblin_raiders', 'guard', lead
    assert war_bands.on_great_blow([lead] + gobs, lead, 3) == ''
    line = war_bands.on_great_blow([lead] + gobs, lead, 7)
    assert line and any(g.has_effect('feared') for g in gobs)


def test_a_follower_holds_its_nerve_while_its_leader_lives():
    lead = _m('hobgoblin_captain')
    gob = _m('goblin', 6, 5)
    gob._band_leader = lead
    assert war_bands.holds_nerve(gob)
    lead.alive = False
    assert not war_bands.holds_nerve(gob)


def test_a_band_healer_mends_a_bandmate_of_another_kind():
    priest = _m('orc_priest', 5, 5)
    gob = _m('goblin', 6, 5)
    priest._band = gob._band = 'u'
    priest.tags = ['nothing_shared']
    gob.tags = ['other']
    gob.hp = 1

    class D:
        width = height = 20
        tiles = [[FLOOR] * 20 for _ in range(20)]

        def in_bounds(self, x, y):
            return 0 <= x < 20 and 0 <= y < 20

        def is_walkable(self, x, y):
            return self.in_bounds(x, y)

    class Hero:
        x, y = 15, 15
        status_effects = {}

        def has_effect(self, n):
            return False
    priest._healer_turn(Hero(), D(), [priest, gob], set())
    assert gob.hp > 1


def test_every_tell_key_has_a_line_and_order():
    d = tells.data()
    assert set(d['order']) == set(d['effects'])
    effects = {a.get('effect') for m in MONS.values() for a in m.get('attacks', []) if a.get('effect')}
    assert effects <= set(d['effects']), effects - set(d['effects'])


def test_a_confuser_says_keep_your_distance():
    kinds = [k for k, v in MONS.items()
             if any(a.get('effect') == 'confused' and float(a.get('effect_chance', 0)) >= 0.3
                    for a in v.get('attacks', []))
             and not any(a.get('effect') in ('paralyzed',) for a in v.get('attacks', []))
             and not v.get('gaze_paralyze')
             and v.get('ai_pattern') not in tells._FAR_AIS]     # one that must come close
    m = _m(kinds[0])
    assert 'distance' in tells.lines(m, limit=1)[0]
