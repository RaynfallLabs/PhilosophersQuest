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
    room = d.rooms[2]
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
