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
        # Each follower tests his nerve (no hero here: on his next turn), or
        # one of them took up the lead; none is simply frightened.
        new = out.get('successor')
        assert not any(m.has_effect('feared') for m in rest)
        for m in rest:
            if m is new:
                assert m._band_role == 'leader'
            elif new is None:
                assert m._morale_check == 'leader' or not m.__dict__.get('_band_leader')
    else:
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
    # A great blow is great (data great_blow): a chain of 8 and a third of
    # his health; an ordinary chain of 7, or a scratch, shakes no one.
    assert war_bands.on_great_blow([lead] + gobs, lead, 7) == ''
    assert war_bands.on_great_blow([lead] + gobs, lead, 9, damage=1) == ''
    line = war_bands.on_great_blow([lead] + gobs, lead, 8, damage=lead.max_hp // 3 + 1)
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


def test_a_band_heard_on_arrival_is_never_named():
    """2026-11-12: "...Goblins have made camp." told the hero what he had
    not seen. The plain line is sound and signs only."""
    import re
    for bid, b in war_bands.data()['bands'].items():
        words = {w for w in re.findall(r'[a-z]+', b['name'].lower()) if len(w) >= 5}
        low = b['line'].lower()
        for w in words:
            assert w not in low, (bid, w, b['line'])


def test_observe_on_a_band_member_says_what_anyone_can_see():
    b = war_bands.data()['bands']['necro_procession']
    assert war_bands.observe_line(b, 'guard', False) == 'It marches with a necromancer and his dead.'
    lead = war_bands.observe_line(b, 'leader', False)
    assert 'waiting for orders' in lead and 'fall' not in lead
    known = war_bands.observe_line(b, 'leader', True)
    assert known.startswith('It leads the band.') and 'the dead it raised will fall with it' in known
    assert 'turn on one another' in war_bands.observe_line(
        war_bands.data()['bands']['demon_warband'], 'leader', True)


def test_the_arrival_names_the_band_only_for_a_hero_who_knows_its_leader():
    from types import SimpleNamespace
    from game_combat import CombatMixin

    class G:
        _announce_band = CombatMixin._announce_band

        def __init__(self, hero, band, monsters):
            self.player, self.monsters, self.msgs = hero, monsters, []
            self.dungeon = SimpleNamespace(band=band)

        def add_message(self, text, cat='info'):
            self.msgs.append(text)

    def said(studied=(), grants=None):
        leader = _m('goblin_king')
        leader._band, leader._band_role = 'u1', 'leader'
        band = {'id': 'goblin_raiders', 'uid': 'u1', 'leader_kind': 'goblin_king',
                'counts': {'guard': 2, 'shooter': 1}, 'said': False}
        hero = SimpleNamespace(studied_monster_ids=set(studied), lore_known_monster_ids=set(),
                               family_lore_grants=dict(grants or {}))
        g = G(hero, band, [leader])
        g._announce_band()
        return g.msgs[0]

    plain = war_bands.data()['bands']['goblin_raiders']['line']
    assert said() == plain
    assert said(grants={'goblinkin': 1}) == plain, 'Recognise does not name the band'
    # Named, with its make-up: a cue (2026-11-22). How to break it is the
    # leader's Observe line.
    named = 'Goblin war-drums. A leader, two fighters and one archer.'
    assert said(studied=('goblin_king',)) == named
    assert said(grants={'goblinkin': 3}) == named


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
