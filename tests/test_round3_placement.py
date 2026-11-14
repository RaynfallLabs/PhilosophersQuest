"""Round 3 (2026-11-14), the flaky tests: what they found in the game.

Seven tests failed now and then under the full parallel suite. Four of them
had found real faults on rare floors, fixed in the game and pinned here:

- loot moved within reach (or out of a pool) was laid on the nearest
  walkable tile: a stair, an altar, a tile already holding a thing, or a
  trader's blanket; and the run's trader chose his spot before the lore
  pieces and the zoo and barracks keepers were set down, so a sown warrior
  and the Scroll of the Lake of Fire turned up on Old Mags' stall;
- a statue set down after the Hellmouth was seated could make its tile the
  only way to the real stair (a maze corridor, a doorway);
- with no bridge or doorway that left a way round, the Black Knight was set
  down on any free tile, which could be the only corridor through;
- a small special room whose wall tiles all stood beside a way in was left
  bare (about one graveyard in eight).

These are rare, randomized floors: logic tests stand in for play.
"""
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

from dungeon import (ALTAR, FLOOR, STAIRS_DOWN, STAIRS_UP, WALL, WATER,  # noqa: E402
                     Dungeon, Room, generate_dungeon)

_CODE = {'#': WALL, '.': FLOOR, '~': WATER, '<': STAIRS_UP, '>': STAIRS_DOWN, '_': ALTAR}


def _floor(rows):
    tiles = [[_CODE[c] for c in row] for row in rows]
    h, w = len(rows), len(rows[0])
    return Dungeon(tiles, [Room(0, 0, w, h)], w, h, 30)


def _bare_game(d, items, hero=(1, 1), monsters=()):
    """A Game with only what _bring_within_reach reads."""
    from main import Game
    g = Game.__new__(Game)
    g.dungeon = d
    g.dungeon_level = 30
    g.player = types.SimpleNamespace(x=hero[0], y=hero[1])
    g.monsters, g.ground_items, g.pets = list(monsters), list(items), []
    return g


def _loot(x, y):
    return types.SimpleNamespace(x=x, y=y, id='bread_ration', name='Bread Ration')


# A pool rings the loot at (5, 2); the hero walks the three columns on the
# left. (3, 2) is the nearest tile he can reach.
_POCKET = ['#########',
           '#<..~~~.#',
           '#...~.~.#',
           '#...~~~.#',
           '#########']


@pytest.mark.parametrize('what', ['stair', 'altar', 'trader', 'item'])
def test_loot_brought_within_reach_lands_on_plain_floor_with_nothing_on_it(what):
    """Moved within reach, a thing lies where the floor's own loot would
    (dungeon._place_one): never on a stair or an altar that hides it, never
    under a trader's blanket or on another thing."""
    from mystery_system import MerchantNPC
    rows = list(_POCKET)
    others = []
    if what == 'stair':
        rows[2] = '#..>~.~.#'
    elif what == 'altar':
        rows[2] = '#.._~.~.#'
    elif what == 'trader':
        others.append(MerchantNPC(3, 2, [], []))
    else:
        others.append(_loot(3, 2))
    d = _floor(rows)
    loot = _loot(5, 2)
    g = _bare_game(d, [loot] + others)
    reach = g._reachable_tiles(1, 1)
    assert (5, 2) not in reach and (3, 2) in reach
    g._bring_within_reach()
    assert (loot.x, loot.y) in reach
    assert (loot.x, loot.y) != (3, 2)                       # the nearest tile was not plain or not free
    assert d.tiles[loot.y][loot.x] == FLOOR
    assert all((o.x, o.y) == (3, 2) for o in others)        # the others stay where they are
    assert max(abs(loot.x - 3), abs(loot.y - 2)) <= 1       # the next nearest plain tile


def test_loot_washed_out_of_a_pool_lands_on_plain_floor_too():
    """An item under water (a pool carved after the loot was set down) is
    laid on the nearest plain floor with nothing on it, not on the stair."""
    rows = ['#######',
            '#<..###',
            '#..>~##',
            '#...###',
            '#######']
    d = _floor(rows)
    wet = _loot(4, 2)                       # the stair is the one walkable tile beside it
    g = _bare_game(d, [wet])
    g.escorts = []
    g._bring_within_reach = lambda: None
    g._settle_monsters()
    assert (wet.x, wet.y) != (3, 2) and d.tiles[wet.y][wet.x] == FLOOR
    assert abs(wet.x - 4) + abs(wet.y - 2) == 2


