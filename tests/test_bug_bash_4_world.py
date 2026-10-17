"""Bug bash 4 (2026-10-16), world angle: generation, reachability, quests,
endings, divine, traps, builds and encounters. Each test names what was
wrong. Behaviour tests on a real Game where one can be built; the rest call
the real functions on a small hand-made floor.

Deep content (floor 65, floor 100, the Cow Level, the Death chase) cannot be
play-tested in a sitting, so these are the guard. Floors are generated with
the game's own random state, so the generation tests run several floors.
"""
import collections
import copy
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import dungeon as D  # noqa: E402
from dungeon import (FLOOR, WALL, WATER, DOOR, SECRET_DOOR, STAIRS_UP,  # noqa: E402
                     STAIRS_DOWN, generate_dungeon, spawn_items)


@pytest.fixture(autouse=True)
def _no_saves(monkeypatch, tmp_path):
    """Nothing these tests do may touch the player's real saves or bones."""
    import save_system
    import bones
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    yield


def _game(name='__bb4_world__', build=None):
    from main import Game
    import items
    items.bind_unique_registry(set())
    screen = pygame.display.set_mode((1, 1))
    if isinstance(build, str):
        from welcome_screen import SECRET_BUILDS
        name, build = build, SECRET_BUILDS[build]
    return Game(screen, player_name=name, secret_build=build)


def _walk4(d, start, through=()):
    """Where the hero can walk from `start`: four ways, through doors and
    secret doors (they can be found), never through water, lava or rock."""
    through = set(through)
    seen = {start}
    q = collections.deque([start])
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) in seen or not d.in_bounds(nx, ny):
                continue
            if d.is_walkable(nx, ny) or d.tiles[ny][nx] in (DOOR, SECRET_DOOR) or (nx, ny) in through:
                seen.add((nx, ny))
                q.append((nx, ny))
    return seen


def _bare_game(rows):
    """A Game with no floor generated: just a hand-made map."""
    from main import Game
    code = {'#': WALL, '.': FLOOR, '~': WATER, '<': STAIRS_UP, '>': STAIRS_DOWN, '+': DOOR}
    tiles = [[code[c] for c in row] for row in rows]
    g = Game.__new__(Game)
    g.dungeon = D.Dungeon(tiles, [], len(rows[0]), len(rows), 5)
    g.dungeon_level = 5
    g.player = types.SimpleNamespace(x=1, y=1, alive=True)
    g.monsters, g.ground_items, g.pets = [], [], []
    g.msgs = []
    g.add_message = lambda text, kind='info': g.msgs.append(text)
    return g


# ===================================================================== reachability
def test_reach_is_four_ways_like_the_hero_walks():
    """WR2: the flood stepped diagonally; the hero only has the four arrows,
    so quest pieces and teleport landings behind a corner counted as in reach."""
    g = _bare_game(['#####',
                    '#.###',
                    '##.##',
                    '#####'])
    assert (2, 2) not in g._reachable_tiles(1, 1)


def test_teleport_never_strands_the_hero_behind_a_diagonal():
    """WR2: on seed 105 floor 92, 86 of 400 teleports landed where no walk led
    back to the stairs."""
    g = _bare_game(['#######',
                    '#<..#.#',
                    '#...#.#',
                    '####.##',
                    '#######'])
    g._refresh_fov = lambda: None
    g.quirk_system = None
    reach = _walk4(g.dungeon, (1, 1))
    for _ in range(60):
        g._teleport_player()
        assert (g.player.x, g.player.y) in reach


def test_womans_beard_can_be_reached_on_foot():
    """WR1: the beard's secret door was cut at the room's corner, which meets
    the room only diagonally: out of reach on foot in 81% of runs."""
    for _ in range(12):
        d, items = generate_dungeon(80, 50, 65), None
        items = spawn_items(d.rooms, 65, d)
        beard = next(i for i in items if getattr(i, 'id', '') == 'womans_beard')
        assert (beard.x, beard.y) in _walk4(d, d.rooms[0].center)


def test_a_pool_island_is_never_chosen_for_a_quest_structure():
    """WR3: an altar, forge or fountain built on a room centre that a pool had
    made an island could never be reached (a quest step lost ~1 run in 10)."""
    rows = ['###########',
            '#<.......##',
            '#.~~~~~..##',
            '#.~...~..##',
            '#.~...~..##',
            '#.~~~~~..##',
            '#........##',
            '###########']
    code = {'#': WALL, '.': FLOOR, '~': WATER, '<': STAIRS_UP}
    tiles = [[code[c] for c in r] for r in rows]
    room = D.Room(1, 2, 9, 5)                   # its centre (5, 4) is the island
    d = D.Dungeon(tiles, [room], len(rows[0]), len(rows), 37)
    ax, ay = D._structure_anchor(d, room)
    assert (ax, ay) in _walk4(d, (1, 1))
    import random
    pos = D._find_or_place_feature(d, [D.Room(0, 0, 3, 3), room], random.Random(1), D.ALTAR)
    assert pos in _walk4(d, (1, 1))


