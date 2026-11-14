"""Dungeon Alive slice 4: furnished special rooms, the lore fixtures, honest
arrival lines, true lairs and the beehive's keepers (src/decor.py,
src/game_lore_fixtures.py, data/room_dressing.json, data/lore_fixtures.json).
"""
import collections
import os
import random
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import decor  # noqa: E402
from dungeon import FLOOR, WALL, Dungeon, Room, spawn_themed  # noqa: E402


def _no_bones(monkeypatch):
    import bones
    monkeypatch.setattr(bones, 'load_bones', lambda *a, **k: None)


def test_room_dressing_names_real_fixtures_and_rooms():
    fx = decor.fixture_defs()
    rooms = decor.room_dressing()['rooms']
    assert set(rooms) == {'treasury', 'library', 'shrine', 'monster_den', 'zoo', 'beehive',
                          'graveyard', 'barracks', 'swamp', 'throne_room'}
    for rtype, cfg in rooms.items():
        if cfg.get('runner'):
            assert cfg['runner'] in fx
        for layer in ('wall', 'stand', 'floor', 'water'):
            for fid in (cfg.get(layer) or {}).get('ids', {}):
                assert fid in fx, (rtype, fid)
                want = 'floor' if layer == 'water' else layer
                assert fx[fid]['layer'] == want, (rtype, fid)


def test_lore_fixtures_are_whole():
    import game_lore_fixtures
    cfg = decor.lore_fixtures()
    subjects = set(os.listdir(os.path.join(ROOT, 'data', 'questions')))
    seen_subjects = set()
    for fid, d in cfg['fixtures'].items():
        assert fid in decor.fixture_defs(), fid
        if d.get('placement') == 'boss':
            # set only by a gate floor's own dressing (slice 6)
            assert hasattr(game_lore_fixtures.LoreFixturesMixin, f"_lore_reward_{d['reward']}"), fid
            continue
        assert hasattr(game_lore_fixtures.LoreFixturesMixin, f"_lore_reward_{d['reward']}"), fid
        assert d['pass'].strip() and d['fail'].strip() and d['verb'].strip(), fid
        assert any(s.startswith(d['subject']) for s in subjects), (fid, d['subject'])
        seen_subjects.add(d['subject'])
        assert d['subject'] != 'math', 'maths stays the sword'
    assert len(seen_subjects) == len([f for f in cfg['fixtures'].values() if f.get('placement') != 'boss']), 'one subject each'
    assert cfg['per_floor'][1] <= 3


def _open_floor(d, room, monsters, items):
    """The room's plain floor with nothing on it: no creature, no item, no
    trap and no fixture. Furniture never goes under any of those."""
    held = {(m.x, m.y) for m in monsters} | {(i.x, i.y) for i in items}
    held |= set((d.__dict__.get('traps') or {}).keys()) | set(d.__dict__.get('pits') or ())
    fx = d.__dict__.get('fixtures') or {}
    return [(x, y) for y in range(room.y + 1, room.y + room.height - 1)
            for x in range(room.x + 1, room.x + room.width - 1)
            if d.in_bounds(x, y) and d.tiles[y][x] == FLOOR and (x, y) not in held
            and (x, y) not in fx]


def test_generated_floors_furnish_their_special_rooms_and_say_so(monkeypatch):
    """Every special room shows its own furniture, unless it has no open
    floor to hold it: a pool carved over it, or every tile under a sleeper
    or a pile of loot (round 3: that is the rule; the test used to count such
    rooms as bare, and about one run in fifty failed on a ratio over five)."""
    _no_bones(monkeypatch)
    from level_manager import LevelManager
    random.seed(4)                 # before the LevelManager rolls its plan (audit G8)
    lm = LevelManager()
    furnished = collections.Counter()
    rooms_seen = collections.Counter()
    for level in list(range(2, 100)) * 2:
        if level % 20 == 0:
            continue
        d, _m, _i = lm.generate(level)
        fx = d.__dict__.get('fixtures') or {}
        state = d.__dict__.get('lore_fixtures') or {}
        assert len(state) <= 3, level
        for center, rtype in d.special_rooms.items():
            room = next(r for r in d.rooms if tuple(r.center) == tuple(center))
            ids = decor.room_dressing()['rooms'][rtype]
            want = set()
            for layer in ('wall', 'stand', 'floor', 'water'):
                want |= set((ids.get(layer) or {}).get('ids', {}))
            if ids.get('runner'):
                want.add(ids['runner'])
            inside = [fid for (x, y), fid in fx.items()
                      if room.x <= x < room.x + room.width and room.y <= y < room.y + room.height]
            if set(inside) & want:
                furnished[rtype] += 1
                rooms_seen[rtype] += 1
            elif _open_floor(d, room, _m, _i):
                rooms_seen[rtype] += 1          # bare, with floor to furnish
            line = decor.room_dressing()['arrival'].get(rtype)
            if line and len(d.special_rooms) == 1:
                assert line in d.atmosphere_messages, (level, rtype)
        if len(rooms_seen) == 10 and min(rooms_seen.values()) >= 5:
            break
    for rtype, n in rooms_seen.items():
        if n >= 5:                 # a ratio over two rooms is noise
            assert furnished[rtype] >= n * 0.7, (rtype, furnished[rtype], n)


