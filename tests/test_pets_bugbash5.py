"""Bug bash 5 (2026-10-17), pets and escorts: behaviour tests on a real
headless Game for PET-01, 02, 05 to 14, CODE-13, JNL-12 and the occupancy
sites of INT-08 / INT-11 / ENG-05.

Most of these are rare (a 1% Shep, a bound sphere in a packed corridor, the
Black Knight's floor) or about who stands where, so they are proven here and
not by play-test.
"""
import os
import pickle
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, HERE)

import pygame  # noqa: E402

pygame.init()

from pet_system import Pet, _SPECIES, _EVOLVE_1, _EVOLVE_2  # noqa: E402
from test_shep import (_game, _messages, _monster, _shep, _special,  # noqa: E402
                       _open_room, _far_walkable)
import test_escort  # noqa: E402

WALL, FLOOR = 0, 1


def _pocket(g, tiles):
    """Wall the whole floor except `tiles`."""
    for y in range(g.dungeon.height):
        for x in range(g.dungeon.width):
            g.dungeon.tiles[y][x] = FLOOR if (x, y) in tiles else WALL


def _escort(g, x, y):
    g.monsters = []
    esc = test_escort._start(g)
    esc.x, esc.y = x, y
    return esc


def _chron(g):
    return ' | '.join(str(e.get('text', '')) for e in g._chronicle if isinstance(e, dict))


def _bound_sphere(g, pet):
    from items import make_item_by_id
    s = make_item_by_id('artifact', 'soul_sphere')
    s.bound_pet = pet
    g.player.inventory.append(s)
    return s


def _throw(g, item, tx, ty):
    g._open_throw_targeting(item)
    g.target_cursor_x, g.target_cursor_y = tx, ty
    g._confirm_throw_target()


# ------------------------------------------------------------ PET-01 / PET-11

def test_a_bound_sphere_with_no_room_comes_down_whole_and_keeps_its_pet():
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    _pocket(g, {(x, y), (x + 1, y)})          # one tile, and a monster on it
    g.monsters = [_monster(x + 1, y)]
    shep = _shep(0, 0)
    shep.nickname = 'Bandit'
    sphere = _bound_sphere(g, shep)
    _throw(g, sphere, x + 1, y)
    assert sphere not in g.player.inventory
    assert sphere in g.ground_items and sphere.bound_pet is shep
    assert g.dungeon.is_walkable(sphere.x, sphere.y)
    assert shep not in g.pets
    assert any('unbroken' in s for s in _messages(g, 4))


def test_a_throw_lands_on_the_last_open_tile_within_range():
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x - 4, y
    for i in range(1, 30):                    # a wall right after the room
        if g.dungeon.in_bounds(x + 5 + i, y):
            g.dungeon.tiles[y][x + 5 + i] = WALL
    g.dungeon.tiles[y][x + 5] = WALL
    g._throw_reach = 3
    assert g._clamp_throw_target(x - 4, y, x + 40, y) == (x - 1, y)      # range
    g._throw_reach = 20
    assert g._clamp_throw_target(x - 4, y, x + 40, y) == (x + 4, y)      # the wall


def test_a_sphere_aimed_into_rock_hatches_on_open_floor_in_range():
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    from items import make_item_by_id
    s = make_item_by_id('artifact', 'soul_sphere')
    g.player.inventory.append(s)
    _throw(g, s, 0, 0)                        # the map's corner: rock
    assert len(g.pets) == 1
    p = g.pets[0]
    assert g.dungeon.is_walkable(p.x, p.y)
    assert max(abs(p.x - x), abs(p.y - y)) <= g._throw_reach + 1


# ------------------------------------------------------------ PET-02 / CODE-13

def _growl_scene():
    g = _game()
    x, y = _open_room(g, half=4)
    g.player.x, g.player.y = x, y
    shep = _shep(x - 1, y)
    g.pets = [shep]
    g.visible = {(x, y)}
    return g, shep


def _growls(g):
    return [e for e in g.msg_log.entries if 'growls low' in str(e[0])]


def test_a_threat_seen_every_other_turn_is_one_growl():
    g, shep = _growl_scene()
    m = _monster(g.player.x + 3, g.player.y)
    g.monsters = [m]
    for t in range(20):
        g.visible = {(g.player.x, g.player.y)} | ({(m.x, m.y)} if t % 2 else set())
        g._do_pet_growl()
    assert len(_growls(g)) == 1


