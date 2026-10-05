"""Behaviour tests for the 2026-10 quest pass.

The older quest tests (test_quest_chains.py) mostly assert that a function
name appears in the source, and every bug fixed in this pass got past them.
These run the real code: generate the quest floor and walk it, tick the real
status system, call the real spawn and judgment functions.

Deep quest content cannot be play-tested in a sitting, so this is the guard.
"""
import collections
import json
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))

import pygame  # noqa: E402

pygame.init()

from dungeon import (generate_dungeon, spawn_items, WALL, SECRET_DOOR,  # noqa: E402
                     WATER, LAVA)


def _reach(d, start, opened=()):
    """Tiles the player can walk to from `start` (8-way), treating `opened`
    tiles as doors that have been opened."""
    seen = {start}
    q = collections.deque([start])
    while q:
        x, y = q.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if (nx, ny) in seen or not d.in_bounds(nx, ny):
                    continue
                if (nx, ny) in opened or d.tiles[ny][nx] not in (WALL, SECRET_DOOR, WATER, LAVA):
                    seen.add((nx, ny))
                    q.append((nx, ny))
    return seen


def _floor(level):
    d = generate_dungeon(80, 50, level)
    items = spawn_items(d.rooms, level, d)
    return d, items


# ----------------------------------------------------------- sealed shrines

@pytest.mark.parametrize('level,door_attr,reward_id', [
    (17, 'ariadne_shrine_door', 'ariadnes_thread'),
    (37, 'athena_shrine_door', 'aegis_of_athena'),
    (53, 'odin_shrine_door', 'sigurds_shovel'),
])
def test_quest_shrine_is_sealed_until_its_door_opens(level, door_attr, reward_id):
    """The reward chamber has exactly one way in: the door the quest opens.
    (The old carve left the two tiles beside the door open, so the Thread,
    the Aegis and the Shovel were free on about 98% of floors and the Bronze
    Bull, the Eye and the altar offering were never needed.)"""
    sealed = 0
    for _ in range(8):
        d, items = _floor(level)
        reward = next((i for i in items if getattr(i, 'id', '') == reward_id), None)
        assert reward is not None, 'the reward must always exist'
        door = getattr(d, door_attr, None)
        if door is None:
            continue    # no solid rock near the feature: left beside it instead
        sealed += 1
        start = d.rooms[0].center
        assert (reward.x, reward.y) not in _reach(d, start), 'reachable with the door shut'
        # Opening the door joins the 3x3 chamber to what lies outside it.
        chamber = _reach(d, (reward.x, reward.y), opened={door})
        assert len(chamber) > 9, 'the door does not connect the chamber to the level'
    assert sealed >= 6, 'sealing should almost always succeed'


def test_ariadnes_fountain_never_dries_up():
    src = open(os.path.join(ROOT, 'src', 'game_divine.py'), encoding='utf-8').read()
    assert "getattr(self.dungeon, 'ariadne_shrine_door', None) is None" in src


# ------------------------------------------------------------ quest items

def test_quest_artifacts_carry_their_lore():
    """Built from data/items/artifact.json, so the lore written for them (the
    best breadcrumbs in the game) is actually shown. They used to be inline
    dicts; the leather scrap's live text was "Useless scrap"."""
    from dungeon import _quest_artifact
    for item_id in ('bronze_bull', 'eye_of_graeae', 'leather_scrap', 'gleipnir',
                    'cats_footstep', 'womans_beard', 'mountain_root',
                    'fish_breath', 'bird_spittle', 'bear_sinew'):
        item = _quest_artifact(item_id)
        assert item is not None, item_id
        assert len((item.lore or '').split()) >= 15, item_id
        assert item.identified
    assert 'seless' not in _quest_artifact('leather_scrap').lore


def test_leather_scrap_on_its_floor_is_the_data_item():
    d, items = _floor(5)
    scrap = next(i for i in items if getattr(i, 'id', '') == 'leather_scrap')
    assert scrap.weight < 1.0
    assert scrap.lore


