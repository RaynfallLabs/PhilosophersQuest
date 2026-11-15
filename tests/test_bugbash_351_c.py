"""Bug bash 3.5.1, hunter C: the world and the newest changes (the floor's
clock, the bigger starting population and its small war-bands, mini-boss
tuning, hit lines and the strike preview, the round-3 rule fixes).

Each test failed before its fix."""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, HERE)

import war_bands  # noqa: E402


def _texts(g):
    return [t for t, _ in g.msg_log.entries]


# ------------------------------------------------------- the known roster

def test_one_of_a_role_is_named_in_the_singular():
    """Every gang of footpads has one archer, and a hero who knew the
    captain's kind heard "A leader, two fighters and one archers"."""
    text = war_bands.roster_text({'counts': {'guard': 2, 'shooter': 1, 'caster': 1, 'healer': 0}})
    assert text == 'A leader, two fighters, one archer and one caster'
    line = war_bands.arrival_line({'id': 'footpads', 'counts': {'guard': 1, 'shooter': 1}}, True)
    assert 'one fighter and one archer.' in line, line
    assert 'one archers' not in line and 'one fighters' not in line
    # More than one stays plural.
    assert war_bands.roster_text({'counts': {'guard': 3}}) == 'A leader and three fighters'


# ------------------------------------------------ floor 1's arrival lines

def _game_with(seed_from, want):
    from test_bug_bash_5_encounters import _game
    for seed in range(seed_from, seed_from + 60):
        g = _game(seed)
        if want(g):
            return g
    raise AssertionError('no floor 1 found for the test')


def test_floor_ones_war_band_is_heard_at_the_start():
    """Since 3.5.1 floor 1 holds a war-band on more than half its maps, but
    only _change_level said the band's line: floor 1's was never said at
    the start, and was first heard on coming back up from floor 2."""
    g = _game_with(1, lambda g: isinstance(getattr(g.dungeon, 'band', None), dict))
    band = g.dungeon.band
    assert band['said']
    line = war_bands.data()['bands'][band['id']]['line']
    known = war_bands.data()['bands'][band['id']]['known_line'].split('{roster}')[0]
    assert any(t == line or t.startswith(known) for t in _texts(g)), _texts(g)


def test_floor_ones_atmosphere_is_said_at_the_start_and_only_once():
    """A den's snoring or a vault's coins on floor 1 were never said at the
    start, and were said on the first return to floor 1."""
    g = _game_with(1, lambda g: bool(getattr(g.dungeon, 'atmosphere_messages', None)))
    atmo = list(g.dungeon.atmosphere_messages)
    texts = _texts(g)
    for a in atmo:
        assert texts.count(a) == 1, (a, texts)
    assert g.dungeon._atmosphere_said
    g._say_atmosphere()
    assert _texts(g).count(atmo[0]) == 1


# ------------------------------------------- the run's people and the camp

def _camp_game():
    """A floor-1 game whose war-band camps in rooms[1], every creature
    cleared away (so the camp's tiles are free and only the rule keeps the
    spawners out of them)."""
    from test_bug_bash_5_encounters import _game
    g = _game(7)
    r = g.dungeon.rooms[1]
    g.dungeon.band = {'id': 'footpads', 'uid': 'u', 'leader_kind': 'bandit_captain',
                      'room': (r.x, r.y, r.width, r.height), 'counts': {}, 'said': True}
    g.monsters = []
    g.ground_items = [i for i in g.ground_items if type(i).__name__ != 'MerchantNPC']
    return g, war_bands.camp_tiles(g.dungeon)


def test_no_encounter_npc_or_unicorn_is_set_down_in_a_war_bands_camp():
    """A wounded stranger or the unicorn among a sleeping gang of footpads
    meant fighting the band to talk (bands camp on more than half of the
    floors from floor 1 since 3.5.1)."""
    g, camp = _camp_game()
    assert camp
    enc = {'tag': '__camp_test__', 'name': 'Marta', 'symbol': '@', 'color': [1, 1, 1]}
    for seed in range(40):
        random.seed(seed)
        npc = g._spawn_encounter_npc(enc, '_flavor_encounter_tag', 1)
        assert npc is not None
        assert (npc.x, npc.y) not in camp, seed
        g.monsters.remove(npc)
    for seed in range(40):
        random.seed(seed)
        g._unicorn_spawned = False
        g._unicorn_target_level = 25
        g._maybe_spawn_unicorn(25)
        uni = [m for m in g.monsters if getattr(m, '_is_unicorn', False)]
        assert len(uni) == 1 and (uni[0].x, uni[0].y) not in camp, seed
        g.monsters.remove(uni[0])


