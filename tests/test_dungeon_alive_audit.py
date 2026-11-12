"""The Dungeon Alive wiring audit's gaps, pinned (2026-11-12,
_alive_research/audit/WIRING_AUDIT.md G1-G10)."""
import json
import os
import random
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import decor  # noqa: E402
import hazards  # noqa: E402
import war_bands  # noqa: E402
from dungeon import FLOOR, WALL, Dungeon, Room  # noqa: E402
from monster import Monster  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))


def _m(kind, x, y):
    return Monster({**MONS[kind], 'id': kind}, x, y)


def _hall():
    w, h = 30, 16
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, 15):
        for x in range(1, 29):
            tiles[y][x] = FLOOR
    return Dungeon(tiles, [Room(0, 0, 6, 6), Room(4, 1, 25, 15)], w, h, 12)


def test_g2_a_shrine_doorstep_stays_clear():
    d = _hall()
    d.tiles[0][15] = WALL
    d.ariadne_shrine_door = (15, 0)
    spots = decor._against_wall_spots(d.rooms[1], d, set())
    assert all(max(abs(x - 15), abs(y - 0)) > 1 for x, y in spots)


def test_g3_a_band_never_displaces_a_named_foe():
    d = _hall()
    boss = _m('arachne', 15, 8)
    boss.is_mini_boss = True
    mons = [boss]
    old = war_bands.data()['chance']
    war_bands.data()['chance'] = 1.0
    try:
        for seed in range(20):
            war_bands.place_band(d, mons, 12, random.Random(seed))
    finally:
        war_bands.data()['chance'] = old
    assert boss in mons, 'the mini-boss was eaten by a camp'


def test_g4_only_a_right_prayer_seals_a_vent():
    import game_lore_fixtures
    d = _hall()
    decor.place(d, (5, 5), 'smoke_vent')
    d.lore_fixtures = {(5, 5): {'tier': 5}}

    class G(game_lore_fixtures.LoreFixturesMixin):
        def __init__(self):
            self.dungeon = d
            self.msgs = []

        def add_message(self, t, k='info'):
            self.msgs.append(t)

        def _make_noise(self, *a, **k):
            pass

        def _chron(self, *a, **k):
            pass
    g = G()
    spec = decor.lore_fixtures()['fixtures']['smoke_vent']
    g._lore_fixture_resolve((5, 5), 'smoke_vent', spec, False)
    assert (5, 5) not in (d.__dict__.get('sealed_vents') or set())
    decor.place(d, (6, 6), 'smoke_vent')
    d.lore_fixtures[(6, 6)] = {'tier': 5}
    g._lore_fixture_resolve((6, 6), 'smoke_vent', spec, True)
    assert (6, 6) in d.sealed_vents


def test_g9_the_first_d_beside_a_lore_fixture_only_tells_you():
    import game_lore_fixtures
    d = _hall()
    decor.place(d, (6, 5), 'copyist_desk')
    d.lore_fixtures = {(6, 5): {'tier': 1}}

    class P:
        x, y = 5, 5
        WIS = 10

    class G(game_lore_fixtures.LoreFixturesMixin):
        def __init__(self):
            self.dungeon = d
            self.player = P()
            self.dungeon_level = 3
            self.msgs = []
            self.state = 'player'

        def add_message(self, t, k='info'):
            self.msgs.append(t)
    g = G()
    assert g._lore_fixture_offer()
    assert g.state == 'player' and 'D again' in g.msgs[-1]


def test_g10_heavy_beasts_and_floating_things():
    assert hazards.is_heavy(_m('hill_giant', 1, 1))
    assert not hazards.is_heavy(_m('giant_rat', 1, 1))
    assert hazards.floats(_m('bat', 1, 1))
    assert hazards.floats(_m('wraith', 1, 1))
    assert not hazards.floats(_m('goblin', 1, 1))


def test_g7_the_devils_band_can_form_in_the_abyss():
    from dungeon import _floor_pool
    got = [war_bands.pick_band(90, _floor_pool(90), random.Random(s)) for s in range(10)]
    assert any(g and g[0] == 'demon_warband' for g in got)