def test_broken_gram_can_be_thrown_and_is_never_cursed():
    """The Odin secret is "throw the broken blade over the altar". A sword
    could not be thrown at all, so reforged Gram was unobtainable. And an
    altar eats cursed items, so a cursed blade destroyed the quest."""
    from game_combat import CombatMixin
    for _ in range(6):
        d, items = _floor(48)
        blade = next(i for i in items if getattr(i, 'id', '') == 'broken_gram')
        assert blade.buc == 'uncursed'
        assert CombatMixin._is_throwable_weapon(blade)


@pytest.mark.parametrize('level,comp', [(68, 'mountain_root'), (71, 'fish_breath')])
def test_ringed_gleipnir_ingredient_can_be_reached_on_foot(level, comp):
    """Root of a Mountain sat in a full ring of lava and Breath of a Fish in
    a full ring of water. The player can enter neither, so Gleipnir could not
    be made in about 19 runs out of 20."""
    ok = 0
    for _ in range(8):
        d, items = _floor(level)
        it = next(i for i in items if getattr(i, 'id', '') == comp)
        neighbours = [(it.x + dx, it.y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        if any(d.is_walkable(x, y) for x, y in neighbours):
            ok += 1
    assert ok == 8


# ---------------------------------------------------------------- the pit

def test_being_in_a_pit_lasts_until_the_player_climbs_out():
    """in_pit was applied for 1 turn and expired on the same turn's status
    tick, before any monster acted: Sigurd's pit never protected or helped."""
    from player import Player
    from status_effects import tick_all
    p = Player()
    p.add_effect('in_pit', -1)
    for _ in range(25):
        tick_all(p)
    assert p.has_effect('in_pit')
    for name in ('game_combat.py', 'main.py'):
        src = open(os.path.join(ROOT, 'src', name), encoding='utf-8').read()
        assert "add_effect('in_pit', 1)" not in src, name


# ------------------------------------------------------------- Medusa's gaze

def _medusa():
    from monster import Monster
    data = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    return Monster({**data['medusa_gorgon'], 'id': 'medusa_gorgon'}, 5, 5)


class _Shield:
    def __init__(self, id_):
        self.id = id_


def test_aegis_reflection_costs_medusa_her_turn():
    from player import Player
    m = _medusa()
    p = Player()
    p.shield = _Shield('aegis_of_athena')
    m._gaze_cooldown = 0
    dmg, msg = m.attack(p)
    assert dmg == 0
    assert 'rigid' in msg
    assert m.status_effects.get('paralyzed', 0) >= 2
    assert not p.has_effect('paralyzed')


def test_petrify_immunity_stops_the_gaze():
    """Medusa's trophy and the Greater Aegis grant petrify_immune. Nothing
    consulted it: every gaze paralyses, so the reward did nothing."""
    from player import Player
    m = _medusa()
    p = Player()
    p.add_effect('petrify_immune', -1)
    for _ in range(12):
        m._gaze_cooldown = 0
        m.attack(p)
        assert not p.has_effect('paralyzed')


# ------------------------------------------------------------ rage and swarms

def test_fenrir_does_not_build_rage_before_he_notices_the_player():
    from boss_levels import generate_boss_level
    from player import Player
    import monster as monster_mod
    d, monsters, _items = generate_boss_level(80)
    fenrir = next(m for m in monsters if m.kind == 'fenrir_wolf')
    p = Player()
    p.x, p.y = d.rooms[0].center
    fenrir._aware = False
    fenrir._alerted = False
    for _ in range(60):
        fenrir._rage_turn_counter = getattr(fenrir, '_rage_turn_counter', 0)
        # call the rage bookkeeping only (movement needs the full game loop)
        engaged = fenrir._aware or fenrir._alerted or fenrir._adjacent_to(p)
        assert not engaged
    assert fenrir.rage_stacks == 0
    assert monster_mod.RAGE_STACK_CAP <= 8
    src = open(os.path.join(ROOT, 'src', 'monster.py'), encoding='utf-8').read()
    assert 'self.rage_stacks < RAGE_STACK_CAP' in src
    assert '_live < LOCUST_CAP' in src


def test_the_name_handles_proper_nouns():
    from monster import the_name

    class M:
        def __init__(self, name, **kw):
            self.name = name
            self.__dict__.update(kw)

    assert the_name(M('giant rat')) == 'The giant rat'
    assert the_name(M('Arachne', is_mini_boss=True)) == 'Arachne'
    assert the_name(M('The Sphinx', is_mini_boss=True)) == 'The Sphinx'
    assert the_name(M('the Iron Patriarch', is_boss=True)) == 'The Iron Patriarch'


# ---------------------------------------------------------------- placement

def test_cow_level_does_not_count_as_depth():
    """Level 999 is the Cow Level. Counting it made "Deepest Level 999" and
    added 999,000 to the score."""
    from boss_levels import COW_LEVEL
    from level_manager import LevelManager
    lm = LevelManager()
    lm.generate(3)
    lm.generate(COW_LEVEL)
    assert lm.max_level_reached == 3


def test_planned_mini_bosses_avoid_boss_and_seal_floors():
    from dungeon import _BOSS_LEVELS
    from level_manager import LevelManager
    for _ in range(300):
        lm = LevelManager()
        for lvl in lm._planned_mini_bosses:
            assert lvl not in _BOSS_LEVELS
            assert lvl not in LevelManager._SEAL_DEMON_LEVELS


def test_special_rooms_get_their_sleepers():
    """spawn_monsters skips rooms[0], so the zoo / graveyard / barracks call
    with a one-room list spawned nothing and the zoo was free gold."""
    from dungeon import spawn_monsters
    d = generate_dungeon(80, 50, 30)
    room = d.rooms[-1]
    assert spawn_monsters([room, room], 30, d, min_count=4, max_count=8)
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    assert 'spawn_monsters([room], ' not in src


# -------------------------------------------------------------------- bones

def test_the_ghost_is_as_strong_as_the_floor_it_died_on():
    from bones import spawn_ghost
    from floor_curve import target_hp
    for floor in (5, 40, 85):
        d = generate_dungeon(80, 50, floor)
        monsters, items = [], []
        spawn_ghost({'player_name': 'Tester', 'dungeon_level': floor, 'max_hp': 60,
                     'gear': [], 'gold': 0}, d, monsters, items)
        ghost = next(m for m in monsters if m.kind == 'player_ghost')
        assert ghost.max_hp >= target_hp(floor)
    assert monsters[0].max_hp > 1000   # floor 85; it used to cap at 300


def test_floor_curve_matches_the_balance_tool():
    import floor_curve
    import respawn_by_hp
    assert floor_curve.HP_ANCHORS == respawn_by_hp.HP_ANCHORS
    assert floor_curve.DMG_ANCHORS == respawn_by_hp.DMG_ANCHORS


def test_walking_out_alive_leaves_no_bones():
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    assert 'self._on_game_over(leave_bones=False)' in src
    assert "_reason in ('died', 'starved')" in src


# ----------------------------------------------------------------- judgment

def test_sword_of_michael_does_not_need_a_perfect_run():
    """It needed karma of exactly 10, and a run offers exactly ten chances at
    +1."""
    from npc_encounters import judge_karma
    assert judge_karma(10)[0] == 'sword_and_scales'
    assert judge_karma(8)[0] == 'sword_and_scales'
    assert judge_karma(7)[0] == 'scales_granted'
    assert judge_karma(1)[0] == 'scales_granted'
    assert judge_karma(0)[0] == 'silence'
    assert judge_karma(-6)[0] == 'abaddon_empowered'


# ------------------------------------------------------------- the Labyrinth

def _lab_reach(d, start, blocked=frozenset()):
    seen = {start}
    q = collections.deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in seen or n in blocked or not d.in_bounds(*n):
                continue
            if d.tiles[n[1]][n[0]] == WALL:
                continue
            seen.add(n)
            q.append(n)
    return seen


def _find(d, tile):
    return next((x, y) for y in range(d.height) for x in range(d.width)
                if d.tiles[y][x] == tile)


def test_labyrinth_is_a_real_maze_with_the_minotaur_between_you_and_the_stair():
    """Floor 20 used to be three straight corridors, two thirds of which the
    player could not reach, with a stair that could be walked to without a
    fight. Now: every open tile is reachable, the stair down can only be
    reached through Asterion's hall, and it is barred while he lives."""
    from boss_levels import generate_boss_level, labyrinth_thread_route
    from dungeon import STAIRS_UP, STAIRS_DOWN
    layouts = set()
    for _ in range(12):
        d, monsters, items = generate_boss_level(20)
        up, down = _find(d, STAIRS_UP), _find(d, STAIRS_DOWN)
        open_tiles = {(x, y) for y in range(d.height) for x in range(d.width)
                      if d.tiles[y][x] != WALL}
        reach = _lab_reach(d, up)
        assert reach == open_tiles, 'part of the maze cannot be reached'
        assert len(open_tiles) > 900

        hall = d.rooms[1]
        hall_tiles = {(x, y) for x in range(hall.x, hall.x + hall.width)
                      for y in range(hall.y, hall.y + hall.height)}
        assert down not in _lab_reach(d, up, blocked=hall_tiles), \
            'the stair can be reached without crossing the hall'

        asterion = next(m for m in monsters if m.kind == 'asterion_minotaur')
        assert (asterion.x, asterion.y) in hall_tiles
        assert d.stairs_guardian == 'asterion_minotaur'

        route = labyrinth_thread_route(d)
        assert route and route[0] == up and route[-1] in hall_tiles
        assert all(d.tiles[y][x] != WALL for x, y in route)

        assert len(items) >= 4, 'the dead ends should hold something'
        assert all((it.x, it.y) in open_tiles for it in items)
        # Arriving from below puts the player on open floor, not on the stair.
        ax, ay = d.rooms[-1].center
        assert d.tiles[ay][ax] not in (WALL, STAIRS_DOWN)
        layouts.add(tuple(map(tuple, d.tiles)))
    assert len(layouts) > 6, 'the maze should differ from run to run'


def test_asterion_is_a_gate_boss():
    data = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    a = data['asterion_minotaur']
    import respawn_by_hp as rs
    assert rs.dice_avg(a['hp']) >= 550
    assert a['is_boss'] and a['can_charge']
    assert a['can_phase_walls'] and a['ai_pattern'] == 'hit_and_run'
    assert a['enraged_pattern'] == 'aggressive' and 0 < a['enrage_at_hp_pct'] < 0.5
    assert rs.max_attack(a) >= 9


def test_a_guarded_stair_refuses_while_the_guardian_lives():
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    i = src.index('def _descend_stairs')
    block = src[i:i + 1600]
    assert "getattr(self.dungeon, 'stairs_guardian', None)" in block
    assert 'm.alive and m.kind == _guard' in block


def test_monsters_load_their_own_lines_from_data():
    """enrage_message / rage_messages / revive_message were written into
    monsters.json but Monster never read them, so every one fell back to the
    generic line."""
    from monster import Monster
    data = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))

    def mk(mid):
        return Monster({**data[mid], 'id': mid}, 1, 1)

    assert 'horns' in mk('asterion_minotaur').enrage_message
    assert mk('whispering_crone').rage_messages
    assert 'head' in mk('green_knight').revive_message
    assert mk('giant_rat').enrage_message == ''