def test_a_threat_pacing_on_the_edge_of_his_range_is_one_growl():
    g, shep = _growl_scene()
    m = _monster(g.player.x, g.player.y)
    g.monsters = [m]
    for t in range(20):
        m.x = g.player.x + (5 if t % 2 == 0 else 6)       # stage-0 radius is 5
        g._do_pet_growl()
    assert len(_growls(g)) == 1


def test_a_threat_that_goes_well_away_and_comes_back_is_growled_at_again():
    g, shep = _growl_scene()
    for xx in range(g.player.x, g.player.x + 9):
        g.dungeon.tiles[g.player.y][xx] = FLOOR
    m = _monster(g.player.x + 3, g.player.y)
    g.monsters = [m]
    g._do_pet_growl()
    m.x = g.player.x + 8                     # radius 5 + 2 < 8
    g._do_pet_growl()
    m.x = g.player.x + 3
    g._do_pet_growl()
    assert len(_growls(g)) == 2


def test_his_growl_memory_lasts_through_a_save():
    g, shep = _growl_scene()
    m = _monster(g.player.x + 3, g.player.y)
    g.monsters = [m]
    g._do_pet_growl()
    shep2, m2 = pickle.loads(pickle.dumps((shep, m)))
    g.pets, g.monsters = [shep2], [m2]
    g._do_pet_growl()
    assert len(_growls(g)) == 1
    # a different creature, even one made later, is not taken for him
    g.monsters.append(_monster(g.player.x, g.player.y + 3))
    g._do_pet_growl()
    assert len(_growls(g)) == 2


# ------------------------------------------------------------ PET-05 / INT-08 / INT-11 / ENG-05

def test_a_following_pet_never_steps_onto_an_escort():
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    esc = _escort(g, x + 2, y)
    pet = Pet('fire', x + 3, y)
    g.pets = [pet]
    _pocket(g, {(x, y), (x + 1, y), (x + 2, y), (x + 3, y)})     # a corridor
    for _ in range(5):
        g._do_pet_turns()
        assert (pet.x, pet.y) != (esc.x, esc.y)


def test_a_floor_change_never_seats_a_pet_on_the_escort():
    """The arrival stair with both side tiles taken (two sleeping rats, as in
    integration r09): the escort takes the tile below, and the pet used to
    be put there too."""
    import json
    from escort_system import Escort
    from monster import Monster
    from dungeon import _find_stair_tiles
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        d = json.load(f)
    g = test_escort._game(level=3)
    esc = Escort({'id': 'wynn', 'name': 'Wynn', 'hp': 999, 'floors': 50, 'leash': 3},
                 g.player.x, g.player.y, floor=g.dungeon_level)
    g.escorts = [esc]
    g.pets = [Pet('fire', g.player.x + 1, g.player.y)]
    dun, mons, its = g.level_mgr.generate(2)
    (ux, uy), _down = _find_stair_tiles(dun.tiles, dun.width, dun.height)
    for sx in (-1, 1):
        dun.tiles[uy][ux + sx] = FLOOR
        r = Monster({**d['giant_rat'], 'id': 'giant_rat'}, ux + sx, uy)
        r.add_effect('sleeping', 99)
        mons.append(r)
    dun.tiles[uy + 1][ux] = FLOOR
    g.level_mgr.save(2, dun, mons, its)
    g._change_level(2, True, via='stairs')
    assert esc in g._escorts_here()
    assert all((p.x, p.y) != (esc.x, esc.y) for p in g.pets)


def _boxed(g, r=4):
    """The hero, one escort beside him, and rock all round them out to `r`
    tiles (the rest of the floor as it was)."""
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    esc = _escort(g, x + 1, y)
    for yy in range(y - r, y + r + 1):
        for xx in range(x - r, x + r + 1):
            if g.dungeon.in_bounds(xx, yy) and (xx, yy) not in ((x, y), (x + 1, y)):
                g.dungeon.tiles[yy][xx] = WALL
    g.pets = []
    return esc


def test_spawn_at_and_atreus_never_put_a_monster_on_the_escort_or_hero():
    g = _game()
    esc = _boxed(g)
    g._spawn_at(g.player.x, g.player.y)
    g._spawn_house_of_atreus(g.dungeon_level)
    assert g.monsters == []                  # nowhere free near him: nothing comes
    bodies = {(g.player.x, g.player.y), (esc.x, esc.y)}
    assert not any((m.x, m.y) in bodies for m in g.monsters)