@pytest.mark.parametrize('level,attr', [(37, 'athena_altar_pos'), (53, 'odin_altar_pos'),
                                        (17, 'ariadne_fountain_pos'), (78, 'dwarven_forge_pos'),
                                        (79, 'vidar_altar_pos'), (99, 'judgment_altar_pos')])
def test_quest_structures_stand_where_the_hero_can_walk(level, attr):
    for _ in range(6):
        d = generate_dungeon(80, 50, level)
        spawn_items(d.rooms, level, d)
        pos = getattr(d, attr)
        assert pos in _walk4(d, D._find_stair_tiles(d.tiles, d.width, d.height)[0])


def test_sealed_shrine_doors_open_onto_walkable_floor():
    for level, door_attr in ((17, 'ariadne_shrine_door'), (37, 'athena_shrine_door'),
                             (53, 'odin_shrine_door')):
        for _ in range(4):
            d = generate_dungeon(80, 50, level)
            spawn_items(d.rooms, level, d)
            door = getattr(d, door_attr, None)
            if door is None:
                continue
            walk = _walk4(d, D._find_stair_tiles(d.tiles, d.width, d.height)[0])
            assert any((door[0] + a, door[1] + b) in walk
                       for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def test_ariadnes_thread_stays_in_its_sealed_shrine():
    """TR1: _bring_within_reach lifted the Thread out of its shrine on every
    run, so the Bronze Bull step was never needed."""
    g = _game()
    for _ in range(3):
        g.level_mgr._saved.pop(17, None)
        g._change_level(17, True)
        centre = getattr(g.dungeon, 'ariadne_shrine_thread_pos', None)
        if centre is None:
            continue
        thread = next(i for i in g.ground_items if getattr(i, 'id', '') == 'ariadnes_thread')
        assert (thread.x, thread.y) == tuple(centre)
        assert centre not in g._reachable_tiles(g.player.x, g.player.y)


def test_quest_and_secret_ending_pieces_are_needed_to_finish():
    """DV7 / E4 / WR3: the Broken Gram, the lore pieces of the secret ending,
    the encounter trigger items, the carrot, the duck and the unicorn were
    left in cut-off pockets (the Lake of Fire scroll 2% of runs)."""
    from main import Game
    for iid in ('broken_gram', 'abyssal_shimmer', 'philosophers_wrench', 'scroll_lake_of_fire',
                'tablet_of_second_death', 'silverlight_pendant', 'oathkeeper_sword',
                'lionheart_shield', 'magic_dungeon_carrot', 'duck_of_doom'):
        assert Game._needed_to_finish(types.SimpleNamespace(id=iid)), iid
    assert Game._needed_to_finish(types.SimpleNamespace(_is_unicorn=True))
    assert not Game._needed_to_finish(types.SimpleNamespace(id='steel_rapier'))


def test_a_two_tile_legendary_in_a_pocket_is_brought_within_reach():
    """WR6: only 1x1 creatures were moved; a 2x2 legendary stayed stranded."""
    g = _bare_game(['##########',
                    '#.....#..#',
                    '#.....#..#',
                    '#.....####',
                    '##########'])
    big = types.SimpleNamespace(x=7, y=1, alive=True, kind='tiamat', tags=['legendary'],
                                treasure={}, footprint=(2, 2))
    g.monsters = [big]
    g._bring_within_reach()
    reach = g._reachable_tiles(1, 1)
    assert all((big.x + a, big.y + b) in reach for a in (0, 1) for b in (0, 1))


def test_floor_one_is_settled_like_every_other_floor(monkeypatch):
    """WR4 / MK-02 / E10: floor 1 never ran _settle_monsters: two monsters on
    one tile about one new game in 37, and quest pieces left out of reach."""
    import level_manager
    real = level_manager.LevelManager.generate

    def stacked(self, level_num):
        d, mons, its = real(self, level_num)
        live = [m for m in mons if m.alive and tuple(getattr(m, 'footprint', (1, 1))) == (1, 1)]
        if len(live) >= 2:
            live[1].x, live[1].y = live[0].x, live[0].y
        return d, mons, its
    monkeypatch.setattr(level_manager.LevelManager, 'generate', stacked)
    g = _game()
    pos = [(m.x, m.y) for m in g.monsters if m.alive]
    assert len(pos) == len(set(pos))


def test_room_extras_never_land_on_monsters_already_there():
    """MK-02: den, zoo, graveyard and barracks extras were set down blind."""
    for _ in range(10):
        d = generate_dungeon(80, 50, 12)
        room = d.rooms[1]
        taken = [types.SimpleNamespace(x=x, y=y, alive=True) for x, y in room.inner_tiles()
                 if d.is_walkable(x, y)][::2]
        new = D.spawn_monsters([room, room], 12, d, min_count=4, max_count=6, existing=taken)
        old = {(m.x, m.y) for m in taken}
        assert all((m.x, m.y) not in old for m in new)


def test_a_planned_mini_boss_is_not_lost_on_a_full_maze_floor():
    """WR5: a mini-boss planned for a maze floor was lost when the one room
    it could use was full (Surtur on 90: 35 runs in 107; now about 4 in 108,
    when no 2x2 space is left anywhere outside the arrival room)."""
    from level_manager import LevelManager
    for _ in range(5):
        d = generate_dungeon(80, 50, 50)
        assert d.is_maze
        lm = LevelManager()
        lm._planned_mini_bosses = {50: 'rangda'}
        lm._placed_mini_bosses = set()
        crowd = [types.SimpleNamespace(x=x, y=y, alive=True, footprint=(1, 1))
                 for r in d.rooms[1:] for x, y in r.inner_tiles()]
        mons = list(crowd)
        lm._try_spawn_mini_boss(d, mons, 50)
        boss = [m for m in mons if getattr(m, 'kind', '') == 'rangda']
        assert boss
        start = d.rooms[0]
        assert not (start.x <= boss[0].x < start.x + start.width
                    and start.y <= boss[0].y < start.y + start.height)


def test_arrival_passives_read_the_new_floor(monkeypatch):
    """WR7: the Morrigan's ravens mapped a circle round where the hero stood
    on the floor just left."""
    import chain_passives
    g = _game()
    g._change_level(2, True)
    real = chain_passives.player_has_passive
    monkeypatch.setattr(chain_passives, 'player_has_passive',
                        lambda p, f: f == 'raven_scout' or real(p, f))
    g._change_level(3, True)
    px, py = g.player.x, g.player.y
    ring = [(px + a, py + b) for a in range(-11, 12) for b in range(-11, 12)
            if a * a + b * b <= 121 and g.dungeon.in_bounds(px + a, py + b)]
    assert all(t in g.dungeon.explored for t in ring)


@pytest.mark.parametrize('level', [40, 60, 80, 100])
def test_boss_floor_arrival_is_on_the_stair(level):
    """WR8: on the hand-built boss floors the hero arrived two tiles off it."""
    g = _game()
    g._change_level(level, True)
    assert g.dungeon.tiles[g.player.y][g.player.x] == STAIRS_UP


def test_teleport_monster_never_strands_a_seal_keeper():
    """DV8: the wand of teleport monster put a seal keeper in a cut-off pocket
    about one zap in 110; its stair stayed sealed."""
    g = _bare_game(['#########',
                    '#...#...#',
                    '#...#...#',
                    '#########'])
    keeper = types.SimpleNamespace(kind='seal_demon_war', tags=[], treasure={})
    tiles = [(x, y) for y in range(4) for x in range(9) if g.dungeon.is_walkable(x, y)]
    landing = g._teleport_monster_landings(keeper, tiles)
    reach = g._reachable_tiles(1, 1)
    assert landing and all(t in reach for t in landing)
    rat = types.SimpleNamespace(kind='giant_rat', tags=[], treasure={})
    assert g._teleport_monster_landings(rat, tiles) == tiles     # ordinary monsters unchanged


def test_hermetic_step_lands_where_the_stairs_can_be_walked_to():
    """B7: Hermes' step had no reachability filter, could land on a pet, and
    never counted as a teleport for Hermes' Wings."""
    import hero_specials
    g = _bare_game(['#########',
                    '#<....#.#',
                    '#.....#.#',
                    '#########'])
    g.player.x, g.player.y = 2, 1
    g._refresh_fov = lambda: None
    seen = []
    g.quirk_system = types.SimpleNamespace(on_teleport=lambda: seen.append(1))
    g.player.status_effects = {}
    pet = types.SimpleNamespace(x=3, y=2, alive=True)
    g.pets = [pet]
    reach = _walk4(g.dungeon, (1, 1))
    for _ in range(40):
        hero_specials._eff_teleport_self(g, {}, {'range': 99, 'haste': 0}, 5)
        assert (g.player.x, g.player.y) in reach and (g.player.x, g.player.y) != (3, 2)
    assert len(seen) == 40


def test_encounter_spawns_fall_back_when_the_rooms_are_full():
    """E5: on a full maze floor the cow, unicorn, carrot and NPCs found no
    tile and were lost for the run."""
    g = _game()
    from monster import Monster
    filler = {'id': 'x', 'name': 'Filler', 'hp': 1, 'attacks': [], 'ai_pattern': 'sessile',
              'symbol': 'x', 'color': [1, 1, 1]}
    g.monsters = [Monster(dict(filler), x, y) for r in g.dungeon.rooms[1:]
                  for x, y in r.inner_tiles() if g.dungeon.is_walkable(x, y)]
    g._cow_spawned = g._cow_level_done = False
    g._cow_level = g.dungeon_level
    g._maybe_spawn_cow(g.dungeon_level)
    assert g._cow_spawned and g._cow_npc is not None
    assert (g._cow_npc.x, g._cow_npc.y) in g._reachable_tiles(g.player.x, g.player.y)


def test_psychopomp_step_on_the_cow_level_goes_home(monkeypatch):
    """E7: a death on the Moo Moo Farm (999) carried the hero to floor 998."""
    import chain_passives
    from boss_levels import COW_LEVEL
    g = _game()
    g.dungeon_level = COW_LEVEL
    went = []
    g._exit_cow_level = lambda: went.append('home')
    g._change_level = lambda lv, top: went.append(lv)
    monkeypatch.setattr(chain_passives, 'consume_run_passive', lambda p, f: f == 'psychopomp_step')
    monkeypatch.setattr(chain_passives, 'player_has_passive', lambda p, f: False)
    g.player.hp = 0
    g._answer_a_killing_blow()
    assert went == ['home']


# ===================================================================== endings and divine
def _stone():
    from items import Artifact
    return Artifact({'id': 'philosophers_stone', 'name': "Philosopher's Stone",
                     'item_class': 'artifact', 'weight': 1, 'symbol': '*', 'color': [255, 255, 255]})


def test_leaving_floor_100_with_the_stone_by_any_route_sets_death_loose():
    """DV2: only the stair started the chase, so a gain-level potion on 100
    carried the Stone to a full victory unpursued."""
    g = _game()
    g._change_level(100, True)
    g.player.inventory.append(_stone())
    g._change_level(99, False)          # what the potion of gain level does
    assert g.death_pursues and g.death_monster is not None


def test_holy_fire_that_runs_out_off_the_floor_gives_abaddon_his_guard_back():
    """DV1: the restore looked only at the current floor; pray on 100, wait on
    99, and Abaddon stayed stripped for good."""
    g = _game()
    g._change_level(100, True)
    ab = next(m for m in g.monsters if m.kind == 'abaddon_destroyer')
    base = list(ab.base_resistances)
    ab.resistances, ab.damage_ward = [], 0.0
    g.abaddon_resist_removed_turns = 1
    g._change_level(99, False)
    g.abaddon_resist_removed_turns = 0              # ran out up here
    g._change_level(100, True)
    ab = next(m for m in g.monsters if m.kind == 'abaddon_destroyer')
    assert ab.resistances == base and ab.damage_ward == ab.base_damage_ward > 0


def test_the_judgments_curse_reaches_abaddon_even_if_floor_100_came_first():
    """DV4: the +50% was applied only to a floor 100 generated after the
    verdict: go down first, come back up to kneel, and nothing happened."""
    g = _game()
    g._change_level(100, True)
    hp = next(m for m in g.monsters if m.kind == 'abaddon_destroyer').max_hp
    g._change_level(99, False)
    g._abaddon_empowered = True
    g._change_level(100, True)
    ab = next(m for m in g.monsters if m.kind == 'abaddon_destroyer')
    assert ab.max_hp == hp + int(hp * 0.5)
    g._change_level(99, False)
    g._change_level(100, True)                      # once only
    assert next(m for m in g.monsters if m.kind == 'abaddon_destroyer').max_hp == ab.max_hp


def test_the_flux_capacitor_comes_once_a_run():
    """DV3: "Nobody calls me chicken!" dropped a Flux Capacitor every time."""
    g = _game()
    for _ in range(4):
        g._chicken_input(pygame.K_2)
    assert sum(1 for i in g.ground_items if getattr(i, 'id', '') == 'flux_capacitor') == 1


def test_a_spent_floor_100_altar_still_answers_the_prayer():
    """DV6: it returned with nothing and the longest cooldown."""
    g = _game()
    g._change_level(100, True)
    p = g.player
    g._l100_altars_used = {(p.x, p.y)}
    p.hp = 1
    g._resolve_simple_prayer(3, at_altar=True)
    assert p.hp > 1


def test_the_cow_level_is_not_new_depth():
    """DV11 / E8: the trip to 999 recharged every once-a-floor ward."""
    from boss_levels import COW_LEVEL
    g = _game()
    for lv in range(2, 7):
        g._change_level(lv, True)
    g._death_save_used = True
    g.player._hrunting_save_used = True
    g._cow_return_level = 6
    g._change_level(COW_LEVEL, True)
    assert g._death_save_used and g.player._hrunting_save_used
    g._change_level(6, False)
    assert g._death_save_used and g.player._hrunting_save_used


def test_death_only_announces_a_quickening():
    """DV13: going back down past a band edge slowed Death and printed
    "Death quickens."."""
    g = _game()
    g.msgs = []
    g.add_message = lambda t, k='info': g.msgs.append(t)
    g.death_pursues = True
    g.death_monster = types.SimpleNamespace(_speed_pct=100)
    g.dungeon_level = 51
    g._maybe_escalate_death()
    assert g.death_monster._speed_pct == 75 and not any('quickens' in m for m in g.msgs)


def test_no_bones_are_written_on_floor_100(monkeypatch):
    """DV16: floor 100 never loads bones; its file just held a slot."""
    import bones
    calls = []
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: calls.append(a))
    g = _game()
    g.dungeon_level = 100
    g.defeat_reason = 'died'
    g._on_game_over()
    assert calls == []


