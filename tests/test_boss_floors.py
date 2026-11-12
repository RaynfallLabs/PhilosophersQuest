"""Dungeon Alive slice 6: the five finales (data/boss_floors.json,
decor.dress_boss_floor). Every gate floor wears its domain, its stair bar is
drawn, its pillars become what the lore says stands there, and the dressing
never changes a fight's mechanics: pillars stay WALL (gaze and breath cover,
Asterion's phasing walls) and the way to the stair stays open.
"""
import collections
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import decor  # noqa: E402
from dungeon import FLOOR, WALL, ICE, STAIRS_UP, STAIRS_DOWN, DOOR, SECRET_DOOR  # noqa: E402


def _gen(monkeypatch, level):
    import bones
    monkeypatch.setattr(bones, 'load_bones', lambda *a, **k: None)
    from level_manager import LevelManager
    return LevelManager().generate(level)


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
            if d.is_walkable(nx, ny) or d.tiles[ny][nx] in (DOOR, SECRET_DOOR, STAIRS_DOWN):
                seen.add((nx, ny))
                q.append((nx, ny))
    return seen


def test_boss_floor_data_names_real_fixtures():
    fx = decor.fixture_defs()
    data = decor.boss_floors()
    for guard, (shut, opened) in data['barriers'].items():
        assert shut in fx and opened in fx, guard
    for level, spec in data['floors'].items():
        for fid in (spec.get('pillars') or {}):
            assert fx[fid]['layer'] == 'stand', fid
        for layer in ('walls', 'stand', 'floor'):
            for part in spec.get(layer) or ():
                for fid in part['ids']:
                    assert fid in fx, (level, fid)
        for part in spec.get('lore') or ():
            assert part['id'] in decor.lore_fixtures()['fixtures'], (level, part)


def test_every_finale_is_dressed_barred_and_walkable(monkeypatch):
    for level, theme in ((20, None), (40, 'temple'), (60, 'deep'), (80, 'rime'), (100, 'abyss')):
        d, mons, items = _gen(monkeypatch, level)
        assert d.theme == theme
        fx = d.__dict__.get('fixtures') or {}
        assert len(fx) >= 15, (level, len(fx))
        stairs = [(x, y) for y in range(d.height) for x in range(d.width)
                  if d.tiles[y][x] == STAIRS_DOWN]
        if level != 100:
            bar = d.barrier
            assert bar['pos'] in stairs
            assert fx[bar['pos']] == decor.boss_floors()['barriers'][d.stairs_guardian][0]
        reach = _walk(d)
        assert all(s in reach for s in stairs), level


def test_pillars_become_statues_but_stay_walls(monkeypatch):
    d, mons, items = _gen(monkeypatch, 40)
    statues = [p for p, f in d.fixtures.items() if f.startswith('statue_') and f != 'statue_crowd'
               and f != 'statue_rubble']
    assert len(statues) >= 12, 'Medusa\'s pillars are people turned to stone'
    for (x, y) in statues:
        assert d.tiles[y][x] == WALL, 'still the cover from her gaze'
        assert d.tile_art[(x, y)] == 'floor'
        assert d.is_opaque(x, y) and not d.is_walkable(x, y)


def test_the_labyrinth_keeps_its_phasing_walls(monkeypatch):
    d, mons, items = _gen(monkeypatch, 20)
    for pos, fid in d.fixtures.items():
        if decor.fixture_def(fid).get('blocks'):
            assert pos not in d.phasing_walls or d.tiles[pos[1]][pos[0]] == WALL
    assert d.theme is None, 'Asterion keeps the base tiles'
    assert collections.Counter(d.fixtures.values())['bronze_grate'] == 1


def test_the_barrier_breaks_when_its_keeper_dies(monkeypatch):
    d, mons, items = _gen(monkeypatch, 60)
    pos = d.barrier['pos']
    decor.open_barrier(d)
    assert d.fixtures[pos] == 'fire_out'


def test_a_seal_demons_floor_has_its_wax_seal(monkeypatch):
    d, mons, items = _gen(monkeypatch, 83)
    if getattr(d, 'stairs_guardian', None):
        assert d.fixtures[d.barrier['pos']] == 'wax_seal'


def test_fenrirs_braziers_melt_the_ice(monkeypatch):
    d, mons, items = _gen(monkeypatch, 80)
    braziers = [p for p in d.lore_fixtures if d.fixtures.get(p) == 'brazier_cold']
    assert braziers
    import game_lore_fixtures

    class G(game_lore_fixtures.LoreFixturesMixin):
        def __init__(self):
            self.dungeon = d
            self.msgs = []

        def add_message(self, t, k='info'):
            self.msgs.append(t)
    pos = braziers[0]
    d.tiles[pos[1] + 1][pos[0]] = ICE if d.tiles[pos[1] + 1][pos[0]] == FLOOR else d.tiles[pos[1] + 1][pos[0]]
    G()._lore_reward_light_brazier(pos, 'brazier_cold')
    assert d.fixtures[pos] == 'brazier_lit'
    assert all(d.tiles[y][x] != ICE for y in range(pos[1] - 2, pos[1] + 3)
               for x in range(pos[0] - 2, pos[0] + 3) if d.in_bounds(x, y))


def test_the_pit_has_its_vents_stones_and_a_line(monkeypatch):
    d, mons, items = _gen(monkeypatch, 100)
    c = collections.Counter(d.fixtures.values())
    assert c['seal_stone'] == 7
    vents = [p for p in d.lore_fixtures if d.fixtures.get(p) == 'smoke_vent']
    assert 4 <= len(vents) <= 6
    assert any('seven' in m.lower() for m in d.atmosphere_messages)


def test_the_room_turns_with_its_keeper(monkeypatch):
    d, mons, items = _gen(monkeypatch, 20)
    ast = next(m for m in mons if m.kind == 'asterion_minotaur')
    before = sum(1 for f in d.fixtures.values() if f == 'rubble')
    decor.boss_phase(d, ast)
    assert sum(1 for f in d.fixtures.values() if f == 'rubble') > before