def test_a_needed_creature_is_never_moved_onto_the_trader():
    """A seal keeper on an island comes to the nearest tile the hero can
    walk to, but not onto a trader's blanket."""
    from mystery_system import MerchantNPC
    d = _floor(_POCKET)
    keeper = types.SimpleNamespace(x=5, y=2, alive=True, kind='seal_demon_war', tags=['demon'],
                                   treasure={}, footprint=(1, 1))
    stall = MerchantNPC(3, 2, [], [])
    g = _bare_game(d, [stall], monsters=[keeper])
    g._bring_within_reach()
    assert (keeper.x, keeper.y) in g._reachable_tiles(1, 1)
    assert (keeper.x, keeper.y) != (stall.x, stall.y)


def test_the_trader_chooses_his_spot_after_everything_else_is_down():
    """On his floor the trader is placed after the lore pieces, the keepers
    of a zoo or a barracks and the settling of the floor, so nothing lands
    on his stall after he has chosen it."""
    from main import Game
    import items
    random.seed(5)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_round3_trader__')
    order = []
    real_settle, real_spawn = g._settle_monsters, g._maybe_spawn_trader

    def settle():
        order.append('settle')
        return real_settle()

    def spawn(level):
        order.append('trader')
        return real_spawn(level)
    g._settle_monsters, g._maybe_spawn_trader = settle, spawn
    g._change_level(19, enter_from_top=True)
    assert order == ['settle', 'trader']
    from mystery_system import MerchantNPC
    (t,) = [i for i in g.ground_items if isinstance(i, MerchantNPC)]
    assert not any((i.x, i.y) == (t.x, t.y) for i in g.ground_items if i is not t)
    assert not any((m.x, m.y) == (t.x, t.y) for m in g.monsters)