def test_divine_intercession_never_hands_out_a_claimed_or_scripted_unique():
    """DV17: the relic pool ignored the run's unique registry, and its
    fallback handed out quest and hero pieces."""
    import items
    from items import load_items, is_random_loot
    g = _game()
    seen = set()
    for t in load_items('artifact'):
        if is_random_loot(t):
            seen.add(t.id)
    items.bind_unique_registry(set(seen))     # every freely-given relic claimed
    for _ in range(20):
        g.ground_items = []
        g._spawn_intercession_artifact(g.player.x, g.player.y)
        for it in g.ground_items:
            assert it.id not in seen and is_random_loot(it)


def test_text_fixes_in_the_divine_and_mystery_screens():
    """DV12, DV14, DV15, DV18, DV19, DV20, DV21."""
    import mystery_system
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert "_eco.written_gold(m['gold_cost'])" in src                    # DV12
    assert '50,000 Death is dead' in src                                  # DV14
    assert 'Slain on the Moo Moo Farm.' in src                            # DV15
    main_src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    assert 'Death climbs the stair behind you.' in main_src               # DV18
    magic = open(os.path.join(ROOT, 'src', 'game_magic.py'), encoding='utf-8').read()
    assert 'f"The {old_name} vanishes' not in magic and 'f"The {target_m.name} vanishes' not in magic
    assert '(Perception +1)' in mystery_system.MYSTERIES['brendan']['reward_text']
    assert '(Wisdom +2, Intelligence +1)' in mystery_system.MYSTERIES['jerome']['reward_text']
    bl = open(os.path.join(ROOT, 'src', 'boss_levels.py'), encoding='utf-8').read()
    assert 'placed here\n    by the level manager' not in bl                 # DV21