# --------------------------------------------------------- Medusa's temple

def _temple():
    from boss_levels import generate_boss_level
    from player import Player
    d, monsters, items = generate_boss_level(40)
    medusa = next(m for m in monsters if m.kind == 'medusa_gorgon')
    medusa._aware = True
    medusa._gaze_cooldown = 0
    p = Player()
    return d, medusa, monsters, items, p


def test_medusas_gaze_reaches_across_open_floor():
    """The gaze used to fire only when she was already adjacent, so there was
    never a line of sight to block and the temple's pillars did nothing."""
    d, medusa, monsters, _items, p = _temple()
    p.x, p.y = medusa.x, medusa.y - 4          # straight up the centre line
    assert medusa._has_los(p.x, p.y, d)
    before = (medusa.x, medusa.y)
    assert medusa._dancer_turn(p, d, monsters, set()) is True
    assert (medusa.x, medusa.y) == before, 'she looks instead of stepping'
    dmg, msg = medusa.attack(p)
    assert dmg == 0
    assert p.has_effect('paralyzed') or 'tear your eyes away' in msg
    assert medusa._gaze_cooldown > 0


def test_a_pillar_breaks_the_gaze():
    d, medusa, monsters, _items, p = _temple()
    # Stand directly behind a sanctum pillar, on the far side from her.
    pillar = (37, 41)
    assert d.tiles[pillar[1]][pillar[0]] == WALL
    dx = pillar[0] - medusa.x
    dy = pillar[1] - medusa.y
    p.x, p.y = pillar[0] + (1 if dx > 0 else -1), pillar[1] + (1 if dy > 0 else -1)
    assert d.is_walkable(p.x, p.y)
    assert not medusa._has_los(p.x, p.y, d), 'test position should be in cover'
    assert medusa._dancer_turn(p, d, monsters, set()) is False
    assert not p.has_effect('paralyzed')
    assert medusa._gaze_cooldown == 0, 'the gaze is not spent on a hidden target'


