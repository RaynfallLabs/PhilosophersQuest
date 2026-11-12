"""Dungeon Alive slice 2: the five domains and the fixture layer
(src/decor.py, data/domains.json, data/fixtures.json).

Fixtures are scenery that can stand in the way: they must never cut a floor
in two, never sit on a stair or a feature, never hide an item or a creature,
and a floor without them (an old save) must work as before.
"""
import collections
import json
import os
import pickle
import random
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import decor  # noqa: E402
from dungeon import (FLOOR, STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR,  # noqa: E402
                     Dungeon, Room, WALL)


def _no_bones(monkeypatch):
    import bones
    monkeypatch.setattr(bones, 'load_bones', lambda *a, **k: None)


def test_domains_cover_every_floor_once():
    seen = collections.Counter()
    for d in decor.domains():
        lo, hi = d['floors']
        for f in range(lo, hi + 1):
            seen[f] += 1
    assert all(seen[f] == 1 for f in range(1, 101))
    assert decor.domain_for(999) is None
    assert decor.domain_for(20)['id'] == 'labyrinth'
    assert decor.domain_for(21)['id'] == 'temple'
    assert decor.domain_for(100)['id'] == 'abyss'


def test_domains_name_real_bosses_and_fixtures():
    mons = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    fx = decor.fixture_defs()
    for d in decor.domains():
        assert d['boss'] in mons, d['id']
        assert d['arrival'].strip()
        for layer, spec in (d.get('decor') or {}).items():
            for fid in spec['ids']:
                assert fid in fx, (d['id'], fid)
                assert fx[fid].get('layer') == layer, (d['id'], fid, layer)


def test_every_fixture_says_what_it_is():
    for fid, f in decor.fixture_defs().items():
        assert f.get('layer') in ('floor', 'stand', 'wall'), fid
        assert f.get('look', '').strip(), fid
        assert f.get('name', '').strip(), fid
        if f.get('opaque'):
            assert f.get('blocks'), f'{fid}: what blocks sight must block feet'
        if f.get('blocks'):
            assert f['layer'] == 'stand', fid
            assert len(f.get('color', [])) == 3, f'{fid}: blocking needs a fallback colour'


def _bare():
    w, h = 12, 8
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, 7):
        for x in range(1, 11):
            tiles[y][x] = FLOOR
    return Dungeon(tiles, [Room(0, 0, 12, 8)], w, h, 25)


def test_a_statue_blocks_feet_and_eyes_but_the_tile_stays_floor():
    d = _bare()
    assert d.is_walkable(5, 4) and not d.is_opaque(5, 4)
    decor.place(d, (5, 4), 'statue_kneel')
    assert not d.is_walkable(5, 4)
    assert d.is_opaque(5, 4)
    assert d.tiles[4][5] == FLOOR
    decor.place(d, (6, 4), 'column_drum')
    assert not d.is_walkable(6, 4) and not d.is_opaque(6, 4)
    decor.place(d, (7, 4), 'roots')
    assert d.is_walkable(7, 4)
    decor.remove(d, (5, 4))
    assert d.is_walkable(5, 4) and not d.is_opaque(5, 4)
    assert decor.blocking_name(d, 6, 4) == 'a fallen column'
    assert 'marble' in decor.look_line(d, 6, 4)


def test_an_old_floor_without_fixtures_still_works():
    d = _bare()
    for k in ('fixture_blocks', 'fixture_opaque', 'fixtures', 'theme', 'domain'):
        d.__dict__.pop(k, None)
    assert d.is_walkable(3, 3) and not d.is_opaque(3, 3)
    assert decor.fixture_at(d, 3, 3) is None
    assert d.theme is None


def _walk(d):
    start = next((x, y) for y in range(d.height) for x in range(d.width)
                 if d.tiles[y][x] == STAIRS_UP)
    seen = {start}
    q = collections.deque([start])
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) in seen or not d.in_bounds(nx, ny):
                continue
            if d.is_walkable(nx, ny) or d.tiles[ny][nx] in (DOOR, SECRET_DOOR):
                seen.add((nx, ny))
                q.append((nx, ny))
    return seen


