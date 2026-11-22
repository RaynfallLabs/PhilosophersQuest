"""A pack keeps together (Brandon's play-test of 3.6.1, 2026-11-22: "Dire rats
spawned, but they were all over the floor... I didn't see two together at
all").

Two causes, both measured on real floors: a pack's extras were set down on
any free tile of its room, and while it had no prey each member roamed the
floor on its own (the vermin's job is 'wander' seven times in ten), so a pack
set down together was 8 to 10 tiles apart within 50 to 200 turns. Now the
extras are set down beside the first, and an idle pack follows its head.
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)
_G = None


def _cheb(a, b) -> int:
    return max(abs(a.x - b.x), abs(a.y - b.y))


def _game():
    global _G
    from main import Game
    from game_states import STATE_PLAYER
    if _G is None:
        random.seed(11)
        _G = Game(pygame.display.set_mode((1, 1)), player_name='__test_packs_together__')
        _G._autosave = lambda *a, **k: None
    _G.state = STATE_PLAYER
    _G.monsters, _G.pets, _G.ground_items = [], [], []
    _G.player.status_effects.clear()
    _G.player.max_hp = _G.player.hp = 100000
    return _G


def _three_rooms(g):
    """Three rooms joined by passages, and the hero shut in a box far off
    (no sight, no sound, no way to him)."""
    from dungeon import FLOOR, WALL, Room
    d = g.dungeon
    rooms = [Room(2, 2, 11, 9), Room(30, 2, 11, 9), Room(16, 20, 11, 9)]
    for y in range(d.height):
        for x in range(d.width):
            d.tiles[y][x] = WALL
    for r in rooms:
        for x, y in r.inner_tiles():
            d.tiles[y][x] = FLOOR
    for x in range(12, 31):
        d.tiles[6][x] = FLOOR
    for y in range(7, 21):
        d.tiles[y][21] = FLOOR
    hx, hy = d.width - 4, d.height - 4
    for x in range(hx - 1, hx + 2):
        for y in range(hy - 1, hy + 2):
            d.tiles[y][x] = FLOOR
    d.rooms = rooms
    d.traps = {}
    d.fixture_blocks = d.fixture_opaque = frozenset()
    g.player.x, g.player.y = hx, hy
    return rooms


@pytest.mark.parametrize('kind', ['dire_rat', 'giant_rat', 'jackal', 'wolf'])
def test_a_pack_is_set_down_beside_its_first(kind):
    import dungeon
    from dungeon import Room, generate_dungeon
    d = generate_dungeon(80, 50, 3)
    d.traps = {}
    room = Room(5, 5, 20, 12)
    for x, y in room.inner_tiles():
        d.tiles[y][x] = dungeon.FLOOR
    eligible = {kind: {**MONS[kind], '_spawn_freq': 1.0}}
    far = 0
    for seed in range(40):
        monsters = []
        assert dungeon._spawn_one_in_room(room, eligible, d, monsters, random.Random(seed))
        head = monsters[0]
        far += sum(_cheb(o, head) > 2 for o in monsters[1:])
    assert far == 0


@pytest.mark.parametrize('kind', ['dire_rat', 'jackal'])
def test_an_idle_pack_goes_about_as_one(kind):
    from monster import Monster
    g = _game()
    rooms = _three_rooms(g)
    uid = f'test-{kind}'
    pack = []
    for at in ((5, 5), (8, 6), (6, 8)):
        m = Monster({**MONS[kind], 'id': kind}, *at)
        m._pack = uid
        m._job = 'wander'
        m._home = at
        pack.append(m)
    g.monsters = list(pack)
    random.seed(4)
    start = (pack[0].x, pack[0].y)
    together = samples = 0
    visited = set()
    for turn in range(300):
        g.state = 'player'
        g._do_monster_turns()
        for i, r in enumerate(rooms):
            if any(r.x < m.x < r.x + r.width - 1 and r.y < m.y < r.y + r.height - 1 for m in pack):
                visited.add(i)
        if turn % 10 == 9:
            samples += 1
            together += all(min(_cheb(a, b) for b in pack if b is not a) <= 3 for a in pack)
    assert not any(m._aware for m in pack)          # it never knew of the hero
    assert (pack[0].x, pack[0].y) != start and len(visited) >= 2   # it went about
    assert together >= 0.85 * samples, (together, samples)


def test_the_head_is_the_leader_kind_when_one_is_with_it():
    import packs
    from monster import Monster
    wolves = [Monster({**MONS['wolf'], 'id': 'wolf'}, 5, 5),
              Monster({**MONS['wolf_pack_leader'], 'id': 'wolf_pack_leader'}, 6, 5),
              Monster({**MONS['wolf'], 'id': 'wolf'}, 7, 5)]
    for w in wolves:
        w._pack = 'wolves@5,5'
    assert packs.head_of(wolves[0], wolves) is wolves[1]
    assert packs.head_of(wolves[1], wolves) is wolves[1]
    wolves[1].alive = False
    assert packs.head_of(wolves[2], wolves) is wolves[0]
    lone = Monster({**MONS['wolf'], 'id': 'wolf'}, 9, 9)
    assert packs.head_of(lone, wolves + [lone]) is None