def test_a_lore_piece_is_laid_on_plain_floor_with_nothing_on_it():
    """The deep-lore pieces go near the middle of a room: on plain floor,
    never on a stair, an altar or another thing (the comment said so; the
    code took any walkable tile)."""
    from main import Game
    import items
    random.seed(3)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_round3_lore__')
    d = g.dungeon
    lvl = g.dungeon_level
    rooms = d.rooms[1:-1] or d.rooms
    near = [(r.center[0] + dx, r.center[1] + dy) for r in rooms
            for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
    near = [t for t in near if d.in_bounds(*t) and d.is_walkable(*t)]
    keep = near[-1]
    g.ground_items = []
    for i, (x, y) in enumerate(near[:-1]):
        if i % 2:
            d.tiles[y][x] = ALTAR                    # an altar: walkable, but not plain
        else:
            g.ground_items.append(_loot(x, y))
    d.tiles[keep[1]][keep[0]] = FLOOR
    (d.__dict__.get('fixtures') or {}).pop(keep, None)
    d.fixture_blocks.discard(keep)
    g._lore_levels['fire_scroll'] = lvl
    g._lore_placed.discard('fire_scroll')
    g._maybe_place_lore_items(d, lvl)
    (scroll,) = [i for i in g.ground_items if getattr(i, 'id', '') == 'scroll_lake_of_fire']
    assert (scroll.x, scroll.y) == keep


# ---------------------------------------------------------------- the Hellmouth

def _hellmouth(x, y):
    import json
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        defn = json.load(f)['hellmouth']
    return Monster({**defn, 'id': 'hellmouth'}, x, y)


def test_a_statue_across_the_way_round_moves_the_hellmouth_when_seated_again():
    """Three corridors join the stairs. The Hellmouth lies in the top one,
    with the others for a way round. Statues across both of them make its
    tile the only way through; seated again, it moves where it cuts
    nothing off."""
    import decor
    import false_stairs
    rows = ['###############',
            '#<............#',
            '#.###########.#',
            '#.............#',
            '#.###########.#',
            '#............>#',
            '###############']
    d = _floor(rows)
    d.rooms = [Room(0, 0, 3, 3)]                     # the arrival room: the corner only
    hm = _hellmouth(7, 1)
    up, down = (1, 1), (13, 5)
    assert false_stairs.poses_as_stairs(hm)
    false_stairs.seat(d, [hm])
    assert (hm.x, hm.y) == (7, 1)                    # a good tile: it stays
    decor.place(d, (7, 3), 'stalagmite')             # the floor is dressed after
    decor.place(d, (7, 5), 'stalagmite')
    assert down not in false_stairs._walk(d, up, blocked={(7, 1)})
    false_stairs.seat(d, [hm])
    assert (hm.x, hm.y) != (7, 1)
    assert down in false_stairs._walk(d, up, blocked={(hm.x, hm.y)})


def test_a_generated_floor_is_seated_again_once_it_is_dressed(monkeypatch):
    """LevelManager.generate seats the Hellmouth, dresses the floor, then
    seats it again (one that still leaves a way round stays put)."""
    import decor
    import false_stairs
    import level_manager
    calls = []
    real_seat, real_dress = false_stairs.seat, decor.dress_floor

    def seat(d, monsters, rng=None):
        calls.append('seat')
        return real_seat(d, monsters, rng)

    def dress(*a, **k):
        calls.append('dress')
        return real_dress(*a, **k)
    monkeypatch.setattr(false_stairs, 'seat', seat)
    monkeypatch.setattr(decor, 'dress_floor', dress)
    level_manager.LevelManager().generate(87)
    assert calls == ['seat', 'dress', 'seat']


def test_a_hellmouth_never_lies_on_a_fixture():
    """'Only on plain floor': a rug, a drift or a stalagmite's tile is not."""
    import decor
    import false_stairs
    rows = ['############',
            '#<.........#',
            '#..........#',
            '#.........>#',
            '############']
    d = _floor(rows)
    up, down = (1, 1), (10, 3)
    reach = false_stairs._walk(d, up)
    d.rooms = [Room(0, 0, 3, 3)]                    # the arrival room: the corner only
    assert false_stairs.good_tile(d, 4, 2, reach, up, down)
    decor.place(d, (4, 2), 'ash_drift')
    assert not false_stairs.good_tile(d, 4, 2, false_stairs._walk(d, up), up, down)


# ---------------------------------------------------------------- the Black Knight

def test_with_no_bridge_and_no_doorway_he_stands_in_a_room_with_a_way_round(monkeypatch):
    """With no corridor for a bridge and every doorway taken, he stands on
    a tile in a room (never the arrival room) where he cuts nothing off.
    He used to be set down on any free tile, which could be the only
    corridor through."""
    import black_knight as bk
    monkeypatch.setattr(bk, '_bridge_candidates', lambda *a, **k: [])
    found = 0
    for seed in range(12):
        d = generate_dungeon(80, 50, 15 + seed % 5, rng=random.Random(seed))
        start = d.rooms[0].center
        doorways = {t for r in d.rooms for t in r.wall_tiles()}
        site = bk.find_site(d, start, random.Random(seed), taken=doorways)
        if site is None:
            continue
        found += 1
        assert site['kind'] == 'room'
        kx, ky = site['knight']
        first = d.rooms[0]
        assert not (first.x <= kx < first.x + first.width and first.y <= ky < first.y + first.height)
        before = [row[:] for row in d.tiles]
        bk.build_bridge(d, site)
        assert d.tiles == before                   # no water, no bridge: just the tile
        assert bk.has_way_round(d, start, (kx, ky))
    assert found >= 10


def test_he_waits_rather_than_stand_in_the_only_way_through(monkeypatch):
    """When no tile on the floor leaves a way round, he does not come."""
    import black_knight as bk
    from main import Game
    import items
    random.seed(7)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_round3_bk__')
    g._black_knight = {'floor': g.dungeon_level, 'spawned': False, 'outcome': None,
                       'sword_dropped': False}
    monkeypatch.setattr(bk, 'find_site', lambda *a, **k: None)
    before = len(g.monsters)
    g._maybe_spawn_black_knight(g.dungeon_level)
    assert len(g.monsters) == before and not g._black_knight['spawned']
