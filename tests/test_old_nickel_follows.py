"""Old Nickel follows the hero out of his room (Brandon's play-test,
2026-11-22: "he wont follow me out of a room, instead getting stuck on the
edge").

Out of his sight, he goes all the way to where he last saw or heard the hero
(footsteps carry round corners: senses.sound_map) and on from there. A hero
who makes no sound still loses him. An elbow of a passage is no corner to be
caught in. While he plays the friend, the hero's pets keep their teeth off
him and he is no reason to stop dressing.
"""
import os
import random
import sys
from collections import deque

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()
_G = None
EIGHT = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
FOUR = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def _game():
    global _G
    from main import Game
    from game_states import STATE_PLAYER
    if _G is None:
        random.seed(7)
        _G = Game(pygame.display.set_mode((1, 1)), player_name='__test_nickel_follows__')
        _G._autosave = lambda *a, **k: None
    _G.state = STATE_PLAYER
    _G.player.status_effects.clear()
    _G.player.max_hp = _G.player.hp = 100000
    _G.player.sp = _G.player.max_sp
    _G.monsters, _G.pets, _G.ground_items = [], [], []
    return _G


def _carve(g, *boxes):
    """An all-stone floor with these boxes (x0, y0, x1, y1) cut out of it."""
    from dungeon import FLOOR, WALL
    d = g.dungeon
    for y in range(d.height):
        for x in range(d.width):
            d.tiles[y][x] = WALL
    for x0, y0, x1, y1 in boxes:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                d.tiles[y][x] = FLOOR
    d.traps = {}
    d.fixture_blocks = d.fixture_opaque = frozenset()


def _nickel(g, at, revealed):
    import emberpup_encounter as ep
    from monster import Monster
    m = Monster(ep.wearer_defn(), *at)
    m._hoard = tuple(at)
    m._revealed = revealed
    g.monsters.append(m)
    g.visible = set()
    g._refresh_fov()
    return m


def _walk(g, *legs):
    for dx, dy, n in legs:
        for _ in range(n):
            g._do_move(dx, dy)


def _way(d, start, goal, steps=EIGHT):
    from dungeon import DOOR
    prev = {start: None}
    q = deque([start])
    while q:
        c = q.popleft()
        if c == goal:
            out = []
            while c != start:
                out.append(c)
                c = prev[c]
            return out[::-1]
        for a, b in steps:
            n = (c[0] + a, c[1] + b)
            if n not in prev and d.in_bounds(*n) and (d.is_walkable(*n) or d.tiles[n[1]][n[0]] == DOOR):
                prev[n] = c
                q.append(n)
    return None


# A room, its doorway at the east, a passage that turns south, then east.
ROOM = (3, 3, 11, 9)
PASSAGES = ((12, 6, 16, 6), (16, 6, 16, 16), (16, 16, 30, 16))


@pytest.mark.parametrize('revealed,keep', [(False, 2), (True, 3)])
def test_he_follows_out_of_the_room_and_round_two_corners(revealed, keep):
    g = _game()
    _carve(g, ROOM, *PASSAGES)
    g.player.x, g.player.y = 9, 6
    m = _nickel(g, (9 - keep, 6), revealed)
    _walk(g, (1, 0, 7), (0, 1, 10), (1, 0, 12))
    assert (g.player.x, g.player.y) == (28, 16)
    assert m.x > 16, (m.x, m.y)                    # out, and round both corners
    assert len(_way(g.dungeon, (m.x, m.y), (28, 16))) <= keep + 2
    assert not m._provoked and m._revealed == revealed


@pytest.mark.parametrize('revealed', [False, True])
def test_out_of_sight_he_goes_all_the_way_to_where_he_last_saw_him(revealed):
    """No sound at all: he still rounds the doorway to the last place."""
    g = _game()
    _carve(g, ROOM, *PASSAGES)
    m = _nickel(g, (14, 6), revealed)
    m._stalk_seen_at = (16, 6)
    m._tracking = True
    m.perception_range = 3
    g.player.x, g.player.y = 16, 14
    for _ in range(2):
        m.take_turn(g.player, g.dungeon, g.monsters)
    assert (m.x, m.y) == (16, 6)


def test_a_silent_hero_round_a_corner_loses_him(monkeypatch):
    import senses
    g = _game()
    _carve(g, ROOM, *PASSAGES)
    monkeypatch.setattr(senses, 'step_radius', lambda p: 0)
    g.player.x, g.player.y = 9, 6
    m = _nickel(g, (7, 6), False)
    m.perception_range = 4
    # out of his short sight: round the corner and far down the passage
    for at in ((16, 14), (30, 16)):
        g.player.x, g.player.y = at
        g._advance_turn()
    for _ in range(50):
        g._advance_turn()
    assert not m._tracking and (m.x, m.y) == m._hoard


def test_a_hero_standing_round_a_corner_is_not_walked_up_to():
    g = _game()
    _carve(g, ROOM, *PASSAGES)
    g.player.x, g.player.y = 16, 8
    m = _nickel(g, (15, 6), True)
    m._stalk_seen_at = (16, 8)
    m._tracking = True
    for _ in range(6):
        assert m.take_turn(g.player, g.dungeon, g.monsters) is False
        assert max(abs(m.x - 16), abs(m.y - 8)) >= 2