def test_summon_guardian_and_gate_never_land_on_the_escort():
    g = _game()
    esc = _boxed(g)
    g._apply_spell_effect({'effect': 'summon_guardian', 'tier': 1})
    g._apply_spell_effect({'effect': 'gate', 'tier': 1})
    assert not any((p.x, p.y) == (esc.x, esc.y) for p in g.pets)


def test_hermes_step_never_lands_the_hero_on_the_escort():
    import hero_specials
    g = _game()
    esc = _boxed(g)
    before = (g.player.x, g.player.y)
    hero_specials._eff_teleport_self(g, {}, {'range': 3}, 0)
    assert (g.player.x, g.player.y) != (esc.x, esc.y)
    assert (g.player.x, g.player.y) == before


def test_teleport_away_never_drops_the_monster_on_the_escort():
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    esc = _escort(g, x + 2, y)
    m = _monster(x + 1, y)
    g.monsters = [m]
    _pocket(g, {(x, y), (x + 1, y), (x + 2, y)})
    g.visible = {(x, y), (x + 1, y), (x + 2, y)}
    g._apply_spell_effect({'effect': 'teleport_away_spell', 'tier': 1}, target=m)
    assert (m.x, m.y) != (esc.x, esc.y)


def test_knockback_never_pushes_a_monster_onto_an_escort():
    from combat import apply_knockback
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    esc = _escort(g, x + 2, y)
    m = _monster(x + 1, y)
    g.monsters = [m]
    apply_knockback(g.player, m, g.dungeon, g.monsters, occupied=g._occupants())
    assert (m.x, m.y) == (x + 1, y)


# ------------------------------------------------------------ PET-06

def _sure_hitter(x, y):
    from monster import Monster
    defn = {'id': 'fx_biter', 'name': 'Biter', 'symbol': 'b', 'color': [200, 0, 0], 'hp': 50,
            'ac': 0, 'thac0': -20, 'speed': 0, 'attacks': [{'damage': '1d2+9'}],
            'ai_pattern': 'sessile', 'resistances': [], 'weaknesses': [], 'min_level': 1}
    return Monster(defn, x, y)


def test_a_monster_beside_a_pet_and_an_escort_swipes_once_a_turn():
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x - 3, y
    esc = _escort(g, x + 1, y)
    pet = Pet('fire', x - 1, y)
    pet.command = 'stay'
    g.pets = [pet]
    g.monsters = [_sure_hitter(x, y)]
    php, ehp = pet.hp, esc.hp
    g._do_pet_turns()
    g._do_escort_turns()
    assert (php - pet.hp > 0) + (ehp - esc.hp > 0) == 1
    g.turn_count += 1                         # next turn: a swipe again
    php, ehp = pet.hp, esc.hp
    g._do_pet_turns()
    g._do_escort_turns()
    assert (php - pet.hp > 0) + (ehp - esc.hp > 0) == 1


# ------------------------------------------------------------ PET-07

def test_the_rescue_is_not_spent_on_a_sleeping_or_feared_foe():
    from test_shep import _rescue_scene
    for effect in ('sleeping', 'feared', 'paralyzed', 'charmed'):
        g, shep, foe = _rescue_scene()
        foe.status_effects[effect] = 50
        g._do_pet_turns()
        assert shep.rescue_ready(g.player.deepest_floor_reached), effect
        assert foe.hp == foe.max_hp and foe.status_effects.get(effect, 0) > 0, effect


# ------------------------------------------------------------ PET-08 / JNL-12

def test_a_named_family_cat_has_her_own_words():
    from game_states import STATE_PET_NAME_INPUT
    for species, own in (('sherlock', 'Sherlock'), ('irene', 'Irene')):
        g = _game()
        x, y = _open_room(g)
        g._hatch_sphere_pet(species, x + 1, y)
        assert g.state == STATE_PET_NAME_INPUT and g._naming_story
        g._pet_name_input_buffer = 'Bean'
        g._pet_name_input(pygame.K_RETURN, '')
        line = _chron(g)
        assert 'Bean' in line and f'the {own}' not in line
        g2 = _game()
        g2._hatch_sphere_pet(species, x + 1, y)
        g2._pet_name_input(pygame.K_ESCAPE, '')
        assert own in _chron(g2) and 'emerged' not in _chron(g2)


# ------------------------------------------------------------ PET-09

