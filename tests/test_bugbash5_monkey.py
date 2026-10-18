"""Bug bash 5 (2026-10-17), the monkey fuzzer's findings (MNK-01, 04, 07,
08, 09) on a real headless Game.

All of these are rare or deep (Setne's tomb on floors 45-65, a 2x2 body on
floors 74-91, a packed corridor, a long disease on floor 80), so they are
proven here, not by play-test.
"""
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

from test_bug_bash_5_encounters import _game, _tomb  # noqa: E402
from test_shep import _open_room  # noqa: E402

WALL, FLOOR = 0, 1


def _boss(mid, x, y):
    from boss_levels import _load_boss
    from monster import Monster
    return Monster(_load_boss(mid), x, y)


def _pocket(g, tiles):
    for y in range(g.dungeon.height):
        for x in range(g.dungeon.width):
            g.dungeon.tiles[y][x] = FLOOR if (x, y) in tiles else WALL


# ---------------------------------------------------------------- MNK-01

def test_mnk01_a_monster_in_the_tomb_doorway_is_put_outside_not_walled_in():
    from geom import occupied_tiles
    g = _game(5)
    ghosts = _tomb(g)
    room = g._setne['room']
    door, out = tuple(room['door']), tuple(room['outside'])
    chamber = [tuple(t) for t in room['chamber']]
    busy = {(m.x, m.y) for m in g.monsters if m.alive}
    g.player.x, g.player.y = next(t for t in chamber if t not in busy)
    for m in g.monsters:
        if (m.x, m.y) == out:
            m.alive = False
    lurker = _boss('lich_lord', *door)
    g.monsters.append(lurker)
    g._encounter_seal_room(ghosts[0])
    assert g.dungeon.tiles[door[1]][door[0]] == WALL
    assert lurker.alive
    assert all(g.dungeon.is_walkable(*t) for t in occupied_tiles(lurker))
    assert (g.player.x, g.player.y) not in set(occupied_tiles(lurker))
    assert (lurker.x, lurker.y) not in chamber


# ---------------------------------------------------------------- MNK-04

def test_mnk04_settle_moves_a_2x2_body_off_the_hero_and_out_of_rock():
    from geom import occupied_tiles
    g = _game(4)
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    g.monsters = []
    g.pets = []
    big = _boss('gashadokuro', x - 1, y - 1)        # the hero under its SE tile
    assert tuple(big.footprint) == (2, 2)
    g.monsters.append(big)
    g._settle_monsters()
    tiles = set(occupied_tiles(big))
    assert (x, y) not in tiles
    assert all(g.dungeon.is_walkable(*t) for t in tiles)