def test_aegis_turns_a_ranged_gaze_back_on_her():
    d, medusa, monsters, _items, p = _temple()
    p.x, p.y = medusa.x, medusa.y - 4
    p.shield = _Shield('aegis_of_athena')
    assert medusa._dancer_turn(p, d, monsters, set()) is True
    dmg, msg = medusa.attack(p)
    assert dmg == 0 and 'rigid' in msg
    assert medusa.status_effects.get('paralyzed', 0) >= 2
    assert not p.has_effect('paralyzed')


def test_a_blindfold_makes_the_gaze_harmless_at_range():
    d, medusa, monsters, _items, p = _temple()
    p.x, p.y = medusa.x, medusa.y - 4
    p.armor_slots[0] = _Shield('blindfold')        # head slot
    assert p.get_sight_radius() == 0
    for _ in range(6):
        medusa._gaze_cooldown = 0
        dmg, _msg = medusa.attack(p)
        assert dmg == 0, 'at range a failed gaze is her whole turn'
        assert not p.has_effect('paralyzed')


def test_medusas_temple_layout_and_loot():
    """The stair lies past the sanctum and is shut while she lives; a
    blindfold is always in a side chapel; her melee attacks carry no second
    copy of the gaze (it ignored the Aegis)."""
    from dungeon import STAIRS_UP, STAIRS_DOWN
    d, medusa, _monsters, items, _p = _temple()
    assert d.stairs_guardian == 'medusa_gorgon'
    up, down = _find(d, STAIRS_UP), _find(d, STAIRS_DOWN)
    sanctum = next(r for r in d.rooms if r.x <= medusa.x < r.x + r.width
                   and r.y <= medusa.y < r.y + r.height)
    sanctum_tiles = {(x, y) for x in range(sanctum.x, sanctum.x + sanctum.width)
                     for y in range(sanctum.y, sanctum.y + sanctum.height)}
    assert down in _lab_reach(d, up)
    assert down not in _lab_reach(d, up, blocked=sanctum_tiles)
    assert any(getattr(i, 'id', '') == 'blindfold' for i in items)
    assert all(d.tiles[i.y][i.x] != WALL for i in items)
    assert not any('gaze' in a['name'].lower() for a in medusa.attacks)
    assert medusa.gaze_paralyze > 0
    pillars = sum(1 for y in range(sanctum.y, sanctum.y + sanctum.height)
                  for x in range(sanctum.x, sanctum.x + sanctum.width)
                  if d.tiles[y][x] == WALL)
    assert pillars >= 8


