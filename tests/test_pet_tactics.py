"""A companion fights beside the hero (3.6.1 play-test, 2026-11-22).

Brandon: "targeting seems off for the Pet... he just seems to soak damage when
I can't see an enemy... make sure they also take defensive maneuvers and cry
for help when their life is low".

The cause (pet_system.Pet.take_turn before this): the pet went for the
nearest foe within four tiles of ITSELF, through walls and into the dark,
walked round to it out of the hero's sight and fought there to the death; a
pet beside a foe always bit, whatever its health. Now (src/pet_tactics.py,
data/pet_tactics.json): it goes for a foe near the hero that he can see,
breaks off when caught out of his sight, falls back behind him when hurt and
losing (by its nature), comes back in when it can win, and cries for help
once a bout of danger.

Pure tests of the decision, a data test, and staged Games (a pet beside the
hero, a foe behind a wall, in the dark, a hurt pet, an unseen cry).
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import pet_tactics as pt  # noqa: E402

FIERCE = pt.rules()['natures']['fierce']
STEADY = pt.rules()['natures']['steady']
TIMID = pt.rules()['natures']['timid']
FEARLESS = pt.rules()['natures']['fearless']


def _foe(d_pet=1, d_hero=2, seen=True, hp=50, blow=4.0, route=0):
    return {'m': object(), 'd_pet': d_pet, 'd_hero': d_hero, 'seen': seen,
            'hp': hp, 'blow': blow, 'route': route}


def _choose(hp, foes, nat=FIERCE, cmd='return', with_hero=True, bite=6, max_hp=40, support=False):
    return pt.choose(hp=hp, max_hp=max_hp, bite=bite, nat=nat, cmd=cmd, support=support,
                     with_hero=with_hero, foes=foes)


# ---------------------------------------------------------------- the rule

def test_a_healthy_pet_bites_the_foe_beside_it():
    f = _foe()
    assert _choose(40, [f]) == ('attack', f)


def test_a_hurt_pet_that_is_losing_falls_back():
    tough = _foe(hp=400, blow=4)
    assert _choose(6, [tough])[0] == 'fall_back'


def test_a_hurt_pet_that_can_win_finishes_the_foe():
    dying = _foe(hp=5, blow=4)
    assert _choose(6, [dying]) == ('attack', dying)


def test_a_timid_pet_breaks_sooner_than_a_fierce_one():
    f = _foe(hp=400, blow=4)
    half = 20                                  # half its health
    assert _choose(half, [f], nat=FIERCE)[0] == 'attack'
    assert _choose(half, [f], nat=TIMID)[0] == 'fall_back'
    assert TIMID['break_below'] > STEADY['break_below'] > FIERCE['break_below'] > 0


def test_a_fearless_one_never_breaks():
    f = _foe(hp=400, blow=40)
    assert _choose(1, [f], nat=FEARLESS)[0] == 'attack'


def test_caught_out_of_the_heros_sight_it_comes_back_unless_it_can_finish_the_foe():
    tough = _foe(hp=400, d_hero=9)
    assert _choose(40, [tough], with_hero=False)[0] == 'regroup'
    dying = _foe(hp=3, d_hero=9)
    assert _choose(40, [dying], with_hero=False) == ('attack', dying)


def test_it_goes_only_for_a_foe_near_the_hero_that_he_can_see():
    seen = _foe(d_pet=3, d_hero=3, seen=True, route=2)
    assert _choose(40, [seen]) == ('engage', seen)
    dark = _foe(d_pet=3, d_hero=3, seen=False, route=2)
    assert _choose(40, [dark])[0] == 'follow'
    # near the pet but beyond the command's reach of the HERO
    far = _foe(d_pet=2, d_hero=pt.command('return')['reach'] + 1, seen=True, route=1)
    assert _choose(40, [far])[0] == 'follow'
    # in sight, but only by a long walk round (a wall between)
    round_ = _foe(d_pet=4, d_hero=4, seen=True, route=pt.command('return')['max_route'] + 1)
    assert _choose(40, [round_])[0] == 'follow'
    assert _choose(40, [_foe(d_pet=4, d_hero=4, seen=True, route=None)])[0] == 'follow'


def test_it_prefers_the_foe_at_the_heros_side():
    at_hero = _foe(d_pet=3, d_hero=1, route=2)
    nearer_pet = _foe(d_pet=2, d_hero=3, route=1)
    assert _choose(40, [nearer_pet, at_hero]) == ('engage', at_hero)


def test_out_of_the_fight_and_wary_it_goes_back_in_only_when_it_can_win():
    # Over its break share, under its rally share: it fights on if a foe is
    # beside it, but does not walk back into a fight it would lose.
    hp = int(40 * (FIERCE['break_below'] + FIERCE['rally_above']) / 2)
    tough = _foe(d_pet=3, d_hero=2, hp=400, route=2)
    assert _choose(hp, [tough])[0] == 'follow'
    worn = _foe(d_pet=3, d_hero=2, hp=5, route=2)
    assert _choose(hp, [worn]) == ('engage', worn)
    mended = int(40 * FIERCE['rally_above']) + 1
    assert _choose(mended, [tough]) == ('engage', tough)


def test_stay_holds_and_wander_hunts_unseen_near_the_hero():
    f = _foe(d_pet=3, d_hero=3, seen=False, route=2)
    assert _choose(40, [f], cmd='stay') == ('hold', None)
    assert _choose(40, [f], cmd='wander') == ('engage', f)
    beside = _foe()
    assert _choose(40, [beside], cmd='stay') == ('attack', beside)


def test_the_support_companion_keeps_by_the_hero_and_falls_back_when_hurt():
    f = _foe(d_pet=2, d_hero=2, route=1)
    assert _choose(40, [f], support=True)[0] == 'follow'
    assert _choose(4, [f], support=True, nat=TIMID)[0] == 'fall_back'


def test_losing_counts_the_bites_it_needs_against_the_blows_it_can_take():
    assert pt.losing(10, 5, 4, 10) is False          # 2 bites, stands 3 turns
    assert pt.losing(10, 5, 4, 20) is True           # 4 bites, stands 3
    assert pt.losing(10, 5, 4, 10, margin=1) is False
    assert pt.losing(10, 5, 4, 10, margin=2) is True
    assert pt.losing(10, 5, 0, 1000) is False        # nothing can hurt it


def test_the_fall_back_tile_is_the_one_the_foes_can_least_reach_or_see():
    cands = [
        {'x': 1, 'y': 0, 'beside': 1, 'seen_by': 0, 'far': 1, 'steps': 0},
        {'x': 0, 'y': 1, 'beside': 0, 'seen_by': 1, 'far': 3, 'steps': 1},
        {'x': 2, 'y': 1, 'beside': 0, 'seen_by': 0, 'far': 2, 'steps': 3},
        {'x': 3, 'y': 1, 'beside': 0, 'seen_by': 0, 'far': 2, 'steps': 2},
    ]
    best = pt.pick_fall_back(cands)
    assert (best['x'], best['y']) == (3, 1)          # unseen, unreached; fewer steps
    assert pt.pick_fall_back([]) is None


def test_the_cry_comes_once_a_bout_of_danger():
    nat = STEADY
    low = nat['cry_below'] - 0.05
    said, bout, calm = pt.cry_step(False, 0, low, True, nat)
    assert said and bout
    for _ in range(10):                              # still low, still in danger
        said, bout, calm = pt.cry_step(bout, calm, low, True, nat)
        assert not said and bout
    calm_turns = pt.rules()['cry']['calm_turns']
    for _ in range(calm_turns):                      # the fight is over
        said, bout, calm = pt.cry_step(bout, calm, low, False, nat)
    assert not bout
    said, bout, calm = pt.cry_step(bout, calm, low, True, nat)
    assert said                                      # a new fight: a new cry
    mended = nat['cry_below'] + pt.rules()['cry']['reset_gap'] + 0.01
    said, bout, calm = pt.cry_step(bout, calm, mended, True, nat)
    assert not bout
    assert pt.cry_step(False, 0, 0.01, True, FEARLESS)[0] is False
    assert pt.cry_step(False, 0, low, False, nat)[0] is False     # no foe near: no cry


def test_the_cry_line_is_a_cue_that_says_where_unseen():
    assert pt.cry_line('Ember', 'yelps', 'he', seen=True) == 'Ember yelps: he is hurt!'
    assert (pt.cry_line('Ember', 'yelps', 'he', seen=False, place=pt.place_word(False),
                        direction='north')
            == 'Ember yelps from the corridor to the north: he is hurt!')


# ---------------------------------------------------------------- the data

def test_every_companion_has_a_nature_and_a_voice_from_data():
    import pet_system
    from pet_system import Pet
    natures = pt.rules()['natures']
    for nat in natures.values():
        assert 0 <= nat['break_below'] <= nat['rally_above'] <= 1 or nat['break_below'] == 0
        assert 0 <= nat['cry_below'] <= 1
    for key in pet_system._SPECIES:
        pet = Pet(key)
        name = pt.nature_name(pet)
        assert name in natures, key
        assert pt.voice(pet) != pt.rules()['cry']['default_voice'], key
    for key, row in pt.rules()['species'].items():
        assert row['nature'] in natures, key
    assert pt.voice(Pet('fire')) == 'yelps'
    assert pt.nature_name(Pet('fire')) == 'fierce'
    assert pt.nature_name(Pet('electric')) == 'timid'
    # a quest companion's nature and voice live in her own data file
    assert pt.nature_name(Pet('mooble', level=20)) == 'timid' and pt.voice(Pet('mooble')) == 'squeaks'
    assert pt.voice(Pet('bococho', level=25)) == 'squawks'
    for cmd in ('return', 'stay', 'wander'):
        assert pt.command_label(cmd).startswith(cmd.title())


def test_a_grown_pet_has_its_grown_voice():
    from pet_system import Pet, _EVOLVE_2
    assert pt.voice(Pet('fire', level=_EVOLVE_2)) == 'roars'


# ---------------------------------------------------------------- in a Game

def _game():
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(5)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_pet_tactics__')
    g._autosave = lambda *a, **k: None
    g.monsters, g.pets, g.ground_items = [], [], []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    from dungeon import WALL
    d = g.dungeon
    for y in range(d.height):
        for x in range(d.width):
            d.tiles[y][x] = WALL
    d.rooms = []
    return g


def _carve(g, x0, y0, x1, y1):
    from dungeon import FLOOR
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            g.dungeon.tiles[y][x] = FLOOR


def _mon(kind, x, y, hp=None):
    import json
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = json.load(f)
    m = Monster({**mons[kind], 'id': kind}, x, y)
    if hp:
        m.hp = m.max_hp = hp
    return m


def _two_rooms(g):
    """Room A (the hero's) and room B, three tiles of rock between, joined
    by a U-shaped corridor below."""
    from dungeon import Room
    _carve(g, 2, 2, 10, 10)
    _carve(g, 14, 2, 22, 10)
    _carve(g, 6, 11, 6, 13)
    _carve(g, 18, 11, 18, 13)
    _carve(g, 6, 13, 18, 13)
    g.dungeon.rooms = [Room(1, 1, 11, 11), Room(13, 1, 11, 11)]


def _place(g, pet, *foes):
    pet.nickname = 'Ember'
    g.pets = [pet]
    g.monsters = list(foes)
    g._refresh_fov()


def _turns(g, n, each=None):
    for _ in range(n):
        g._advance_turn()
        g._refresh_fov()
        if each:
            each()


def _log(g):
    return [str(e[0]) for e in g.msg_log.entries]


def test_a_pet_never_goes_round_a_wall_for_a_foe_the_hero_cannot_see():
    from pet_system import Pet
    g = _game()
    _two_rooms(g)
    g.player.x, g.player.y = 9, 6
    pet = Pet('fire', 10, 6, level=6)
    gob = _mon('goblin', 14, 6)          # four tiles from the pet, through rock
    _place(g, pet, gob)
    seen = []
    _turns(g, 24, lambda: seen.append((pet.x, pet.y) in g.visible))
    assert all(seen), "the pet left the hero's sight"
    assert max(abs(pet.x - g.player.x), abs(pet.y - g.player.y)) <= 2


def test_a_pet_does_not_charge_into_the_dark():
    from pet_system import Pet
    g = _game()
    _carve(g, 2, 5, 30, 9)
    g.player.x, g.player.y = 5, 7
    pet = Pet('fire', 6, 7, level=6)
    gob = _mon('goblin', 10, 7)          # beyond the hero's light
    _place(g, pet, gob)
    assert (gob.x, gob.y) not in g.visible
    hp = gob.hp
    _turns(g, 12, lambda: None)
    assert (pet.x, pet.y) in g.visible
    if (gob.x, gob.y) not in g.visible:
        assert gob.hp == hp              # nothing bitten in the dark


def test_a_pet_caught_out_of_sight_comes_back_to_the_hero():
    from pet_system import Pet
    g = _game()
    _two_rooms(g)
    g.player.x, g.player.y = 8, 3
    pet = Pet('fire', 8, 13, level=6)    # in the corridor, out of his sight
    gob = _mon('goblin', 9, 13, hp=400)
    gob._aware = True
    _place(g, pet, gob)
    assert (pet.x, pet.y) not in g.visible
    bitten_unseen = []

    def watch():
        if (pet.x, pet.y) not in g.visible and gob.hp < 400:
            bitten_unseen.append(gob.hp)
    _turns(g, 12, watch)
    assert (pet.x, pet.y) in g.visible
    assert not bitten_unseen


def test_a_hurt_pet_falls_back_behind_the_hero_and_cries_once():
    from pet_system import Pet
    g = _game()
    _carve(g, 2, 2, 14, 10)
    g.player.x, g.player.y = 5, 6
    pet = Pet('fire', 8, 6, level=6)
    gob = _mon('goblin', 9, 6, hp=400)
    pet.hp = int(pet.max_hp * 0.2)
    _place(g, pet, gob)
    _turns(g, 10)
    hx, hy = g.player.x, g.player.y
    assert max(abs(pet.x - hx), abs(pet.y - hy)) <= 1, (pet.x, pet.y)
    from geom import chebyshev_distance
    assert chebyshev_distance(pet.x, pet.y, gob) > chebyshev_distance(hx, hy, gob)   # the hero between
    cries = [t for t in _log(g) if 'is hurt!' in t]
    assert cries == ['Ember yelps: it is hurt!']
    assert pet.alive


def test_an_unseen_pets_cry_says_where_it_came_from():
    from pet_system import Pet
    g = _game()
    _two_rooms(g)
    g.player.x, g.player.y = 8, 3
    pet = Pet('fire', 8, 13, level=6)
    pet.command = 'stay'
    pet.hp = int(pet.max_hp * 0.2)
    gob = _mon('goblin', 9, 13, hp=400)
    gob._aware = True
    _place(g, pet, gob)
    _turns(g, 2)
    assert 'Ember yelps from the corridor to the south: it is hurt!' in _log(g)


def test_a_cry_is_not_heard_through_wax():
    from pet_system import Pet
    g = _game()
    _two_rooms(g)
    g.player.x, g.player.y = 8, 3
    pet = Pet('fire', 8, 13, level=6)
    pet.command = 'stay'
    pet.hp = int(pet.max_hp * 0.2)
    gob = _mon('goblin', 9, 13, hp=400)
    gob._aware = True
    _place(g, pet, gob)
    import counters
    orig = counters.deafened
    counters.deafened = lambda player: True
    try:
        _turns(g, 2)
    finally:
        counters.deafened = orig
    assert not [t for t in _log(g) if 'is hurt!' in t]


def _swipe_scene(struck: bool):
    from pet_system import Pet
    g = _game()
    _carve(g, 2, 2, 14, 10)
    g.player.x, g.player.y = 3, 6
    pet = Pet('electric', 8, 6, level=10)
    sl = _mon('goblin', 9, 6)
    sl.attacks = [{'name': 'sling stone', 'damage': '1d2+5', 'type': 'physical', 'ranged': True}]
    _place(g, pet, sl)
    g.visible = {(x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)}
    if struck:
        sl._struck_hero_turn = g.turn_count
    before = pet.hp
    g._monster_swipes(g.pets)
    return before - pet.hp, g


def test_a_slinger_that_shot_the_hero_this_turn_only_clips_the_pet_beside_it():
    whole, _ = _swipe_scene(False)
    clip, g = _swipe_scene(True)
    assert whole in (6, 7) and clip == 3        # a whole sling stone, then half of one
    assert any('clips Ember the Zappik' in t for t in _log(g))


def test_a_foe_in_the_dark_that_strikes_a_pet_in_the_light_is_something():
    from pet_system import Pet
    g = _game()
    _carve(g, 2, 2, 14, 10)
    g.player.x, g.player.y = 3, 6
    pet = Pet('electric', 8, 6, level=10)
    gob = _mon('goblin', 9, 6)
    _place(g, pet, gob)
    g.visible = {(pet.x, pet.y), (g.player.x, g.player.y)}
    g._monster_swipes(g.pets)
    hits = [t for t in _log(g) if 'Ember the Zappik.' in t]
    assert hits and all(t.startswith('Something ') for t in hits), hits


def test_the_pet_card_says_its_nature():
    from pet_system import Pet
    g = _game()
    lines = g._pet_nature_lines(Pet('fire'))
    assert lines and lines[0][0] == FIERCE['card']
