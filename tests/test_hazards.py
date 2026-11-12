"""Dungeon Alive slice 3: each domain's hazards, trap lean, kin and clans
(src/hazards.py, src/game_hazards.py, data/hazards.json, data/domains.json).

Hazards are seen before they bite (Observe teaches them), catch monsters as
well as the hero, and the kin weights are lore only: no kind becomes
eligible that was not, and nothing scales with the floor number.
"""
import json
import os
import random
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import decor  # noqa: E402
import hazards  # noqa: E402
from dungeon import (FLOOR, WALL, STAIRS_UP, STAIRS_DOWN, TRAP_TYPES,  # noqa: E402
                     Dungeon, Room, _build_spawn_pool, _floor_pool)


def _no_bones(monkeypatch):
    import bones
    monkeypatch.setattr(bones, 'load_bones', lambda *a, **k: None)


def test_hazard_data_is_whole():
    fx = decor.fixture_defs()
    mons = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    fams = {m.get('family') for m in mons.values()}
    traps = {t['type'] for t in TRAP_TYPES}
    for fid, h in hazards.data()['hazards'].items():
        assert fid in fx, fid
        assert h['trigger'] in ('step', 'cycle'), fid
        assert h.get('hero'), fid
        if h.get('after'):
            assert h['after'] in fx, fid
        if h['trigger'] == 'cycle':
            assert fx.get(fid + '_active'), f'{fid}: needs its firing picture'
        # Observe must teach what it does, in more than a word.
        assert len(fx[fid]['look'].split()) >= 10, fid
    for d in decor.domains():
        for spec in d.get('hazards') or ():
            assert spec['id'] in hazards.data()['hazards'], (d['id'], spec)
        for fam in d.get('kin') or {}:
            assert fam in fams, (d['id'], fam)
        for t in d.get('traps') or {}:
            assert t in traps, (d['id'], t)
    for fam in decor.config()['clan_lines']:
        assert fam in fams, fam


def test_kin_changes_weights_never_eligibility():
    for level in (25, 50, 70, 90):
        base = {k for k in _build_spawn_pool(level)}

        class D:
            clan = 'demons'
        clanned = _floor_pool(level, D())
        assert set(clanned) == base
        plain = _build_spawn_pool(level)
        for k, v in clanned.items():
            if v.get('family') == 'demons':
                assert v['_spawn_freq'] == 3.0 * plain[k]['_spawn_freq']
        dom = decor.domain_for(level)
        pool = _build_spawn_pool(level)
        for k, v in pool.items():
            if v.get('family') in (dom.get('kin') or {}):
                # weighted up from the plain bell curve
                assert v['_spawn_freq'] > 0


def test_kin_is_by_domain_not_by_floor_number():
    # Two floors of one domain lean the same way.
    assert hazards.kin_weight(41, 'dragons') == hazards.kin_weight(59, 'dragons')
    assert hazards.kin_weight(19, 'dragons') == 1.0
    assert hazards.kin_weight(21, 'gorgons') > 1.0


def test_a_clan_is_a_family_with_enough_kinds():
    pool = _build_spawn_pool(66)
    got = set()
    for seed in range(60):
        fam = hazards.pick_clan(66, pool, random.Random(seed))
        if fam:
            got.add(fam)
            n = sum(1 for v in pool.values() if v.get('family') == fam)
            assert n >= 4, fam
            assert hazards.clan_line(fam)
    assert got


def test_step_hazards_and_levitation():
    rng = random.Random(0)
    ice = hazards.hazard_def('thin_ice')
    assert not any(hazards.step_fires(ice, heavy=False, levitating=True, rng=rng) for _ in range(50))
    light = sum(hazards.step_fires(ice, heavy=False, levitating=False, rng=rng) for _ in range(2000))
    heavy = sum(hazards.step_fires(ice, heavy=True, levitating=False, rng=rng) for _ in range(2000))
    assert heavy > light * 1.8, 'a heavy pack goes through'
    icicle = hazards.hazard_def('icicle_shadow')
    assert any(hazards.step_fires(icicle, heavy=False, levitating=True, rng=rng) for _ in range(50)), \
        'an icicle falls on the levitating too'


def _room_floor():
    w, h = 14, 10
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, 9):
        for x in range(1, 13):
            tiles[y][x] = FLOOR
    tiles[1][1] = STAIRS_UP
    tiles[8][12] = STAIRS_DOWN
    return Dungeon(tiles, [Room(0, 0, 14, 10)], w, h, 45)


