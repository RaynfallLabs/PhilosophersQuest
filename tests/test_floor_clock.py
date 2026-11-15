"""The floor's clock (3.5.1, src/wanderers.py): time to explore, then a
trickle; and floors peopled when they are made.

Brandon, play-testing floor 1: "I just don't think we need a constant stream
of monsters... I'd rather have a larger population at first, with complex
encounters set up, then a trickle if you hang around TOO LONG, but give the
player some time to explore... walking back and forth becomes a massive
chore."

Late-floor pacing and the war-band rolls are random and deep, so they are
proven here, not by play-test: the dials (floor_curve), the clock (pure),
the Game's turn (headless), and the data (war_bands.json).
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, HERE)

import floor_curve  # noqa: E402
import wanderers  # noqa: E402
from dungeon import Dungeon, Room, WALL, FLOOR, STAIRS_UP, STAIRS_DOWN  # noqa: E402

ROW = 5


def _corridor_floor():
    """One straight corridor along ROW from x=2 to x=61: the up stair at
    the west end, the down stair at the east end, two rooms' centres on it."""
    w, h = 70, 12
    tiles = [[WALL] * w for _ in range(h)]
    for x in range(2, 62):
        tiles[ROW][x] = FLOOR
    tiles[ROW][2] = STAIRS_UP
    tiles[ROW][61] = STAIRS_DOWN
    rooms = [Room(19, ROW - 1, 3, 3), Room(39, ROW - 1, 3, 3)]   # centres (20, 5) and (40, 5)
    return Dungeon(tiles, rooms, w, h, 1)


# ------------------------------------------------------------------ the dials

def test_the_grace_is_the_floors_own_explore_and_then_some():
    assert floor_curve.wander_grace(0) == floor_curve.WANDER_GRACE_FLAT
    assert floor_curve.wander_grace(224) == round(floor_curve.WANDER_GRACE_FLAT
                                                  + floor_curve.WANDER_GRACE_PER_TILE * 224)
    # A thorough explore walks about 1.5 tours; the grace is more than that.
    assert floor_curve.wander_grace(224) > 1.5 * 224


def test_the_trickle_starts_slow_and_quickens_to_the_floors_pace():
    for level in (1, 25, 50, 75, 100):
        gaps = [floor_curve.wander_gap(level, past) for past in range(0, 2000, 50)]
        assert gaps[0] == max(floor_curve.WANDER_TRICKLE_START, floor_curve.wander_interval(level))
        assert gaps[-1] == floor_curve.wander_interval(level)
        assert all(a >= b for a, b in zip(gaps, gaps[1:])), (level, gaps)


# ------------------------------------------------------------ the clock, pure

def test_the_explore_tour_walks_every_room_then_the_down_stair():
    d = _corridor_floor()
    # Up stair (2) -> room (20) -> room (40) -> down stair (61).
    assert wanderers.explore_tour(d) == 59
    assert d._explore_tour == 59            # kept on the floor


def test_nothing_comes_while_the_hero_explores():
    d = _corridor_floor()
    g = wanderers.grace(d)
    said = []
    for t in range(1, g):
        say, due = wanderers.advance(d, 1, t)
        assert not due, t
        if say:
            said.append((t, say))
    # One warning, near the end of the grace.
    assert said == [(int(g * floor_curve.WANDER_WARN_SHARE), 'warning')]
    say, due = wanderers.advance(d, 1, g)
    assert (say, due) == ('stirs', True)


def test_then_a_trickle_that_quickens():
    d = _corridor_floor()
    g = wanderers.grace(d)
    times = []
    for t in range(1, g + 3000):
        if wanderers.advance(d, 1, t)[1]:
            times.append(t)
    gaps = [b - a for a, b in zip(times, times[1:])]
    assert times[0] == g
    assert gaps[0] == floor_curve.WANDER_TRICKLE_START
    assert gaps[-1] == floor_curve.wander_interval(1)
    assert all(a >= b for a, b in zip(gaps, gaps[1:]))


def test_a_floor_settles_while_the_hero_is_away():
    d = _corridor_floor()
    g = wanderers.grace(d)
    t = 0
    for t in range(1, g + 500):
        wanderers.advance(d, 1, t)
    c = wanderers.clock(d)
    assert c['stirred']
    # Away for a long while (a trader three floors up): back to one full
    # tour of quiet, and the lines may be said again.
    t += 2000
    say, due = wanderers.advance(d, 1, t)
    assert not due
    quiet_from = g - max(100, wanderers.explore_tour(d))
    assert c['here'] == quiet_from + 1
    assert not c['stirred']