@pytest.mark.parametrize('revealed', [False, True])
def test_an_elbow_of_a_passage_is_no_corner_to_be_caught_in(revealed):
    g = _game()
    _carve(g, *PASSAGES)
    g.player.x, g.player.y = 15, 6
    m = _nickel(g, (16, 6), revealed)
    assert m.take_turn(g.player, g.dungeon, g.monsters) is False
    assert (m.x, m.y) == (16, 7) and not m._provoked


def test_a_dead_end_still_corners_him():
    g = _game()
    _carve(g, (12, 6, 16, 6))
    g.player.x, g.player.y = 15, 6
    m = _nickel(g, (16, 6), True)
    assert m.take_turn(g.player, g.dungeon, g.monsters) is True
    assert m._stalk_event == 'cornered'


def test_the_friend_gives_way_before_he_is_walked_into():
    """A quicker hero takes a step in which he has no turn: walking into him
    then was an attack, and the act dropped."""
    g = _game()
    _carve(g, (3, 6, 20, 6))
    g.player.x, g.player.y = 9, 6
    m = _nickel(g, (10, 6), False)
    hp = m.hp
    g._do_move(1, 0)
    assert (g.player.x, g.player.y) == (10, 6) and m.x >= 11
    assert m.hp == hp and not m._revealed and g.state == 'player'


def test_the_friend_squeezes_past_the_heros_pet():
    from pet_system import Pet
    g = _game()
    _carve(g, (3, 6, 20, 6))
    g.player.x, g.player.y = 9, 6
    m = _nickel(g, (10, 6), False)
    pet = Pet('fire', 11, 6)
    g.pets.append(pet)
    g._do_move(1, 0)
    assert (g.player.x, g.player.y) == (10, 6) and m.x >= 11 and pet.x < 10
    assert not m._revealed


@pytest.mark.parametrize('revealed,box', [(False, (3, 6, 10, 6)), (True, (3, 6, 20, 6))])
def test_cornered_or_revealed_walking_into_him_is_still_a_blow(revealed, box):
    g = _game()
    _carve(g, box)
    g.player.x, g.player.y = 9, 6
    m = _nickel(g, (10, 6), revealed)
    g._do_move(1, 0)
    assert (g.player.x, g.player.y) == (9, 6) and (m.x, m.y) == (10, 6)
    assert g.combat_target is m
    g.quiz_engine.__dict__.pop('callback', None)


@pytest.mark.parametrize('speed,steps', [(10, 1), (12, 2)])
def test_he_scurries_only_after_a_quicker_hero(monkeypatch, speed, steps):
    g = _game()
    _carve(g, (3, 6, 20, 6))
    g.player.x, g.player.y = 16, 6
    m = _nickel(g, (9, 6), False)
    monkeypatch.setattr(g.player, 'get_speed', lambda: speed)
    m.take_turn(g.player, g.dungeon, g.monsters)
    assert m.x == 9 + steps


def test_no_pet_breaks_the_friends_peace_until_the_act_drops():
    import lore_powers
    g = _game()
    _carve(g, ROOM)
    g.player.x, g.player.y = 9, 6
    m = _nickel(g, (7, 6), False)
    assert lore_powers.at_peace(m)
    assert not g._busy_watch(m)                    # no reason to stop dressing
    m._struck = True
    assert not lore_powers.at_peace(m)
    m._struck = False
    m._revealed = True
    assert not lore_powers.at_peace(m)


@pytest.mark.parametrize('revealed,keep', [(False, 2), (True, 3)])
def test_on_real_floors_he_is_still_with_him_at_the_far_room(revealed, keep):
    from dungeon import generate_dungeon
    kept = walks = 0
    for seed in range(16):
        g = _game()
        random.seed(seed)
        d = g.dungeon = generate_dungeon(80, 50, 1 + seed % 8)
        g.dungeon_level = 1 + seed % 8
        d.traps = {}
        room = d.rooms[0]
        tiles = [t for t in room.inner_tiles() if d.is_walkable(*t)]
        pairs = [(a, b) for a in tiles for b in tiles
                 if max(abs(a[0] - b[0]), abs(a[1] - b[1])) == keep]
        if not pairs:
            continue
        hero, at = pairs[len(pairs) // 2]
        ways = [_way(d, hero, tuple(r.center), FOUR) for r in d.rooms[1:] if d.is_walkable(*r.center)]
        far = max((w for w in ways if w), key=len, default=None)
        if not far or len(far) < 15:
            continue
        g.player.x, g.player.y = hero
        m = _nickel(g, at, revealed)
        for _ in range(180):
            here = (g.player.x, g.player.y)
            if here == far[-1]:
                break
            p = _way(d, here, far[-1], FOUR)
            if not p or p[0] == (m.x, m.y):
                break
            g._do_move(p[0][0] - here[0], p[0][1] - here[1])
        walks += 1
        w = _way(d, (m.x, m.y), (g.player.x, g.player.y))
        kept += w is not None and len(w) <= keep + 4
    assert walks >= 8
    assert kept >= 0.85 * walks, (kept, walks)


def test_a_pet_is_never_traded_onto_a_dug_pit():
    from pet_system import Pet
    g = _game()
    _carve(g, (3, 6, 20, 6))
    g.player.x, g.player.y = 9, 6
    m = _nickel(g, (10, 6), False)
    pet = Pet('fire', 11, 6)
    g.pets.append(pet)
    old = getattr(g.dungeon, 'pits', set())
    g.dungeon.pits = {(9, 6)}
    try:
        assert not g._old_nickel_gives_way(m)
        assert (pet.x, m.x) == (11, 10)
    finally:
        g.dungeon.pits = old