def test_guide_my_hand_line_is_in_sentence_case():
    """DV18: "A Hand Closes Over Yours. Wisdom +N For N Turns."."""
    g = _game()
    g.msgs = []
    g.add_message = lambda t, k='info': g.msgs.append(t)
    g._answer_guide_my_hand(5, 5, 5, 0.05)
    assert any(m.startswith('A hand closes over yours. Wisdom +') for m in g.msgs)
    assert any('A shield stands over you.' in m for m in g.msgs)


# ===================================================================== traps and containers
def _trap(kind='arrow'):
    return {'type': kind, 'damage': '1d4', 'damage_type': 'physical',
            'message': 'Click!', 'symbol': '^', 'color': (1, 1, 1), 'revealed': True}


def test_an_alarm_wakes_the_nearby_and_roots_stay_rooted():
    """TR3: the alarm turned sessile monsters aggressive for good and woke
    nobody."""
    from monster import Monster
    import json
    defs = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    g = _game()
    px, py = g.player.x, g.player.y
    gob = Monster({**defs['goblin'], 'id': 'goblin'}, px + 3, py)
    gob.status_effects['sleeping'] = 50
    eye = Monster({**defs['floating_eye'], 'id': 'floating_eye'}, px + 2, py)
    pattern = eye.ai_pattern
    g.monsters = [gob, eye]
    g.dungeon.traps[(px, py)] = _trap('alarm')
    g._check_floor_trap(px, py, forced=True)
    assert gob._alerted and 'sleeping' not in gob.status_effects
    assert eye.ai_pattern == pattern