def test_a_bare_special_room_gets_a_loose_piece_of_its_own():
    """A small graveyard whose every wall tile stands beside a way in has no
    spot for a headstone (they keep clear of the ways in): it still shows a
    bone pile on its own floor, which blocks nothing."""
    from dungeon import DOOR, GRAVE
    w, h = 9, 9
    tiles = [[WALL] * w for _ in range(h)]
    room = Room(2, 2, 5, 5)                  # inner 3x3, at (3..5, 3..5)
    for y in range(3, 6):
        for x in range(3, 6):
            tiles[y][x] = FLOOR
    for x, y in ((4, 2), (4, 6), (2, 4), (6, 4)):
        tiles[y][x] = DOOR                   # a way in on every side
    tiles[3][3] = tiles[3][5] = GRAVE        # graves along the north wall: no head to stand at
    d = Dungeon(tiles, [room], w, h, 30)
    d.special_rooms = {tuple(room.center): 'graveyard'}
    taken = set()
    n = decor.furnish_special_rooms(d, taken, [], random.Random(1))
    fx = d.__dict__.get('fixtures') or {}
    assert n == 1 and set(fx.values()) == {'bone_pile'}
    (pos,) = fx
    assert d.tiles[pos[1]][pos[0]] == FLOOR and d.is_walkable(*pos)
    # A room with nowhere free is left as it is: nothing goes under the loot.
    d2 = Dungeon([row[:] for row in tiles], [room], w, h, 30)
    d2.special_rooms = {tuple(room.center): 'graveyard'}
    full = {(x, y) for y in range(3, 6) for x in range(3, 6)}
    assert decor.furnish_special_rooms(d2, set(full), [], random.Random(1)) == 0
    assert not (d2.__dict__.get('fixtures') or {})


def _plain_floor():
    w, h = 16, 10
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, 9):
        for x in range(1, 15):
            tiles[y][x] = FLOOR
    return Dungeon(tiles, [Room(0, 0, 16, 10)], w, h, 30)


def test_themed_spawns_prefer_the_theme():
    d = _plain_floor()
    got = spawn_themed(d.rooms[0], 30, d, words=['skeleton'], families=['restless_dead'],
                       count=(4, 4), rng=random.Random(2))
    assert got and all(m.family == 'restless_dead' for m in got)
    hive = spawn_themed(d.rooms[0], 9, d, words=decor.room_dressing()['beehive_keepers']['words'],
                        families=['vermin'], count=(3, 3), rng=random.Random(3))
    assert hive and all(m.family == 'vermin' for m in hive)


class _Hero:
    def __init__(self):
        self.x, self.y = 5, 5
        self.hp, self.max_hp = 20, 60
        self.sp, self.max_sp = 10, 200
        self.gold = 100
        self.status_effects = {}
        self.WIS = 10

    def has_effect(self, n):
        return self.status_effects.get(n, 0) not in (0, None)


class _G:
    def __init__(self, d):
        import game_lore_fixtures
        self.__class__ = type('G', (game_lore_fixtures.LoreFixturesMixin, _G), {})
        self.dungeon = d
        self.player = _Hero()
        self.dungeon_level = 30
        self.monsters = []
        self.ground_items = []
        self.msgs = []
        self.gold_in = 0
        self.noise = []

    def add_message(self, t, k='info'):
        self.msgs.append(t)

    def _gain_gold(self, n, **k):
        self.gold_in += n

    def _make_noise(self, kind, x=None, y=None):
        self.noise.append(kind)

    def _display_name(self, it):
        return getattr(it, 'name', 'it')

    def _chron(self, *a, **k):
        pass

    def _refresh_fov(self):
        pass


def test_a_right_answer_gives_once_and_a_wrong_one_spends_it():
    d = _plain_floor()
    decor.place(d, (6, 5), 'field_kitchen')
    d.lore_fixtures = {(6, 5): {'tier': 2}}
    g = _G(d)
    defs = decor.lore_fixtures()['fixtures']
    assert decor.lore_fixture_near(d, 5, 5) == ((6, 5), 'field_kitchen')
    g._lore_fixture_resolve((6, 5), 'field_kitchen', defs['field_kitchen'], True)
    assert g.player.sp > 10
    assert d.fixture_state[(6, 5)] == 'spent'
    assert decor.lore_fixture_near(d, 5, 5) is None, 'once only'
    decor.place(d, (4, 5), 'brazen_head')
    d.lore_fixtures[(4, 5)] = {'tier': 2}
    g._lore_fixture_resolve((4, 5), 'brazen_head', defs['brazen_head'], False)
    assert d.fixture_state[(4, 5)] == 'spent'
    assert 'alarm' in g.noise, 'the head laughs loud enough to wake the floor'


def test_the_ledger_pays_coin_and_the_shrine_mends():
    d = _plain_floor()
    g = _G(d)
    defs = decor.lore_fixtures()['fixtures']
    g._lore_fixture_resolve((3, 3), 'ledger_desk', defs['ledger_desk'], True)
    assert g.gold_in > 0
    g.player.status_effects['poisoned'] = 5
    g._lore_fixture_resolve((3, 4), 'wayside_icon', defs['wayside_icon'], True)
    assert not g.player.has_effect('poisoned')


def test_the_surveyors_table_maps_the_floor():
    d = _plain_floor()
    g = _G(d)
    g._lore_fixture_resolve((3, 3), 'surveyor_table', decor.lore_fixtures()['fixtures']['surveyor_table'], True)
    assert len(d.explored) == d.width * d.height


def test_the_special_room_lines_no_longer_live_in_the_dead_place():
    src = open(os.path.join(ROOT, 'src', 'dungeon.py'), encoding='utf-8').read()
    body = src[src.index('def _build_atmosphere'):src.index('# BSP helpers')]
    assert 'exotic roars' not in body