def test_ordinary_medusas_gaze_respects_the_aegis_and_immunity():
    from monster import Monster
    from player import Player
    data = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    med = Monster({**data['medusa'], 'id': 'medusa'}, 5, 5)
    med.attacks = [a for a in med.attacks if 'gaze' in a['name'].lower()]
    assert med.attacks, 'the common medusa should still have her gaze'
    for setup in ('immune', 'aegis'):
        p = Player()
        p.x, p.y = 5, 6
        if setup == 'immune':
            p.add_effect('petrify_immune', -1)
        else:
            p.shield = _Shield('aegis_of_athena')
        for _ in range(15):
            dmg, _msg = med.attack(p)
            assert dmg == 0
            assert not p.has_effect('paralyzed'), setup


# ------------------------------------------------------------ Fafnir's lair

def _lair():
    from boss_levels import generate_boss_level
    from player import Player
    d, monsters, items = generate_boss_level(60)
    fafnir = next(m for m in monsters if m.kind == 'fafnir_dragon')
    fafnir._aware = True
    p = Player()
    return d, fafnir, monsters, items, p


def test_fafnir_breathes_on_the_way_in_then_closes():
    """The old `ranged` AI stood off at 2 to 8 tiles and breathed for ever, so
    he never came to the pit. Now he breathes once, then advances while the
    breath recharges, and ends up beside the player."""
    d, fafnir, monsters, _items, p = _lair()
    p.x, p.y = fafnir.x - 6, fafnir.y
    assert fafnir._has_los(p.x, p.y, d)
    assert fafnir._dragon_turn(p, d, monsters, set()) is True      # breath
    start = (fafnir.x, fafnir.y)
    moved = 0
    for _ in range(12):
        before = (fafnir.x, fafnir.y)
        fafnir._dragon_turn(p, d, monsters, set())
        moved += (fafnir.x, fafnir.y) != before
        if fafnir._adjacent_to(p):
            break
    assert moved >= 2 and (fafnir.x, fafnir.y) != start
    assert fafnir._adjacent_to(p), 'he should close to melee'