def test_a_mimic_never_comes_out_on_the_hero_or_a_monster():
    """TR5 / MK-01: a chest picked from underfoot put the mimic on the hero,
    where no blow could reach it."""
    from container_system import _spawn_mimic
    g = _game()
    px, py = g.player.x, g.player.y
    chest = types.SimpleNamespace(x=px, y=py)
    m = _spawn_mimic(chest, g.monsters, 5, dungeon=g.dungeon, avoid=(px, py))
    assert (m.x, m.y) != (px, py)
    m2 = _spawn_mimic(types.SimpleNamespace(x=m.x, y=m.y), g.monsters, 5,
                      dungeon=g.dungeon, avoid=(px, py))
    assert (m2.x, m2.y) not in ((m.x, m.y), (px, py))


def test_a_fumbled_disarm_cannot_be_sidestepped_and_does_not_pit_the_wrong_tile():
    """TR6: the fumble ran the step-on code, so the PER sidestep or levitation
    cancelled it, and a pit put the hero in a pit he was not standing in."""
    g = _game()
    g.msgs = []
    g.add_message = lambda t, k='info': g.msgs.append(t)
    g._advance_turn = lambda: None
    g.player.PER = 40                       # sidestep chance 85%
    g.player.add_effect('levitating', 50)
    px, py = g.player.x, g.player.y
    for _ in range(5):
        g.dungeon.traps[(px + 1, py)] = _trap('arrow')
        g._resolve_trap_disarm((px + 1, py), 'arrow', 1)
        assert (px + 1, py) not in g.dungeon.traps
        assert not any('sidestep' in m or 'float' in m for m in g.msgs)
    g.dungeon.traps[(px + 1, py)] = _trap('pit')
    g._resolve_trap_disarm((px + 1, py), 'pit', 1)
    assert not g.player.has_effect('in_pit')