def test_a_hop_down_the_stair_and_back_buys_nothing():
    d = _corridor_floor()
    g = wanderers.grace(d)
    for t in range(1, g + 500):
        wanderers.advance(d, 1, t)
    before = wanderers.clock(d)['here']
    wanderers.advance(d, 1, g + 500 + 3)        # two turns away
    assert wanderers.clock(d)['here'] == before + 1
    # Ten turns away settles ten turns, no more.
    wanderers.advance(d, 1, g + 500 + 3 + 11)
    assert wanderers.clock(d)['here'] == before + 2 - 10


def test_leaving_during_the_grace_keeps_what_is_left_of_it():
    d = _corridor_floor()
    for t in range(1, 50):
        wanderers.advance(d, 1, t)
    wanderers.advance(d, 1, 5000)
    assert wanderers.clock(d)['here'] == 50


def test_the_lines_are_there():
    for key in ('warning', 'stirs'):
        text = wanderers.line(key, random.Random(1))
        assert text and text[0].isupper() and text.endswith('.'), (key, text)


# ------------------------------------------------------------ the Game's turn

def test_a_fresh_floor_one_brings_in_no_newcomer_for_a_long_explore():
    from test_bug_bash_5_encounters import _game
    g = _game(3)
    # Even a floor already thinned out (the alive cap would allow one).
    for m in g.monsters:
        m.alive = False
    g.dungeon.explored = {(x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)
                          if g.dungeon.is_walkable(x, y)}
    g.visible = set()
    grace = wanderers.grace(g.dungeon)
    assert grace >= floor_curve.WANDER_GRACE_FLAT + 2 * 100
    for _ in range(grace - 1):
        g.turn_count += 1
        g._maybe_wander_spawn()
    assert [m for m in g.monsters if m.alive] == []
    # Then the floor stirs, said once, and newcomers come.
    msgs = []
    g.add_message = lambda text, *a, **k: msgs.append(text)
    for _ in range(400):
        g.turn_count += 1
        g._maybe_wander_spawn()
    assert any(m.alive for m in g.monsters)
    stirs = set(wanderers._lines()['stirs'])
    assert sum(1 for t in msgs if t in stirs) == 1


# ------------------------------------------------------------ the floors' own

def test_the_top_floors_hold_small_war_bands_from_their_own_pool():
    import dungeon
    import war_bands
    d = war_bands.data()
    assert int(d['first_floor']) == 1
    small = [bid for bid, b in d['bands'].items() if b['floors'][0] == 1]
    assert set(small) == {'goblin_scouts', 'footpads'}
    for floor in (1, 2, 4, 6):
        pool = dungeon._floor_pool(floor, None)
        for bid in small:
            b = d['bands'][bid]
            assert any(k in pool for k in b['leader']), (floor, bid)
            assert any(k in pool for k in b['guard']), (floor, bid)
        assert war_bands.pick_band(floor, pool, random.Random(floor)) is not None
    for bid in small:
        b = d['bands'][bid]
        for key in ('line', 'known_line', 'rout_line', 'break_line'):
            assert b[key].strip(), (bid, key)
        assert '{roster}' in b['known_line']


def test_a_floor_is_peopled_when_it_is_made():
    import dungeon
    assert dungeon.MIN_FLOOR_MONSTERS >= 8
    assert dungeon.FLOOR_DENSITY_BASE >= 0.6
    with open(os.path.join(ROOT, 'data', 'war_bands.json'), encoding='utf-8') as f:
        assert json.load(f)['chance'] >= 0.5


def test_the_floor_stirs_only_when_something_really_comes():
    """A floor still as full as it began takes no newcomer (the alive cap),
    so "things will come looking now" waits for the first that does
    (bug bash 3.5.1 C: a sneaking hero heard it and nothing came)."""
    from test_bug_bash_5_encounters import _game
    import floor_curve as fc
    g = _game(4)
    g.dungeon.explored = {(x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)
                          if g.dungeon.is_walkable(x, y)}
    g.visible = set()
    for m in g.monsters:
        m._tracking = False
    # A floor made with fewer than the cap is filled to it. (The floors are
    # not the seed's: a part-made rat, with no symbol, failed on the runs
    # that drew a thin floor 1. Bug bash 3.5.1 E.)
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        rat = {**json.load(f)['giant_rat'], 'id': 'giant_rat'}
    while sum(1 for m in g.monsters if m.alive) < fc.wander_alive_cap(g.dungeon_level):
        g.monsters.append(Monster(dict(rat), 0, 0))
    msgs = []
    g.add_message = lambda text, *a, **k: msgs.append(text)
    stirs = set(wanderers._lines()['stirs'])
    for _ in range(wanderers.grace(g.dungeon) + 300):
        g.turn_count += 1
        g._maybe_wander_spawn()
    assert not any(t in stirs for t in msgs)
    n = len(g.monsters)
    for m in g.monsters:
        m.alive = False                       # the hero thins the floor
    for _ in range(300):
        g.turn_count += 1
        g._maybe_wander_spawn()
    assert len(g.monsters) > n
    assert sum(1 for t in msgs if t in stirs) == 1