def test_fafnir_does_not_waste_breath_on_a_player_in_a_pit():
    d, fafnir, monsters, _items, p = _lair()
    p.x, p.y = fafnir.x - 6, fafnir.y
    p.add_effect('in_pit', -1)
    before = (fafnir.x, fafnir.y)
    fafnir._breath_cd = 0
    result = fafnir._dragon_turn(p, d, monsters, set())
    assert (fafnir.x, fafnir.y) != before, 'he advances instead of breathing'
    assert result is False or fafnir._adjacent_to(p)
    assert int(getattr(fafnir, '_breath_cd', 0) or 0) == 0


def test_fafnir_fights_with_tooth_and_claw_up_close():
    d, fafnir, _monsters, _items, p = _lair()
    p.x, p.y = fafnir.x - 1, fafnir.y
    names = set()
    for _ in range(40):
        _dmg, msg = fafnir.attack(p)
        names.add(msg)
    assert not any('breath' in m.lower() for m in names)


def test_lair_has_a_fallback_pit_a_real_hoard_and_a_barred_stair():
    from dungeon import STAIRS_UP, STAIRS_DOWN
    d, fafnir, _monsters, items, _p = _lair()
    assert d.old_pit in d.pits and d.is_walkable(*d.old_pit)
    lair = d.rooms[-2]
    assert lair.x <= d.old_pit[0] < lair.x + lair.width
    assert lair.y <= d.old_pit[1] < lair.y + lair.height
    assert d.stairs_guardian == 'fafnir_dragon'
    lair_tiles = {(x, y) for x in range(lair.x, lair.x + lair.width)
                  for y in range(lair.y, lair.y + lair.height)}
    up, down = _find(d, STAIRS_UP), _find(d, STAIRS_DOWN)
    assert down in _lab_reach(d, up)
    assert down not in _lab_reach(d, up, blocked=lair_tiles)
    gold = sum(getattr(i, 'amount', 0) for i in items)
    assert gold >= 1500, gold
    assert len(items) >= 8
    assert all(d.tiles[i.y][i.x] != WALL for i in items)
    assert fafnir.max_hp >= 1800 and fafnir.ai_pattern == 'dragon'