def test_generated_floors_are_dressed_and_never_cut(monkeypatch):
    _no_bones(monkeypatch)
    from level_manager import LevelManager
    random.seed(11)
    lm = LevelManager()
    totals = collections.Counter()
    for level in (2, 9, 23, 33, 47, 58, 66, 77, 84, 95):
        d, monsters, items = lm.generate(level)
        assert d.theme == decor.domain_for(level).get('theme')
        assert d.domain == decor.domain_for(level)['id']
        fx = d.__dict__.get('fixtures') or {}
        totals[d.domain] += len(fx)
        reach = _walk(d)
        stairs = [(x, y) for y in range(d.height) for x in range(d.width)
                  if d.tiles[y][x] == STAIRS_DOWN]
        assert all(s in reach for s in stairs), level
        held = {(m.x, m.y) for m in monsters if m.alive} | {(i.x, i.y) for i in items}
        for pos, fid in fx.items():
            defn = decor.fixture_def(fid)
            x, y = pos
            if defn['layer'] == 'wall':
                assert d.tiles[y][x] == WALL, (level, fid)
            else:
                assert d.tiles[y][x] == FLOOR, (level, fid, d.tiles[y][x])
            if defn.get('blocks'):
                assert pos not in held, (level, fid)
        # Nothing furnished walls anything off: lift the fixtures and the
        # walk from the up stair reaches exactly the furnished tiles more.
        blocks = set(d.fixture_blocks)
        d.fixture_blocks = set()
        bare = _walk(d)
        d.fixture_blocks = blocks
        assert bare - reach <= blocks, (level, sorted(bare - reach - blocks)[:5])
    for dom in ('labyrinth', 'temple', 'deep', 'rime', 'abyss'):
        assert totals[dom] > 0, dom


def test_boss_floors_wear_their_domain(monkeypatch):
    _no_bones(monkeypatch)
    from level_manager import LevelManager
    lm = LevelManager()
    for level, theme in ((20, None), (40, 'temple'), (60, 'deep'), (80, 'rime'), (100, 'abyss')):
        d, _m, _i = lm.generate(level)
        assert d.theme == theme, level


def test_fixtures_pickle_with_their_floor():
    d = _bare()
    decor.place(d, (3, 3), 'stalagmite')
    decor.place(d, (4, 4), 'ash_drift', state='spent')
    d2 = pickle.loads(pickle.dumps(d))
    assert not d2.is_walkable(3, 3) and d2.is_opaque(3, 3)
    assert decor.fixture_at(d2, 4, 4) == 'ash_drift'
    assert d2.fixture_state[(4, 4)] == 'spent'


def test_a_missing_theme_picture_falls_back_to_the_base_tile():
    import renderer
    d = _bare()
    d.theme = 'no_such_theme'
    name = renderer._tile_sprite_name(d, 1, 1, FLOOR)
    assert not name.startswith('themes/')
    d.tile_art = {(2, 2): 'hoard'}
    assert renderer._tile_sprite_name(d, 2, 2, FLOOR) == 'hoard'


def test_the_domains_are_announced_once(monkeypatch):
    class G:
        def __init__(self):
            self.msgs = []
            self.chron = []

        def add_message(self, t, k='info'):
            self.msgs.append(t)

        def _chron(self, kind, text, **kw):
            self.chron.append(text)
    import game_encounters
    g = G()
    game_encounters.EncountersMixin._announce_domain(g, 21)
    game_encounters.EncountersMixin._announce_domain(g, 22)
    game_encounters.EncountersMixin._announce_domain(g, 41)
    assert len(g.msgs) == 2
    assert 'Athena' in g.msgs[0]
    assert g.chron[0].endswith('The Forgotten Temple.')
