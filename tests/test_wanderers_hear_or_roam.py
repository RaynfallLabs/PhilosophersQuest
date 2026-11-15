"""A wandering newcomer goes to see a fight only if it could hear it (3.5.1).

Brandon, play-testing floor 1: "walking across the floor and back, I'm
getting spammed by monsters... and they're all coming right at me".

Every newcomer was handed the place of the hero's last fight, from anywhere
on the floor, though a fight carries five tiles (data/senses.json noise).
On the same 24 floor-1 maps, 173 of 197 newcomers were sent straight at him.
A newcomer is now led to a recent loud noise only when that sound reaches
the tile it came in on, along open ground, as any sound travels
(senses.sound_map). Otherwise it roams like any other monster, and hears or
sees the hero only by its own senses.
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

import pygame  # noqa: E402

pygame.init()

from test_bug_bash_5_encounters import _game  # noqa: E402

WALL, FLOOR = 0, 1
ROW = 5

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _corridor(g, length=60):
    """One straight corridor along ROW, the hero at its west end, nothing
    else on the floor (no stairs, so no stair-side preference)."""
    d = g.dungeon
    for y in range(d.height):
        for x in range(d.width):
            d.tiles[y][x] = FLOOR if (y == ROW and 2 <= x < 2 + length) else WALL
    d.fixture_blocks = set()
    g.player.x, g.player.y = 2, ROW
    g.monsters = []
    g.pets = []
    g.visible = {(2, ROW), (3, ROW)}
    from floor_curve import wander_interval
    g.turn_count = wander_interval(g.dungeon_level) * 40


def _spawn_one(g, explored):
    """Run the wanderer check with ``explored`` as the only places a
    newcomer may come in; return the newcomer."""
    import dungeon as D
    from monster import Monster
    g.dungeon.explored = set(explored)
    real = D.spawn_monsters
    D.spawn_monsters = lambda *a, **k: [Monster({**MONS['giant_rat'], 'id': 'giant_rat'}, 0, 0)]
    try:
        g._maybe_wander_spawn()
    finally:
        D.spawn_monsters = real
    assert len(g.monsters) == 1, 'no newcomer spawned'
    return g.monsters[0]


def test_a_fight_records_how_far_it_carries():
    import senses
    g = _game(1)
    g._make_noise('melee')
    loud = g.dungeon._last_loud
    assert len(loud) == 4 and loud[3] == senses.noise_radius('melee') == 5
    g._make_noise('alarm')
    assert g.dungeon._last_loud[3] == senses.noise_radius('alarm')


def test_a_newcomer_far_from_the_fight_roams():
    random.seed(7)
    g = _game(1)
    _corridor(g)
    g.dungeon._last_loud = (2, ROW, g.turn_count - 5, 5)     # a fight at the hero
    m = _spawn_one(g, {(x, ROW) for x in range(30, 60)})
    assert m.__dict__.get('_goal') is None, (m.x, m.y, m.__dict__.get('_goal'))
    assert m.__dict__.get('_lead_used') is True


def test_a_newcomer_within_earshot_goes_to_see():
    random.seed(7)
    g = _game(1)
    _corridor(g)
    g.dungeon._last_loud = (35, ROW, g.turn_count - 5, 5)    # a fight out east
    m = _spawn_one(g, {(x, ROW) for x in range(33, 38)})
    assert m.__dict__.get('_goal') == (35, ROW)


def test_an_alarm_reaches_further_than_a_fight():
    random.seed(7)
    g = _game(1)
    _corridor(g)
    # Twelve tiles from the hero: out of a fight's reach, inside an alarm's.
    spot = {(14, ROW)}
    g.dungeon._last_loud = (2, ROW, g.turn_count - 5, 5)
    assert _spawn_one(g, spot).__dict__.get('_goal') is None
    g.monsters = []
    g.dungeon._last_loud = (2, ROW, g.turn_count - 5, 12)
    assert _spawn_one(g, spot).__dict__.get('_goal') == (2, ROW)


def test_sound_does_not_pass_through_stone():
    random.seed(7)
    g = _game(1)
    _corridor(g)
    g.dungeon.tiles[ROW][10] = WALL                           # the corridor is cut
    g.dungeon._last_loud = (8, ROW, g.turn_count - 5, 12)
    assert _spawn_one(g, {(12, ROW)}).__dict__.get('_goal') is None


def test_an_old_fight_or_an_old_saves_mark():
    random.seed(7)
    g = _game(1)
    _corridor(g)
    # Too long ago: no lead, however near.
    g.dungeon._last_loud = (35, ROW, g.turn_count - 41, 5)
    assert _spawn_one(g, {(36, ROW)}).__dict__.get('_goal') is None
    # An old save's mark has no reach: it is taken as a fight's.
    g.monsters = []
    g.dungeon._last_loud = (35, ROW, g.turn_count - 5)
    assert _spawn_one(g, {(36, ROW)}).__dict__.get('_goal') == (35, ROW)