def test_p_picks_an_adjacent_chest_and_skips_a_rewired_trap():
    """TR7 / TR15: P always disarmed first (rewired traps too: a chain of 3
    deleted your own trap, a 5 gave another hint)."""
    g = _game()
    px, py = g.player.x, g.player.y
    t = _trap('arrow')
    t['safe_for_player'] = t['rewired'] = True
    g.dungeon.traps = {(px + 1, py): t}
    assert g._try_disarm_trap() is False
    from items import load_items
    chest = copy.copy(load_items('container')[0])
    chest.x, chest.y = px, py - 1
    chest.is_mimic = False
    g.ground_items.append(chest)
    g.dungeon.traps[(px - 1, py)] = _trap('arrow')
    g._player_input(pygame.K_p)
    assert 'DISARMING' not in (g.quiz_title or '')


def test_a_teleport_trap_is_taken_apart_not_rewired():
    """TR15: rewired teleport, rust and polymorph traps did nothing to a monster."""
    g = _game()
    g._advance_turn = lambda: None
    g.dungeon.traps = {(3, 3): _trap('teleport')}
    g._resolve_trap_disarm((3, 3), 'teleport', 4)
    assert (3, 3) not in g.dungeon.traps


def test_loot_is_never_placed_on_stairs_or_altars():
    """TR10: loot on the down stair hid it (5.6% of floors)."""
    import random
    from items import load_items
    tiles = [[WALL] * 5 for _ in range(5)]
    for x, y in ((1, 1), (2, 1), (3, 1), (1, 2), (2, 2), (3, 2), (1, 3), (2, 3)):
        tiles[y][x] = STAIRS_DOWN if (x, y) == (1, 1) else D.ALTAR
    tiles[3][3] = FLOOR
    d = D.Dungeon(tiles, [], 5, 5, 3)
    room = D.Room(0, 0, 5, 5)
    for seed in range(10):
        out = []
        assert D._place_one(load_items('potion')[:3], room, d, out, random.Random(seed))
        assert (out[0].x, out[0].y) == (3, 3)


def test_a_rewired_trap_out_of_sight_says_nothing():
    """TR11: the visibility test was always true."""
    from monster import Monster
    import json
    defs = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    g = _game()
    g.msgs = []
    g.add_message = lambda t, k='info': g.msgs.append(t)
    g.visible = set()
    m = Monster({**defs['goblin'], 'id': 'goblin'}, 3, 3)
    g.monsters = [m]
    g._fire_trap_on_monster(m, _trap('alarm'), (3, 3))
    assert not any('snaps on' in t for t in g.msgs)