def test_mnk04_wander_spawn_never_sets_a_2x2_body_half_in_a_wall():
    import dungeon as D
    from geom import occupied_tiles
    g = _game(4)
    g.monsters = []
    g.pets = []
    real = D.spawn_monsters
    D.spawn_monsters = lambda *a, **k: [_boss('gashadokuro', 0, 0)]
    try:
        dn = g.dungeon
        px, py = g.player.x, g.player.y
        g.visible = set()
        g.turn_count = max(10, 22 - g.dungeon_level // 4) * 50
        # Only floor with rock to the east: no 2x2 body fits on these.
        dn.explored = {(x, y) for y in range(dn.height) for x in range(dn.width)
                       if dn.is_walkable(x, y) and not dn.is_walkable(x + 1, y)
                       and abs(x - px) + abs(y - py) >= 8}
        assert dn.explored
        g._maybe_wander_spawn()
        assert g.monsters == []
        # With open floor, a 2x2 body lands whole on it.
        dn.explored = {(x, y) for y in range(dn.height) for x in range(dn.width)
                       if dn.is_walkable(x, y) and abs(x - px) + abs(y - py) >= 8}
        for _ in range(20):
            g._maybe_wander_spawn()
            if g.monsters:
                break
        assert g.monsters
        for m in g.monsters:
            assert all(t in dn.explored for t in occupied_tiles(m))
    finally:
        D.spawn_monsters = real


# ---------------------------------------------------------------- MNK-06

def test_mnk06_knockback_checks_a_2x2_bodys_whole_new_footprint():
    from combat import apply_knockback
    from geom import occupied_tiles
    g = _game(4)
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    g.monsters, g.pets = [], []
    big = _boss('gashadokuro', x + 1, y)            # tiles (x+1..x+2, y..y+1)
    g.monsters.append(big)
    g.dungeon.tiles[y + 1][x + 3] = WALL            # rock under its new SE tile
    apply_knockback(g.player, big, g.dungeon, g.monsters, occupied=g._occupants())
    assert (big.x, big.y) == (x + 1, y)
    assert all(g.dungeon.is_walkable(*t) for t in occupied_tiles(big))
    g.dungeon.tiles[y + 1][x + 3] = FLOOR
    apply_knockback(g.player, big, g.dungeon, g.monsters, occupied=g._occupants())
    assert (big.x, big.y) == (x + 2, y)


# ---------------------------------------------------------------- MNK-07

def test_mnk07_the_codex_sketch_helper_never_stands_on_the_hero():
    import hero_specials as HS
    g = _game(2)
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    g.monsters, g.pets = [], []
    HS._eff_summon_sketch_helper(g, {}, {'duration': 10, 'level': 3}, 3)
    assert len(g.pets) == 1
    assert (g.pets[0].x, g.pets[0].y) != (x, y)
    assert g.dungeon.is_walkable(g.pets[0].x, g.pets[0].y)


def test_mnk07_with_no_room_the_sketch_fades_and_nothing_stacks():
    import hero_specials as HS
    g = _game(2)
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    g.monsters, g.pets = [], []
    _pocket(g, {(x, y)})
    assert HS._eff_summon_sketch_helper(g, {}, {'duration': 10, 'level': 3}, 3) is HS.NOTHING
    assert g.pets == []


def test_mnk07_the_dreamspun_sketch_never_lands_on_the_hero_when_crowded():
    from quiz_engine import QuizResult
    from test_shep import _monster
    g = _game(2)
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    g.pets = []
    # Every neighbour taken; open floor two tiles out.
    g.monsters = [_monster(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                  if (dx, dy) != (0, 0)]
    target = g.monsters[0]
    g.visible = {(i, j) for j in range(g.dungeon.height) for i in range(g.dungeon.width)}
    g._pending_power = 'sketch_manifest'
    g.target_cursor_x, g.target_cursor_y = target.x, target.y
    g._confirm_power_target()
    g.quiz_engine.callback(QuizResult(success=True, score=2, correct=2, asked=2))
    assert len(g.pets) == 1
    pet = g.pets[0]
    assert (pet.x, pet.y) != (x, y)
    assert not any((m.x, m.y) == (pet.x, pet.y) for m in g.monsters)
    assert g.dungeon.is_walkable(pet.x, pet.y)


# ---------------------------------------------------------------- MNK-08

def test_mnk08_disease_never_drains_below_one_and_names_the_right_stat():
    import status_effects as SE
    g = _game(3)
    p = g.player
    p.status_effects.pop('poison_resist', None)
    p.status_effects.pop('drain_resist', None)
    random.seed(1)
    lines = set()
    for _ in range(4000):
        p.status_effects['diseased'] = 50
        p.hp = p.max_hp = max(p.max_hp, 10 ** 6)
        for t, _kind in SE.tick_all(p, g.dungeon):
            if 'saps' in t:
                lines.add(t)
    assert p.STR == 1 and p.CON == 1
    assert 'The disease saps your strength! STR -1.' in lines
    assert 'The disease saps your health! CON -1.' in lines
    assert not any('strength! CON' in t for t in lines)


# ---------------------------------------------------------------- MNK-09

def test_mnk09_an_escort_with_no_room_nearby_never_lands_on_the_hero():
    g = _game(2)
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    g.monsters, g.pets = [], []
    # A corridor: nothing free within 3, one free tile at 5.
    _pocket(g, {(x + i, y) for i in range(6)})
    g.monsters = [_boss('lich_lord', x + i, y) for i in range(1, 5)]
    esc = g._spawn_escort({'id': 'e', 'name': 'Escort', 'hp': 9})
    assert esc is not None and (esc.x, esc.y) == (x + 5, y)
    # Walled in alone: no escort rather than one on the hero.
    _pocket(g, {(x, y)})
    g.monsters = []
    g.escorts = []
    assert g._spawn_escort({'id': 'e', 'name': 'Escort', 'hp': 9}) is None
    assert g.escorts == []