def test_a_pet_special_meets_resistances_and_weaknesses():
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x - 3, y
    pet = Pet('fire', x - 1, y)
    pet.level = _EVOLVE_1
    pet._refresh_stats()
    g.pets = [pet]
    hot = _monster(x, y)
    hot.resistances = ['fire']
    hot.weaknesses = []
    g.monsters = [hot]
    dealt = g._pet_hit(pet, hot, 2.0, damage_type='fire')
    assert dealt == int(int(pet.base_damage * 2.0) * 0.5)
    shep = _shep(x - 1, y, level=_EVOLVE_1)
    hide = _monster(x, y)
    hide.resistances = ['pierce']
    hide.weaknesses = []
    dealt = g._pet_hit(shep, hide, 1.7)            # his bite: piercing
    assert dealt == int(int(shep.base_damage * 1.7) * 0.5)


def test_water_jet_knocks_its_target_back_a_tile_but_not_into_rock():
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x - 3, y
    pet = Pet('water', x - 1, y)
    pet.level = _EVOLVE_1
    pet._refresh_stats()
    g.pets = [pet]
    m = _monster(x, y)
    g.monsters = [m]
    jet = next(s for s in _SPECIES['water']['specials'] if s['id'] == 'water_jet')
    g._resolve_pet_special(pet, jet, m.x, m.y)
    assert (m.x, m.y) == (x + 1, y)
    g.dungeon.tiles[y][x + 2] = WALL
    g._resolve_pet_special(pet, jet, m.x, m.y)
    assert (m.x, m.y) == (x + 1, y)


# ------------------------------------------------------------ PET-10

def test_sic_em_needs_a_tile_the_hero_can_see_and_no_rock_in_between():
    from game_states import STATE_PLAYER
    for case in ('unseen', 'rock'):
        g = _game()
        x, y = _open_room(g)
        g.player.x, g.player.y = x - 3, y - 3
        shep = _shep(x - 3, y, level=_EVOLVE_1)
        g.pets = [shep]
        m = _monster(x + 3, y)
        g.monsters = [m]
        if case == 'unseen':
            g.visible.discard((m.x, m.y))
        else:
            for yy in range(g.dungeon.height):
                g.dungeon.tiles[yy][x] = WALL
        g._pending_pet_special = _special('sic_em')
        g._pending_pet_special_pet = shep
        g.target_cursor_x, g.target_cursor_y = m.x, m.y
        g._confirm_pet_special_target()
        assert m.hp == m.max_hp, case
        assert not shep._special_cooldowns.get('sic_em'), case       # not spent
        assert g.state == STATE_PLAYER


# ------------------------------------------------------------ PET-12

def test_the_duck_hatches_beside_the_hero_not_on_him():
    from items import make_item_by_id
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    duck = make_item_by_id('armor', 'duck_of_doom')
    g.player.armor_slots[0] = duck
    g.player.quirk_progress = {}
    g._duck_of_doom_transform()
    assert len(g.pets) == 1
    assert (g.pets[0].x, g.pets[0].y) != (x, y)
    assert max(abs(g.pets[0].x - x), abs(g.pets[0].y - y)) == 1


# ------------------------------------------------------------ PET-13

def _knight(g):
    import test_black_knight as tbk
    k = tbk._on_his_floor(g)
    tbk._beside(g, k)
    return k


def test_a_draw_won_by_pets_alone_says_so_and_the_sword_is_his_only_once_taken():
    import black_knight as bk
    g = _game()
    k = _knight(g)
    shep = _shep(g.player.x, g.player.y, level=_EVOLVE_2)
    shep.x, shep.y = k.x, k.y           # (position only matters for the name)
    g.pets = [shep]
    for _ in range(5):                  # a limb a turn, all in the world's pass
        k.take_damage(10 ** 6)
        g._black_knight_tick(end=True)
    assert k.defeated
    log = _chron(g)
    assert 'Shep the Legend took the Black Knight apart one limb at a time' in log
    assert 'I have his sword' not in log and "Black Knight's sword" not in log
    sword = next(i for i in g.ground_items if getattr(i, 'id', '') == bk.data()['sword_id'])
    g._black_knight_sword_taken(sword)
    assert "I have the Black Knight's sword" in _chron(g)


def test_a_draw_the_hero_fought_is_his_own_line():
    import test_black_knight as tbk
    g = _game()
    k = _knight(g)
    for _ in range(5):
        tbk._hit(g, k)
    log = _chron(g)
    assert 'Fought the Black Knight to what he insists was a draw.' in log
    assert 'apart one limb at a time' not in log
    assert 'I have his sword' not in log


# ------------------------------------------------------------ PET-14

def test_the_emberpup_doc_no_longer_promises_karma_for_feeding():
    import emberpup_encounter
    doc = emberpup_encounter.__doc__
    assert '+1 karma' not in doc
    assert 'moves no karma' in doc