def test_trap_lines_use_an_before_a_vowel():
    """TR12: "You notice a arrow trap"."""
    g = _game()
    g.msgs = []
    g.add_message = lambda t, k='info': g.msgs.append(t)
    g.player.PER = 1000                     # always sidesteps
    px, py = g.player.x, g.player.y
    g.dungeon.traps[(px, py)] = _trap('arrow')
    g._check_floor_trap(px, py)
    assert any('You notice an arrow trap' in t for t in g.msgs)
    magic = open(os.path.join(ROOT, 'src', 'game_magic.py'), encoding='utf-8').read()
    assert "' swings' if opened" in magic or "'s swing' if opened != 1 else ' swings'" in magic


def test_a_fire_chest_trap_is_fire_damage():
    """TR16: every chest trap was 'physical', so fire resistance never counted."""
    from container_system import _trigger_trap
    seen = []
    p = types.SimpleNamespace(max_hp=60, take_damage=lambda n, t='physical': seen.append(t) or n,
                              add_effect=lambda *a, **k: True)
    _trigger_trap(p, {'damage': '2d6', 'damage_type': 'fire', 'message': 'Flame!'}, [])
    assert seen == ['fire']
    import json
    data = json.load(open(os.path.join(ROOT, 'data', 'chest_traps.json'), encoding='utf-8'))
    flame = [t for tier in data['traps_by_tier'].values() for t in tier if t['type'] == 'flame']
    assert flame and flame[0]['damage_type'] == 'fire'


def test_spawn_at_never_puts_a_monster_on_the_hero():
    """MK-12: a failed fountain, grave or throne could spawn on the hero."""
    g = _game()
    px, py = g.player.x, g.player.y
    for _ in range(10):
        n = len(g.monsters)
        g._spawn_at(px, py)
        if len(g.monsters) > n:
            assert (g.monsters[-1].x, g.monsters[-1].y) != (px, py)


# ===================================================================== builds and traits
def test_sibyl_counts_the_deepest_floor_not_the_current_one():
    """B1: a hero on 30 climbed back to 19 and earned "before level 20"."""
    g = _game()
    g.correct_answers = 2000
    g.player.deepest_floor_reached = 30
    g.dungeon_level = 19
    g.quirk_system.on_turn()
    assert not g.quirk_system.is_unlocked('sibyl')


def test_eye_of_the_storm_is_not_wiped_by_a_stair_bounce():
    """B2: one step up and back down reset the floor's damage."""
    g = _game()
    qs = g.quirk_system
    qs._sp('eye_storm_no_damage_prev', False)       # hurt on this floor
    qs.fresh_descent = False                        # up a stair and back
    qs.on_floor_entered(2)
    assert qs._p('eye_storm_no_damage_prev') is False
    qs.fresh_descent = True
    qs.on_floor_entered(3)
    assert qs._p('eye_storm_clean_floors', 0) == 0


@pytest.mark.parametrize('build', ['corwin', 'cain', 'fianna', 'fluffs',
                                   'leonardo di ser piero da vinci'])
def test_every_build_starts_full(build):
    """B5: the kit's carry bonuses raised the maximum after HP/MP were filled."""
    g = _game(build=build)
    p = g.player
    assert (p.hp, p.mp, p.sp) == (p.max_hp, p.max_mp, p.max_sp)


def test_joan_and_hildegard_heal_nothing_on_a_failed_quiz():
    """B8: chain 0 still healed 6%."""
    import hero_specials
    g = _game()
    g.player.hp = 5
    hero_specials._eff_heal_and_crit_buff(g, {}, {'heal': 0, 'crit_turns': 0}, 0)
    hero_specials._eff_aoe_heal_self(g, {}, {'self_heal': 0, 'cleanse': 0}, 0)
    assert g.player.hp == 5


def test_hephaestus_counts_equips_only():
    """B11: unequips counted too, so it unlocked on the 8th equip."""
    g = _game()
    qs = g.quirk_system
    for _ in range(8):
        qs.on_item_equipped('leather_armor', 'armor', 'body')
        qs.on_item_unequipped('leather_armor', 'armor', 'body')
    assert not qs.is_unlocked('hephaestus')


def test_trait_texts_match_their_thresholds():
    """B12."""
    import quirk_system
    import quirk_text
    assert 'More than once' not in quirk_text.QUIRK_HINT['gorgon_ward']
    qsrc = open(os.path.join(ROOT, 'src', 'quirk_system.py'), encoding='utf-8').read()
    assert 'Twenty-five correct in a row' not in qsrc
    assert quirk_system._QUIRK_PROGRESS['time_dilation'][1] == 50
    assert f'-- {len(quirk_system._QUIRK_PROGRESS)} Bofuri-style traits' in qsrc