def test_a_vent_glows_the_turn_before_it_breathes():
    d = _room_floor()
    decor.place(d, (5, 5), 'fire_vent')
    d.hazard_phase = {(5, 5): 2}
    phases = [hazards.cycle_phase(d, (5, 5), t) for t in range(12)]
    assert phases[1] == 'warn' and phases[2] == 'fire'
    assert phases[7] == 'warn' and phases[8] == 'fire'
    assert phases.count('fire') == 2


class _Hero:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.hp = self.max_hp = 60
        self.mp = 20
        self.status_effects = {}
        self.STR = self.CON = self.DEX = self.INT = self.WIS = self.PER = 10

    def has_effect(self, n):
        return self.status_effects.get(n, 0) not in (0, None)

    def add_effect(self, n, t):
        self.status_effects[n] = t

    def take_damage(self, a, t='physical'):
        self.hp -= a
        return a

    def is_dead(self):
        return self.hp <= 0

    def is_burdened(self):
        return False


class _Game:
    def __init__(self, d, hero):
        import game_hazards
        self.__class__ = type('G', (game_hazards.HazardsMixin, _Game), {})
        self.dungeon = d
        self.player = hero
        self.monsters = []
        self.msgs = []
        self.state = 'player'
        self.visible = {(x, y) for x in range(d.width) for y in range(d.height)}
        self.turn_count = 0
        self.killed = []

    def add_message(self, t, k='info'):
        self.msgs.append(t)

    def _make_noise(self, *a, **k):
        pass

    def _sees_monster(self, m):
        return True

    def _on_monster_killed(self, m, **k):
        self.killed.append(m)

    def _on_game_over(self):
        pass


def test_crumbling_floor_drops_the_hero_into_a_pit_and_is_spent(monkeypatch):
    d = _room_floor()
    decor.place(d, (4, 4), 'crumbling_floor')
    hero = _Hero(4, 4)
    g = _Game(d, hero)
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    g._hazard_step_hero(4, 4)
    assert hero.has_effect('in_pit')
    assert hero.hp < 60
    assert (4, 4) in d.pits
    assert decor.fixture_at(d, 4, 4) == 'rubble'
    assert any('give way' in m for m in g.msgs)


def test_a_vent_burns_the_monster_standing_on_it():
    import json as _j
    from monster import Monster
    d = _room_floor()
    decor.place(d, (6, 6), 'fire_vent')
    d.hazard_phase = {(6, 6): 0}
    mons = _j.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    m = Monster({**mons['goblin'], 'id': 'goblin'}, 6, 6)
    hp0 = m.hp
    g = _Game(d, _Hero(2, 2))
    g.monsters = [m]
    g.turn_count = 6
    g._hazards_tick()
    assert m.hp < hp0 or not m.alive
    assert m.has_effect('burning') or not m.alive


def test_generated_domain_floors_carry_their_hazards(monkeypatch):
    _no_bones(monkeypatch)
    from level_manager import LevelManager
    lm = LevelManager()
    want = {'temple': {'crumbling_floor', 'strangler_vine'}, 'deep': {'fire_vent'},
            'rime': {'thin_ice', 'icicle_shadow'}, 'abyss': {'brimstone', 'soul_sigil'}}
    seen = {k: set() for k in want}
    for level in (23, 27, 33, 44, 48, 55, 63, 67, 74, 83, 88, 94):
        d, _m, _i = lm.generate(level)
        first = d.rooms[0]
        stairs = [(x, y) for y in range(d.height) for x in range(d.width)
                  if d.tiles[y][x] in (STAIRS_UP, STAIRS_DOWN)]
        for pos, fid in (d.__dict__.get('fixtures') or {}).items():
            if not hazards.hazard_def(fid):
                continue
            seen[d.domain].add(fid)
            assert not (first.x <= pos[0] < first.x + first.width
                        and first.y <= pos[1] < first.y + first.height), (level, fid)
            assert all(max(abs(pos[0] - s[0]), abs(pos[1] - s[1])) > 1 for s in stairs), (level, fid)
    for dom, ids in want.items():
        assert seen[dom] & ids, dom


def test_the_labyrinth_keeps_todays_traps():
    rng = random.Random(1)
    kinds = {hazards.pick_trap(5, TRAP_TYPES, rng)['type'] for _ in range(400)}
    assert kinds == {t['type'] for t in TRAP_TYPES}
    deep = [hazards.pick_trap(50, TRAP_TYPES, rng)['type'] for _ in range(2000)]
    assert deep.count('fire') > deep.count('alarm') * 2