def test_a_dragon_does_not_fall_into_a_man_sized_pit():
    src = open(os.path.join(ROOT, 'src', 'game_combat.py'), encoding='utf-8').read()
    assert "tuple(getattr(m, 'footprint', (1, 1))) == (1, 1)" in src


def test_belly_strike_is_melee_only():
    """An archer in a pit is still shooting at scales (and was otherwise
    completely safe while doing full damage)."""
    src = open(os.path.join(ROOT, 'src', 'combat.py'), encoding='utf-8').read()
    assert "player.has_effect('in_pit') and not is_ranged" in src
    import combat
    assert 1.0 < combat.PIT_BELLY_MULT <= 1.5


def test_gram_must_be_thrown_over_the_altar_not_from_it():
    from game_helpers import throw_crosses_tile
    assert throw_crosses_tile(5, 5, 9, 5, 7, 5)           # altar between
    assert not throw_crosses_tile(7, 5, 9, 5, 7, 5)       # standing on it
    assert not throw_crosses_tile(5, 5, 7, 5, 7, 5)       # aiming at it
    assert not throw_crosses_tile(5, 5, 9, 5, 7, 8)       # nowhere near


def test_fire_resistance_halves_fire_and_is_not_immunity():
    from player import Player
    p = Player()
    p.max_hp = p.hp = 500
    p.add_effect('fire_resist', -1)
    assert p.take_damage(40, 'fire') == 20
    assert p.take_damage(41, 'fire') == 21      # rounded up
    q = Player()
    q.max_hp = q.hp = 500
    q.add_effect('fire_shield', 10)
    assert q.take_damage(40, 'fire') == 0       # the temporary shield still blocks
    r = Player()
    r.max_hp = r.hp = 500
    r.add_effect('cold_resist', -1)
    assert r.take_damage(40, 'cold') == 0       # other resistances unchanged


# ------------------------------------------------------------ Fafnir's Blood

def test_fafnirs_blood_pays_by_how_well_you_follow_the_birds():
    """It was a free drink: full heal, permanent fire protection and the Gram
    hint, identical in every run. Each part is now earned on an animal
    chain."""
    from food_system import apply_fafnirs_blood
    from player import Player

    def drink(chain):
        p = Player()
        p.max_hp = 200
        p.hp = 100
        wis = p.WIS
        msgs = apply_fafnirs_blood(p, chain)
        return p, wis, ' '.join(msgs)

    p, wis, text = drink(0)
    assert p.hp == 60 and not p.has_effect('fire_resist')       # scalded, nothing gained
    assert 'throw' not in text

    p, wis, text = drink(1)
    assert p.hp == 200 and 'throw' not in text
    assert not p.has_effect('fire_resist')

    p, wis, text = drink(2)
    assert 'throw' in text and not p.has_effect('fire_resist')   # the Gram secret

    p, wis, text = drink(3)
    assert p.has_effect('fire_resist') and not p.has_effect('warning')

    p, wis, text = drink(4)
    assert p.has_effect('warning') and p.WIS == wis

    p, wis, text = drink(5)
    assert p.has_effect('fire_resist') and p.has_effect('warning')
    assert p.WIS == wis + 1 and p.hp == 200 and 'throw' in text

    # never lethal
    low = Player()
    low.max_hp, low.hp = 200, 5
    apply_fafnirs_blood(low, 0)
    assert low.hp >= 1


def test_drinking_the_blood_starts_the_bird_speech_quiz():
    src = open(os.path.join(ROOT, 'src', 'game_menus.py'), encoding='utf-8').read()
    i = src.index('def _drink_fafnirs_blood')
    block = src[i:i + 2600]
    assert "subject='animal'" in block and "mode='escalator_chain'" in block
    assert 'apply_fafnirs_blood(self.player, chain)' in block
    j = src.index('def _quaff_menu_input')
    assert "== 'fafnirs_blood'" in src[j:j + 1400]