def test_secret_build_names_keep_their_small_words_lower_case():
    """B14: "Achilles Son Of Peleus", "Leonardo Di Ser Piero Da Vinci"."""
    assert _game(build='achilles son of peleus').player_name == 'Achilles Son of Peleus'
    assert _game(build='leonardo di ser piero da vinci').player_name == 'Leonardo di Ser Piero da Vinci'
    assert _game(build='prometheus the firebearer').player_name == 'Prometheus the Firebearer'


def test_hero_specials_are_refreshed_from_the_code_on_load(tmp_path, monkeypatch):
    """B16: a save kept its own copy of the special dicts forever."""
    import save_system
    from main import Game
    g = _game(build='hermes trismegistus')
    assert g.player.hero_specials
    g.player.hero_specials[0] = dict(g.player.hero_specials[0], label='STALE')
    assert save_system.save_game(g)
    state = save_system.load_game(g.player_name)
    g2 = Game(pygame.display.set_mode((1, 1)), player_name=g.player_name,
              secret_build=g.secret_build)
    g2.load_state(state)
    assert g2.player.hero_specials[0].get('label') != 'STALE'


def test_hero_special_texts():
    """B19: "(1 traps revealed)", "N foe(s) caught" counting NPCs, "age Thirteen"."""
    import hero_specials
    g = _game()
    g.msgs = []
    g.add_message = lambda t, k='info': g.msgs.append(t)
    g.dungeon.traps = {(g.player.x + 1, g.player.y): _trap()}
    g.dungeon.traps[(g.player.x + 1, g.player.y)]['revealed'] = False
    hero_specials._eff_reveal_radius(g, {}, {'radius': 3}, 3)
    assert any('(1 trap revealed' in m for m in g.msgs)
    src = open(os.path.join(ROOT, 'src', 'hero_specials.py'), encoding='utf-8').read()
    assert 'age Thirteen' not in src and 'foe(s) caught' not in src


# ===================================================================== encounters
def test_the_unicorn_never_eats_on_the_heros_tile():
    """E9: a carrot dropped at the hero's feet put her on his tile."""
    from monster import Monster
    g = _game()
    px, py = g.player.x, g.player.y
    u = Monster({'id': 'ethereal_unicorn', 'name': 'Ethereal Unicorn', 'hp': 200,
                 'attacks': [], 'ai_pattern': 'sessile', 'symbol': 'u', 'color': [1, 1, 1]}, px + 2, py)
    u._is_unicorn, u._unicorn_state, u._unicorn_wait, u._unicorn_eat_turns = True, 'relaxing', 0, 0
    g.monsters = [u]
    carrot = types.SimpleNamespace(id='magic_dungeon_carrot', x=px, y=py)
    g.ground_items = [carrot]
    g.dungeon.tiles[py][px + 1] = FLOOR
    g._tick_unicorn()
    assert u._unicorn_state == 'eating' and (u.x, u.y) != (px, py)
    g._tick_unicorn()
    g._tick_unicorn()
    assert carrot not in g.ground_items and u._unicorn_state == 'trusting'


def test_house_of_atreus_scions_are_named_people():
    """E11: "The Agamemnon hits you"."""
    from monster import the_name
    g = _game()
    for _ in range(20):
        n = len(g.monsters)
        g._spawn_house_of_atreus(g.dungeon_level)
        if len(g.monsters) > n:
            m = g.monsters[-1]
            assert the_name(m) == m.name
            return


def test_encounter_chronicle_lines_carry_their_article():
    """E14: "Met Lost Girl.", "Met The Penitent."."""
    from monster import Monster
    g = _game()
    npc = Monster({'id': 'npc_traveler', 'name': 'Lost Girl', 'hp': 1, 'attacks': [],
                   'ai_pattern': 'sessile', 'symbol': 'p', 'color': [1, 1, 1]}, 3, 3)
    g._npc_encounter_monster = npc
    g._npc_encounter_active = {'tag': 'lost_girl', 'name': 'Lost Girl'}
    g._npc_is_flavor = False
    g._npc_selected_option = {}
    g._close_npc_encounter(resolved=True)
    # With no line of its own an encounter is only "Met the Lost Girl."
    # (the generic random verbs are gone, DEEDS_KARMA_DESIGN 7.7).
    lines = [e['text'] for e in g._chronicle]
    assert lines and lines[-1] == 'Met the Lost Girl.'
    src = open(os.path.join(ROOT, 'src', 'game_encounters.py'), encoding='utf-8').read()
    assert '(Regenerating, 30 turns)' in src                              # E15