def test_no_trader_sets_out_his_stall_in_a_war_bands_camp():
    """The stall went in the first room past the arrival room with a free
    tile, camp or no camp."""
    import road
    g, camp = _camp_game()
    for seed in range(10):
        spot = g._trader_spot(road.rng_for(seed, 'trader:1'))
        assert spot is not None and spot not in camp, seed


def test_the_emberpup_and_old_nickel_are_never_in_a_war_bands_camp():
    g, camp = _camp_game()
    for seed in range(40):
        random.seed(seed)
        g.monsters = []
        g._emberpup = {'floor': 1, 'spawned': False, 'outcome': None,
                       'cloak_floor': 1, 'cloak_spawned': False, 'cloak_seed': seed}
        g._maybe_spawn_emberpup(1)
        g._maybe_spawn_cloak_wearer(1)
        placed = [m for m in g.monsters if getattr(m, '_is_abandoned_emberpup', False)
                  or getattr(m, '_wary_home', None)]
        assert len(placed) == 2, seed
        for m in placed:
            assert (m.x, m.y) not in camp, (seed, m.name)


def test_the_mooble_never_opens_his_cave_off_a_war_bands_camp():
    """His three dance-offs meant three fights through the band."""
    from test_bug_bash_5_encounters import _game

    import copy
    from dungeon import generate_dungeon

    def doorstep(g):
        """The floor tile the cave's mouth opens from."""
        cave = g._mooble_carve_cave()
        assert cave
        wx, wy = cave['mouth']
        cx, cy = cave['centre']
        return (wx - (cx - wx) // 2, wy - (cy - wy) // 2)

    g = _game(21)
    g.monsters = []
    checked = 0
    for mapseed in range(12):
        clean = generate_dungeon(80, 50, 1, random.Random(mapseed))
        for seed in (1, 2, 3):
            g._mooble = {'floor': 1, 'spawned': False, 'outcome': None, 'seed': seed}
            g.dungeon = copy.deepcopy(clean)
            step = doorstep(g)
            room = next(((r.x, r.y, r.width, r.height) for r in clean.rooms
                         if r.x <= step[0] < r.x + r.width and r.y <= step[1] < r.y + r.height), None)
            if room is None:
                continue                      # it opened off a corridor
            # A band camps in the room his cave opened into: it opens elsewhere.
            g.dungeon = copy.deepcopy(clean)
            g.dungeon.band = {'room': room}
            camp = war_bands.camp_tiles(g.dungeon)
            assert doorstep(g) not in camp, (mapseed, seed)
            assert g._mooble_room_spot() not in camp
            checked += 1
    assert checked >= 20


def test_a_floor_with_no_band_has_no_camp():
    from types import SimpleNamespace
    assert war_bands.camp_tiles(SimpleNamespace()) == set()
    assert war_bands.camp_tiles(None) == set()
    rooms = [SimpleNamespace(x=1, y=1), SimpleNamespace(x=9, y=9)]
    assert war_bands.outside_camp(SimpleNamespace(band=None), rooms) == rooms


# ------------------------------------------------ a mini-boss with no room

def test_a_mini_boss_with_nowhere_to_stand_comes_a_floor_later():
    """Surtur (2 x 2) is planned on floor 90, a maze whose few clearings
    the floor's own monsters fill: in about one run in fourteen nowhere fit
    him and he was lost for the run."""
    import items
    from dungeon import Dungeon, Room, WALL, FLOOR, STAIRS_UP, STAIRS_DOWN
    from level_manager import LevelManager
    items.bind_unique_registry(set())
    lm = LevelManager()
    lm._planned_mini_bosses = {90: 'surtur'}
    # A 1-wide corridor and two 1 x 1 rooms: no 2 x 2 fits anywhere.
    w, h = 30, 5
    tiles = [[WALL] * w for _ in range(h)]
    for x in range(1, 29):
        tiles[2][x] = FLOOR
    tiles[2][1] = STAIRS_UP
    tiles[2][28] = STAIRS_DOWN
    d = Dungeon(tiles, [Room(0, 1, 3, 3), Room(13, 1, 3, 3), Room(26, 1, 3, 3)], w, h, 90)
    monsters = []
    lm._try_spawn_mini_boss(d, monsters, 90)
    assert not monsters
    # Not 91 (Thanatos, a seal demon's floor): 92.
    assert lm._planned_mini_bosses == {92: 'surtur'}
    _, ms, _ = lm.generate(92)
    assert any(m.kind == 'surtur' for m in ms)
    assert 'surtur' in lm._placed_mini_bosses


def test_a_carried_mini_boss_never_lands_on_a_floor_already_made():
    import items
    from level_manager import LevelManager
    items.bind_unique_registry(set())
    lm = LevelManager()
    lm._planned_mini_bosses = {90: 'surtur', 94: 'asmodeus'}
    lm._saved = {92: object()}
    assert lm._carry_mini_boss('surtur', 90) == 95
    assert lm._planned_mini_bosses == {94: 'asmodeus', 95: 'surtur'}


# --------------------------------------------- the explore tour of a maze

def _serpentine():
    """A 1-wide passage snaking down a 41 x 21 block, both stairs and the
    floor's only two clearings beside each other at its top left."""
    from dungeon import Dungeon, Room, WALL, FLOOR, STAIRS_UP, STAIRS_DOWN
    w, h = 45, 25
    tiles = [[WALL] * w for _ in range(h)]
    for row in range(1, 22, 2):
        for x in range(1, 42):
            tiles[row][x] = FLOOR
        if row < 21:
            tiles[row + 1][41 if (row // 2) % 2 == 0 else 1] = FLOOR
    tiles[1][1] = STAIRS_UP
    tiles[1][5] = STAIRS_DOWN
    rooms = [Room(0, 0, 3, 3), Room(4, 0, 3, 3)]          # centres (1, 1) and (5, 1)
    return Dungeon(tiles, rooms, w, h, 10)


def test_a_mazes_tour_walks_its_passages():
    """A maze floor's few clearings were its whole tour: a maze whose up and
    down stairs sat in two clearings side by side had a tour of 4 tiles and
    100 turns of grace, in a maze of 450 tiles of passage."""
    import wanderers
    d = _serpentine()
    tour = wanderers.explore_tour(d)
    assert tour >= 300, tour
    assert wanderers.grace(d) >= 700


def test_the_real_maze_floors_get_a_maze_sized_grace():
    import wanderers
    from dungeon import generate_dungeon
    for seed in range(4):
        d = generate_dungeon(80, 50, 10 + 20 * seed, random.Random(seed))
        assert d.is_maze
        walk = len(wanderers._walk_map(d))
        assert wanderers.explore_tour(d) >= walk // 2, (seed, wanderers.explore_tour(d), walk)


def test_a_room_and_corridor_floor_keeps_its_rooms_only_tour():
    """The maze rule never touches a floor of rooms and corridors (its
    rooms hold three quarters of its ground), so 3.5.1's measured graces
    stand."""
    import wanderers
    from dungeon import generate_dungeon
    for seed, level in ((1, 1), (2, 5), (3, 33), (4, 77)):
        d = generate_dungeon(80, 50, level, random.Random(seed))
        ok = wanderers._walk_map(d)
        assert wanderers._passage_stops(d, ok, d.rooms) == [], level


def test_a_room_with_water_at_its_centre_is_still_toured():
    """A room whose centre was water or a statue was left out of the tour."""
    import wanderers
    from dungeon import Dungeon, Room, WALL, FLOOR, WATER, STAIRS_UP, STAIRS_DOWN
    w, h = 40, 9
    tiles = [[WALL] * w for _ in range(h)]
    rooms = [Room(0, 0, 9, 9), Room(26, 0, 9, 9)]          # centres (4, 4), (30, 4)
    for r in rooms:
        for y in range(r.y + 1, r.y + r.height - 1):
            for x in range(r.x + 1, r.x + r.width - 1):
                tiles[y][x] = FLOOR
    for x in range(8, 27):
        tiles[4][x] = FLOOR                                   # the corridor between
    tiles[4][3] = STAIRS_UP
    tiles[4][4] = STAIRS_DOWN
    tiles[4][30] = WATER
    d = Dungeon(tiles, rooms, w, h, 1)
    # Up (3,4) -> first room (4,4) -> beside the pool (29,4) -> down (4,4).
    assert wanderers.explore_tour(d) == 1 + 25 + 25
