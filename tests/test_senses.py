"""Dungeon Alive slice 1: monsters notice the hero by sight, sound and lore
senses, never through stone by magic (src/senses.py, data/senses.json).

Brandon, 2026-11-12: "NONE automatically know where you are unless it's
thematically and lore appropriate." These tests build small real maps (two
rooms and a wall between them) and run Monster.take_turn on them.
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import senses  # noqa: E402
from dungeon import Dungeon, Room, WALL, FLOOR, DOOR  # noqa: E402
from monster import Monster  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), '..')


class Hero:
    def __init__(self, x, y, dex=10):
        self.x, self.y = x, y
        self.hp = self.max_hp = 50
        self.status_effects = {}
        self.equipped_accessories = []
        self.boons_taken = {}
        self.STR = self.CON = self.INT = self.WIS = self.PER = 10
        self.DEX = dex

    def has_effect(self, name):
        return self.status_effects.get(name, 0) > 0

    def is_burdened(self):
        return False

    def get_ac(self):
        return 10


def two_rooms(door=False):
    """Two 9x9 rooms side by side, a solid wall at x == 10 between them, and
    a corridor round the bottom (y == 12) that joins them. With door=True
    the corridor has a closed door in it."""
    w, h = 21, 14
    tiles = [[WALL] * w for _ in range(h)]
    for y in range(1, 10):
        for x in range(1, 10):
            tiles[y][x] = FLOOR
        for x in range(11, 20):
            tiles[y][x] = FLOOR
    for y in range(10, 13):
        tiles[y][2] = FLOOR
        tiles[y][18] = FLOOR
    for x in range(2, 19):
        tiles[12][x] = FLOOR
    if door:
        tiles[12][10] = DOOR
    rooms = [Room(0, 0, 11, 11), Room(10, 0, 11, 11)]
    return Dungeon(tiles, rooms, w, h, 5)


def make(kind='goblin', x=15, y=5, **extra):
    data = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    d = {**data[kind], 'id': kind}
    d.update(extra)
    return Monster(d, x, y)


def setup_function(_):
    senses.begin_turn(moved=True, guilty=False, floor=5)


# ---------------------------------------------------------------------------

def test_a_wall_hides_the_hero_from_eyes():
    dun = two_rooms()
    hero = Hero(7, 5)                       # 8 tiles away, behind the wall
    gob = make('goblin', 15, 5)
    assert senses.perceive(gob, hero, dun) is None
    for _ in range(5):
        gob.take_turn(hero, dun, [gob])
    assert not gob._tracking
    assert not gob._aware


def test_a_clear_view_is_seen():
    dun = two_rooms()
    hero = Hero(12, 5)
    gob = make('goblin', 17, 5)
    assert senses.perceive(gob, hero, dun) == 'sight'
    gob.take_turn(hero, dun, [gob])
    assert gob._tracking and gob._aware


def test_invisible_hero_is_not_seen_but_a_wolf_smells_him():
    dun = two_rooms()
    hero = Hero(12, 5)
    hero.status_effects['invisible'] = 10
    gob = make('goblin', 17, 5)
    assert senses.perceive(gob, hero, dun) is None
    wolf = make('wolf_pack_leader', 17, 5)
    assert senses.perceive(wolf, hero, dun) == 'scent'


def test_scent_goes_through_stone_and_the_wolf_paths_round():
    dun = two_rooms()
    hero = Hero(7, 5)
    wolf = make('wolf_pack_leader', 13, 5)
    assert senses.perceive(wolf, hero, dun) == 'scent'
    start = senses.find_path(wolf, dun, (hero.x, hero.y))
    assert start, 'a path round the wall exists'
    for _ in range(40):
        if wolf._adjacent_to(hero):
            break
        wolf.take_turn(hero, dun, [wolf])
    assert wolf._adjacent_to(hero), 'it followed the corridor, not the wall'


def test_tremor_needs_the_hero_to_move():
    dun = two_rooms()
    hero = Hero(8, 5)
    cobra = make('cobra', 12, 5)
    senses.begin_turn(moved=False, guilty=False, floor=5)
    assert senses.perceive(cobra, hero, dun) is None
    senses.begin_turn(moved=True, guilty=False, floor=5)
    assert senses.perceive(cobra, hero, dun) == 'tremor'
    hero.status_effects['levitating'] = 5
    assert senses.perceive(cobra, hero, dun) is None


def test_the_furies_find_only_the_guilty():
    dun = two_rooms()
    hero = Hero(4, 5)
    fury = make('erinyes_lesser', 16, 5)
    assert senses.perceive(fury, hero, dun) is None
    senses.begin_turn(moved=True, guilty=True, floor=5)
    assert senses.perceive(fury, hero, dun) == 'guilt'


def test_asterion_is_master_of_his_house():
    dun = two_rooms()
    hero = Hero(2, 2)
    ast = make('asterion_minotaur', 18, 9)
    assert senses.perceive(ast, hero, dun) == 'master'


def test_footsteps_go_round_corners_not_through_stone():
    dun = two_rooms()
    m = sound = senses.sound_map(dun, 8, 5, 6)
    assert (12, 5) not in m, 'stone stops sound'
    assert sound[(8, 5)] == 0
    far = senses.sound_map(dun, 8, 5, 40)
    assert far[(12, 5)] > 4, 'the long way round'


def test_a_closed_door_muffles_sound():
    open_ = senses.sound_map(two_rooms(), 6, 12, 30)
    shut = senses.sound_map(two_rooms(door=True), 6, 12, 30)
    assert shut[(14, 12)] > open_[(14, 12)]


def test_a_heard_noise_gives_a_place_not_the_hero():
    dun = two_rooms()
    hero = Hero(7, 11)
    gob = make('goblin', 11, 11)          # four tiles of open ground from the fight
    gob.ai_pattern = 'aggressive'
    dun.tiles[11][11] = FLOOR
    dun.tiles[11][7] = FLOOR
    senses.emit(dun, 7, 12, 'melee')
    senses.resolve_noises(dun, [gob], hero, rng=random.Random(1))
    assert gob._heard[:2] == (7, 12)
    hero.x, hero.y = 2, 2                  # the hero moves off after the fight
    gob.take_turn(hero, dun, [gob])
    assert gob._goal == (7, 12)
    assert not gob._tracking


def test_a_lost_trail_is_searched_then_given_up():
    dun = two_rooms()
    hero = Hero(5, 5)
    gob = make('goblin', 6, 5)
    gob.take_turn(hero, dun, [gob])
    assert gob._tracking
    hero.x, hero.y = 15, 5                  # gone through the wall (a blink)
    for _ in range(60):
        gob.take_turn(hero, dun, [gob])
        if gob._goal is None:
            break
    assert gob._goal is None and not gob._tracking
    assert gob._lost_line


def test_a_sleeper_sleeps_through_silence_and_wakes_to_a_fight():
    dun = two_rooms()
    hero = Hero(3, 3)
    gob = make('goblin', 5, 5)
    gob.add_effect('sleeping', 500)
    for _ in range(10):
        gob.take_turn(hero, dun, [gob])
    assert gob.has_effect('sleeping')
    woke = False
    rng = random.Random(3)
    for _ in range(20):
        senses.emit(dun, 4, 4, 'melee')
        if senses.resolve_noises(dun, [gob], hero, rng=rng):
            woke = True
            break
    assert woke and not gob.has_effect('sleeping')


def test_an_alarm_rouses_to_the_place():
    import container_system
    gob = make('goblin', 15, 5)
    container_system.alert_monsters_near([gob], 14, 6, 10)
    assert gob._alerted and gob._goal == (14, 6)


def test_the_imp_no_longer_hunts_from_across_the_floor():
    dun = two_rooms()
    hero = Hero(2, 2)
    imp = make('imp', 18, 9)
    imp._job = 'guard'
    for _ in range(10):
        imp.take_turn(hero, dun, [imp])
    assert not imp._tracking
    assert (imp.x, imp.y) == (18, 9), 'a guard keeps its post'


def test_an_archer_keeps_its_distance():
    """Archers Find a Lane (AI-2, src/lanes.py): beside the hero an archer
    with somewhere to shoot from steps back every time (it was half the
    time), at most twice running: a hero who keeps after it gets it in melee."""
    dun = two_rooms()
    hero = Hero(5, 5)
    stepped = 0
    for seed in range(30):
        random.seed(seed)
        arc = make('goblin', 6, 5, ai_pattern='ranged',
                   attacks=[{'name': 'Shortbow', 'damage': '1d6', 'type': 'pierce',
                             'ranged': True}])
        arc._tracking = True
        arc.take_turn(hero, dun, [arc])
        if max(abs(arc.x - hero.x), abs(arc.y - hero.y)) == 2:
            stepped += 1
    assert stepped == 30, stepped


def test_a_den_sleeps():
    dun = two_rooms()
    mons = [make('goblin', 13, 3), make('goblin', 14, 3), make('goblin', 3, 3)]
    senses.assign_jobs(mons, dun.rooms, rng=random.Random(0), sleep_rooms=[dun.rooms[1]])
    assert mons[0].has_effect('sleeping') and mons[1].has_effect('sleeping')


def test_observe_lines():
    gob = make('goblin', 5, 5)
    # In the creature's own pronoun (round 3): a goblin is "he".
    assert senses.status_line(gob) == "He hasn't noticed you."
    gob.add_effect('sleeping', 10)
    assert senses.status_line(gob) == 'He is asleep.'
    rat = make('giant_rat', 5, 5)
    assert senses.status_line(rat) == "It hasn't noticed you."
    wolf = make('wolf_pack_leader', 5, 5)
    assert 'scent' in senses.senses_line(wolf)


def test_senses_data_names_real_monsters_and_senses():
    d = senses.data()
    mons = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    known = set(d['senses'])
    for kind, ss in d['monsters'].items():
        assert kind in mons or kind == 'death', kind
        for s in ss:
            assert s in known, (kind, s)
    for fam, ss in d['families'].items():
        for s in ss:
            assert s in known, (fam, s)
    for kind in d.get('monster_ranges', {}):
        assert kind in mons, kind
    fams = {m.get('family') for m in mons.values()}
    for fam in d['jobs']:
        if fam.startswith('_') or fam in ('default', 'sleep_turns'):
            continue
        assert fam in fams, fam


def test_no_old_through_the_walls_detection_left():
    src = open(os.path.join(ROOT, 'src', 'monster.py'), encoding='utf-8').read()
    assert 'dist_to_player <= detection_range' not in src
    assert '<= 10\n                    or player.has_effect' not in src


def test_a_lore_sense_says_itself_once_a_floor():
    dun = two_rooms()
    hero = Hero(7, 5)
    wolf = make('wolf_pack_leader', 13, 5)
    wolf.take_turn(hero, dun, [wolf])
    assert wolf._sense_how == 'scent'
    wolf._sense_how = ''
    wolf._tracking = False
    wolf.take_turn(hero, dun, [wolf])
    assert not wolf._sense_how, 'said once a floor per kind'


class _SenseGame:
    """Just enough of a Game to say a sense line."""
    from game_combat import CombatMixin
    _say_sense_lines = CombatMixin._say_sense_lines

    def __init__(self, hero, sees):
        self.player = hero
        self._sees = sees
        self.msgs = []

    def _sees_monster(self, m):
        return self._sees

    def add_message(self, text, cat='info'):
        self.msgs.append(text)


def _knower(*studied):
    from types import SimpleNamespace
    return SimpleNamespace(studied_monster_ids=set(studied), lore_known_monster_ids=set(),
                           family_lore_grants={})


def test_a_sense_never_names_a_creature_the_hero_cannot_see():
    """2026-11-12: "The wight has felt the warmth of the living" from behind a
    wall named a creature he had never seen. Unseen, it is "something"."""
    for how in ('scent', 'tremor', 'lifesense', 'echo', 'mindsense', 'guilt'):
        assert '{' not in senses.sense_line(how, 'unseen'), how
        assert senses.sense_line(how, 'known') and senses.sense_line(how, 'seen'), how
    wolf = make('wolf_pack_leader', 13, 5)
    g = _SenseGame(_knower('wolf_pack_leader'), sees=False)
    wolf._sense_how = 'scent'
    g._say_sense_lines(wolf)
    assert g.msgs and 'wolf' not in g.msgs[0].lower() and 'something' in g.msgs[0].lower()


def test_a_seen_unknown_creature_shows_what_it_does_and_a_known_one_explains():
    wolf = make('wolf_pack_leader', 13, 5)
    g = _SenseGame(_knower(), sees=True)
    wolf._sense_how = 'scent'
    g._say_sense_lines(wolf)
    assert 'sniffs the air' in g.msgs[0] and 'scent' not in g.msgs[0]
    g = _SenseGame(_knower('wolf_pack_leader'), sees=True)
    wolf._sense_how = 'scent'
    g._say_sense_lines(wolf)
    assert 'It has your scent' in g.msgs[0]
    assert not wolf.__dict__.get('_sense_how'), 'said once'


def test_g7_an_archer_that_can_blink_steps_out_to_a_clear_shot():
    w, h = 30, 20
    tiles = [[FLOOR] * w for _ in range(h)]
    for x in range(w):
        tiles[0][x] = tiles[h - 1][x] = WALL
    for y in range(h):
        tiles[y][0] = tiles[y][w - 1] = WALL
    dun = Dungeon(tiles, [Room(0, 0, w, h)], w, h, 55)
    hero = Hero(15, 10)
    arc = make('shadow_archer', 16, 10)
    arc.phase_blink_chance = 1.0
    arc._tracking = True
    arc.take_turn(hero, dun, [arc])
    assert max(abs(arc.x - hero.x), abs(arc.y - hero.y)) in (4, 2), (arc.x, arc.y)


def test_g7_asterion_lowers_his_horns_before_his_rage():
    dun = two_rooms()
    hero = Hero(12, 5)
    ast = make('asterion_minotaur', 16, 5)
    ast._hit_run_state = 'hunting'
    ast.take_turn(hero, dun, [ast])
    assert ast._charge_ready


def test_c3_a_ghoul_goes_to_a_corpse_and_eats_it():
    from items import Corpse
    import game_combat
    dun = two_rooms()
    hero = Hero(2, 2)
    ghoul = make('ghoul', 15, 5)
    ghoul._job = 'guard'
    ghoul._home = (15, 5)
    body = Corpse('Goblin', 'goblin', 17, 5)

    class G(game_combat.CombatMixin):
        def __init__(self):
            self.ground_items = [body]
            self.msgs = []

        def add_message(self, t, k='info'):
            self.msgs.append(t)

        def _sees_monster(self, m):
            return True

        def _display_name(self, it):
            return 'goblin corpse'
    g = G()
    assert senses.is_scavenger(ghoul)
    for _ in range(12):
        g._scavenge_prep(ghoul)
        ghoul.take_turn(hero, dun, [ghoul])
        g._scavenge_after(ghoul)
        if body not in g.ground_items:
            break
    assert body not in g.ground_items, 'the corpse is eaten'
    assert any('feeding' in m for m in g.msgs)
