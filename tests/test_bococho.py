# ruff: noqa: F811  (make_game is a pytest fixture, imported)
"""The Bococho (RARE_PETS_PLAN 3): the data, the camp's state machine,
Varro, the side floor, the pet, her saddlebags and riding.

The journey through the real keys is tests/test_bococho_journey.py; the
race's scoring is tests/test_race.py. The feel of the race and of riding
is Brandon's play-test.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

from test_bugbash_wb_e import (  # noqa: E402,F401  (make_game is a fixture)
    make_game, no_errors, open_floor, place_monster, reload, stand_beside)

with open(os.path.join(ROOT, 'data', 'bococho.json'), encoding='utf-8') as _f:
    DATA = json.load(_f)


def _strings(node, path=''):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            if not str(k).startswith('_'):
                yield from _strings(v, f'{path}.{k}')
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _strings(v, f'{path}[{i}]')


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

# The plural they, each about many birds or things (never one person or bird).
PLURAL_THEY = ('races them for bets', 'keeps them on short ropes', 'feeds them little',
               'their ribs show', 'every one of them runs', 'pull at their ropes',
               'then they trot off', 'stumbles through them', 'one by one they slip free',
               'not one of them looks back', 'works them hard', 'give them hope',
               'nothing between them', 'they cross the line side by side')


def test_the_data_is_in_the_house_voice_and_never_a_copy():
    for path, text in _strings(DATA):
        low = text.lower()
        for m in re.finditer(r'\b(they|them|their|themselves)\b', low):
            near = low[max(0, m.start() - 30):m.end() + 30]
            assert any(ok in near for ok in PLURAL_THEY), (path, near)
        for banned in ('wark', 'kweh', 'chocobo', 'kupo', 'gysahl', 'final fantasy'):
            assert banned not in low, (path, banned)
        assert not text.rstrip().endswith(('...', '…')), path
    assert DATA['young']['pronoun'] == 'she' and DATA['varro']['pronoun'] == 'he'
    assert 'whirrup' in ' '.join(DATA['fed'])              # her own call
    assert (DATA['first_floor'], DATA['last_floor']) == (51, 65)
    assert DATA['chance_per_run'] == 1.0                   # every run
    assert len(DATA['fed']) == DATA['feeds_needed'] == 2
    assert len(DATA['too_soon']) == DATA['feeds_needed']   # one line per stage


def test_sunroot_the_fixtures_and_the_species_are_in_the_data():
    with open(os.path.join(ROOT, 'data', 'items', 'ingredient.json'), encoding='utf-8') as f:
        ing = json.load(f)
    root = ing[DATA['food_id']]
    assert root['min_level'] <= DATA['first_floor']        # forage before the camp
    with open(os.path.join(ROOT, 'data', 'fixtures.json'), encoding='utf-8') as f:
        fx = json.load(f)['fixtures']
    for fid in ('race_tether_post', 'race_betting_board', 'race_finish_banner'):
        assert fid in fx and fx[fid]['look'], fid
    assert fx['race_tether_post']['blocks'] and not fx['race_finish_banner'].get('blocks')
    import pet_system
    sp = pet_system._SPECIES['bococho']
    assert [s['name'] for s in sp['stages']] == ['Bococho Chick', 'Bococho', 'Bococho Champion']
    assert sp['damage_type'] == 'crushing' and sp['pronoun'] == 'she' and sp['quest_only']
    charge = next(s for s in sp['specials'] if s['id'] == 'bococho_charge')
    assert charge['unlock_stage'] == 2 and charge['leap'] and charge['knockback'] == 1
    assert DATA['pet']['saddlebags_lb'] == 20


def test_she_is_never_a_spheres_hatch():
    import random
    import pet_system
    random.seed(3)
    assert 'bococho' not in {pet_system.random_species() for _ in range(400)}


def test_her_kicks_are_strong_and_she_starts_grown():
    import pet_system
    pet = pet_system.Pet('bococho', 0, 0, level=DATA['pet']['start_level'])
    assert pet.stage == 1 and pet.species_name == 'Bococho'
    bite = pet_system.growth('bite', pet.level)
    assert pet.base_damage == max(1, round(bite * DATA['pet']['species']['bite_mult']))
    assert pet_system.is_companion(pet)
    assert pet.pronouns()[0] == 'she'
    champ = pet_system.Pet('bococho', 0, 0, level=55)
    assert [s['id'] for s in champ.available_specials()] == ['bococho_charge']
    assert pet.available_specials() == []
    # her picture: her stage's own, or a stand-in until the art is installed
    import bococho_encounter as bc
    assert pet.sprite_id in ('bococho', bc.data()['sprites']['fallback']['bococho'])


# ---------------------------------------------------------------------------
# The camp
# ---------------------------------------------------------------------------

def _camp(make_game):
    """A Titivillus run with the camp set up beside him (QA Shift+G) on a
    quiet, open floor."""
    import bococho_encounter as bc
    g, h = make_game(build='titivillus', name='Titivillus')
    open_floor(g, g.player.x, g.player.y, 6)
    g.pets = []
    h.shift('G')
    assert any(bc.is_young(m) for m in g.monsters), h.said()
    g.monsters = [m for m in g.monsters if bc.role(m)]
    g.player_gold = 10_000
    h.said()
    return g, h


def _young(g):
    import bococho_encounter as bc
    return next(m for m in g.monsters if bc.is_young(m))


def _varro(g):
    import bococho_encounter as bc
    return next(m for m in g.monsters if bc.is_varro(m))


def _open(h, m):
    g = h.g
    stand_beside(g, m)
    h.move(m.x - g.player.x, m.y - g.player.y)
    if g._bc_phase == 'story':
        h.key(pygame.K_RETURN)


def _feed(h):
    _open(h, _young(h.g))
    h.key('1')
    text = h.g._bc_text
    h.key(pygame.K_RETURN)
    h.key('2')
    return text


def _roots(g, n=4):
    import bococho_encounter as bc
    from items import load_items, copy_at, grant_identified
    tpl = next(i for i in load_items('ingredient') if i.id == bc.data()['food_id'])
    r = copy_at(tpl, g.player.x, g.player.y)
    r.count = n
    grant_identified(g, r)
    g.player.inventory.append(r)


def test_the_qa_key_sets_the_camp_and_gives_sunroot(make_game):
    import bococho_encounter as bc
    import decor
    g, h = _camp(make_game)
    st = g._bococho_state()
    assert st['floor'] == g.dungeon_level and st['spawned']
    assert sum(1 for m in g.monsters if bc.is_bird(m)) == 2
    fx = list(decor.fixtures_of(g.dungeon).values())
    assert fx.count('race_tether_post') == 3 and 'race_betting_board' in fx
    roots = [i for i in g.player.inventory if i.id == 'sunroot']
    assert roots and roots[0].count == 2
    for m in g.monsters:                                   # never a letter: a picture that is there
        from paths import data_path
        assert os.path.exists(data_path('assets', 'tiles', 'monsters', m.sprite_id + '.png')), m.sprite_id
    h.shift('G')                                           # again: her trust, two more roots
    assert sum(i.count for i in g.player.inventory if i.id == 'sunroot') == 4
    assert bc.trusts(st)
    h.shift('G')                                           # once more: she joins (to try riding)
    assert st['outcome'] == 'adopted' and g.state == 'bococho'
    h.key(pygame.K_RETURN)
    assert g.state == 'pet_name_input'
    h.key(pygame.K_RETURN)
    assert any(getattr(p, 'species_key', '') == 'bococho' for p in g.pets)


def test_the_feeds_too_soon_and_waiting(make_game):
    import bococho_encounter as bc
    g, h = _camp(make_game)
    st = g._bococho_state()
    g.player.inventory = [i for i in g.player.inventory if i.id != 'sunroot']
    assert _feed(h).startswith('You hold out your')         # anything but Sunroot
    g.player.inventory = [i for i in g.player.inventory
                          if not hasattr(i, 'sp_restore') and i.id != 'sunroot']
    from items import Food, Ingredient
    g.player.inventory = [i for i in g.player.inventory if not isinstance(i, (Food, Ingredient))]
    assert _feed(h) == bc.data()['no_food']
    _roots(g)
    turn = g.turn_count
    assert _feed(h) == bc.data()['fed'][0]
    assert bc.feeds(st) == 1 and g.turn_count == turn + 1     # a feed is a turn
    # Too soon: the screen shows only the line, and no turn passes.
    _open(h, _young(g))
    assert g._bc_phase == 'outcome' and g._bc_text == bc.data()['too_soon'][0]
    turn = g.turn_count
    h.key(pygame.K_RETURN)
    assert g.state == 'player' and g.turn_count == turn and bc.feeds(st) == 1
    # Leaving the floor counts as waiting.
    g._bococho_left(st['floor'], st['floor'] + 1)
    assert not g._bococho_waiting('feed')
    assert _feed(h) == bc.data()['fed'][1] and bc.trusts(st)
    # Her screen says where her trust stands.
    assert g._bococho_waiting_text() == bc.data()['waiting'][2]
    assert _feed(h) == bc.data()['fed_again']               # trusted: no gap now
    no_errors(h)


def test_i_choose_you_refusals_say_what_is_missing(make_game):
    import bococho_encounter as bc
    g, h = _camp(make_game)
    st = g._bococho_state()
    _open(h, _young(g))
    h.key('3')
    assert g._bc_text == bc.data()['refused']
    h.key(pygame.K_RETURN)
    h.key('2')
    st['feeds'] = 1
    _open(h, _young(g))
    h.key('3')
    assert g._bc_text == bc.data()['refused_trust']
    h.key(pygame.K_RETURN)
    h.key('2')
    st['feeds'] = 2
    _open(h, _young(g))
    h.key('3')
    assert g._bc_text == bc.data()['refused_tethered']
    h.key(pygame.K_RETURN)
    h.key('2')
    st['won'] = True
    g._bococho_wait_from_now('choose')                     # a failed try a moment ago
    _open(h, _young(g))
    h.key('3')
    assert g._bc_text == bc.data()['refused_soon']
    h.key(pygame.K_RETURN)
    h.key('2')
    st['waits'] = {}
    _open(h, _young(g))
    h.key('3')
    assert h.in_quiz()
    h.quiz(0, 1)                                           # a wrong answer: she sidesteps
    assert g._bc_text == bc.data()['fail'] and g._bococho_waiting('choose')
    assert st['outcome'] is None


def test_varro_takes_the_bet_only_when_she_trusts_and_the_fee_is_there(make_game):
    import bococho_encounter as bc
    from boss_levels import UNDERWAY_RUN
    g, h = _camp(make_game)
    st = g._bococho_state()
    fee = bc.fee(st['floor'])
    assert fee == __import__('economy').share(st['floor'], DATA['race_fee_share'])
    _open(h, _varro(g))
    h.key('1')
    assert g._bc_text == bc.data()['challenge_untrusted']
    h.key(pygame.K_RETURN)
    h.key('2')
    st['feeds'] = 2
    g.player_gold = 0
    g.player.inventory = [i for i in g.player.inventory
                          if 'treasure' not in str(getattr(i, 'item_class', ''))]
    _open(h, _varro(g))
    h.key('1')
    if g._bc_text != bc.data()['challenge_poor'].format(fee=f'{fee:,}'):
        # (the QA hero's treasure covered it: that is paying too)
        assert g._bc_text.startswith('Varro takes your')
    else:
        h.key(pygame.K_RETURN)
        h.key('2')
        g.player_gold = fee + 7
        _open(h, _varro(g))
        h.key('1')
        assert g._bc_text.startswith('Varro takes your') and g.player_gold == 7
    h.key(pygame.K_RETURN)
    assert g.dungeon_level == UNDERWAY_RUN and g.state == 'race'
    no_errors(h)


def _to_the_race(h):
    import bococho_encounter as bc
    g = h.g
    g._bococho_state()['feeds'] = 2
    _open(h, _varro(g))
    h.key('1')
    assert g._bc_text.startswith('Varro takes your'), g._bc_text
    h.key(pygame.K_RETURN)
    assert g.state == 'race'
    return bc


def test_leaving_mid_race_forfeits_and_a_loss_waits(make_game):
    g, h = _camp(make_game)
    floor = g.dungeon_level
    bc = _to_the_race(h)
    h.key(pygame.K_ESCAPE)
    assert g._race_phase == 'forfeit_ask'
    h.key('n')
    assert g._race_phase == 'intro'
    h.key(pygame.K_ESCAPE)
    h.key('y')
    assert g.dungeon_level == floor and g.state == 'player'
    st = g._bococho_state()
    assert st['race'] is None and not st['won'] and st['races'] == 1
    assert g._bococho_waiting('race')                      # try again after the gap
    _open(h, _varro(g))
    assert g._bococho_waiting_text().startswith('Varro counts your gold again')
    h.key('1')
    assert g._bc_text == bc.data()['challenge_soon']
    h.key(pygame.K_RETURN)
    h.key('2')
    h.wait(26)
    gold = g.player_gold
    _to_the_race(h)                                        # the fee again
    assert g.player_gold == gold - bc.fee(floor)
    # Away by the gate stair: Varro's race too.
    g.state = 'player'
    ex = g.dungeon.race_exit
    g.player.x, g.player.y = ex
    h.key('.', uni='>')
    assert g.dungeon_level == floor and g._bococho_state()['race'] is None
    assert any('Varro grins and calls the race for Brassbeak' in t for t in h.said())
    no_errors(h)


def test_a_lost_race_is_lost_and_varro_gloats(make_game):
    g, h = _camp(make_game)
    floor = g.dungeon_level
    bc = _to_the_race(h)
    h.key(pygame.K_RETURN)
    for _ in range(5):
        h.key('2')
        h.quiz(0, 1)                                       # chain 0 every leg
        for _ in range(10):
            if g.state == 'race':
                break
            h.frame(0.2)
        h.key(pygame.K_RETURN)
    assert g.dungeon_level == floor
    said = ' '.join(h.said())
    assert 'Brassbeak wins by' in said and 'Better luck next time' in said
    assert not g._bococho_state()['won'] and any(bc.is_varro(m) for m in g.monsters)
    no_errors(h)


def test_striking_varro_ends_the_race_and_she_bolts(make_game):
    import bococho_encounter as bc
    import deeds
    g, h = _camp(make_game)
    st = g._bococho_state()
    karma = g.karma
    varro = _varro(g)
    _open(h, varro)
    h.key('3')
    assert g._bc_text.startswith(bc.data()['strike'])
    assert bc.data()['strike_bolts'] in g._bc_text
    h.key(pygame.K_RETURN)
    assert st['outcome'] == 'fled' and not any(bc.is_young(m) for m in g.monsters)
    assert varro._bococho_hostile and not varro.is_allied
    # He is a foe now: walking into him is an attack (the maths chain).
    stand_beside(g, varro)
    h.move(varro.x - g.player.x, varro.y - g.player.y)
    assert h.in_quiz() and 'MELEE' in g.quiz_title
    h.quiz(1, 1)
    # His fall: no karma, his birds run, a deed.
    varro.hp = 0
    varro.alive = False
    g._on_monster_killed(varro)
    assert g.karma == karma
    assert not any(bc.is_bird(m) and m.alive for m in g.monsters)
    assert deeds.has(g._deeds_reg(), 'slew.gilt_varro')
    assert st['varro'] == 'slain'


# ---------------------------------------------------------------------------
# The side floor
# ---------------------------------------------------------------------------

def test_the_underway_run_is_a_side_floor_with_its_oval():
    import boss_levels
    from boss_levels import UNDERWAY_RUN, is_side_floor
    import decor
    assert is_side_floor(UNDERWAY_RUN) and boss_levels.SIDE_FLOOR_NAMES[UNDERWAY_RUN]
    d, monsters, items = boss_levels.generate_boss_level(UNDERWAY_RUN)
    assert monsters == [] and items == []
    inside, outside = d.race_loops
    assert len(inside) > 100 and len(outside) > len(inside)
    assert all(d.is_walkable(*t) for t in inside + outside)
    # each ring is a loop: every tile beside the next
    for ring in (inside, outside):
        for a, b in zip(ring, ring[1:] + ring[:1]):
            assert max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= 1
    fx = list(decor.fixtures_of(d).values())
    assert 'race_finish_banner' in fx and 'race_betting_board' in fx
    from dungeon import STAIRS_DOWN
    ex = d.race_exit
    assert d.tiles[ex[1]][ex[0]] == STAIRS_DOWN
    # the paddock reaches the track
    from collections import deque
    seen, q = {tuple(ex)}, deque([tuple(ex)])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            t = (x + dx, y + dy)
            if t not in seen and d.is_walkable(*t):
                seen.add(t)
                q.append(t)
    assert set(inside) <= seen


# ---------------------------------------------------------------------------
# The pet: saddlebags and riding
# ---------------------------------------------------------------------------

def _with_bococho(make_game, level=25):
    from pet_system import Pet
    g, h = make_game(build='titivillus', name='Titivillus')
    p = g.player
    open_floor(g, p.x, p.y, 7)
    import decor
    for pos in list(decor.fixtures_of(g.dungeon)):
        decor.remove(g.dungeon, pos)
    g.dungeon.dark_rooms = set()
    g.dungeon.traps = {}
    g.monsters = []
    g.pets = []
    pet = Pet('bococho', p.x + 1, p.y, level=level)
    g.pets.append(pet)
    h.wait()
    h.said()
    return g, h, pet


def test_her_saddlebags_raise_every_load_line(make_game):
    g, h, pet = _with_bococho(make_game)
    p = g.player
    assert p.saddlebag_lb == 20
    with_bags = p.get_carry_limit()
    g.pets = []
    g._sync_saddlebags()
    without = p.get_carry_limit()
    assert with_bags == without + 20
    # A load Burdened on foot is only Heavy with her bags.
    g.pets = [pet]
    g._sync_saddlebags()
    lim = p.get_carry_limit()
    from items import Item
    rock = Item.__new__(Item)
    rock.__dict__.update({'id': 'test_rock', 'name': 'rock', 'weight': 0.0, 'count': 1})
    p.inventory.append(rock)
    rock.weight = max(0.0, without * p.BURDENED_SHARE + 1 - p.get_current_weight())
    assert p.load_tier() == 'heavy' and lim * p.HEAVY_SHARE < p.get_current_weight()
    g.pets = []
    g._sync_saddlebags()
    assert p.load_tier() == 'burdened'
    # Stored in her sphere, the bags go with her.
    g.pets = [pet]
    h.wait()
    g._companions_to_stasis()
    h.wait()
    assert p.saddlebag_lb == 0


def test_mounting_needs_her_beside_a_grown_bird_and_no_foe(make_game):
    import riding
    g, h, pet = _with_bococho(make_game)
    p = g.player
    pet.x, pet.y = p.x + 3, p.y
    h.shift('R')
    assert not p.riding and riding.refusal_line('far', pet.name) in h.said()
    pet.x, pet.y = p.x + 1, p.y
    m = place_monster(g, 'goblin', -2, 0)
    g._refresh_fov()
    h.shift('R')
    assert not p.riding and any(t.startswith('Not with') for t in h.said())
    g.monsters.remove(m)
    p.status_effects['confused'] = 5
    h.shift('R')
    assert not p.riding
    p.status_effects.pop('confused')
    chick = g.pets[0].__class__('bococho', p.x, p.y + 1, level=1)
    assert riding.mount_refusal(p, chick) == 'small'
    turn = g.turn_count
    h.shift('R')
    assert p.riding and pet.ridden and g.turn_count == turn + 1
    assert 'You swing up into' in ' '.join(h.said())
    h.shift('R')                                           # and down again
    assert not p.riding and not pet.ridden and (pet.x, pet.y) != (p.x, p.y)
    no_errors(h)


def _mount(h, pet):
    g = h.g
    pet.x, pet.y = g.player.x + 1, g.player.y
    h.shift('R')
    assert g.player.riding


def test_two_tiles_a_step_and_one_turn_for_the_world(make_game):
    g, h, pet = _with_bococho(make_game)
    _mount(h, pet)
    p = g.player
    calls = []
    real = g._advance_turn

    def _count(*a, **k):
        calls.append(1)
        return real(*a, **k)
    g._advance_turn = _count
    x = p.x
    h.key(pygame.K_LEFT)
    assert p.x == x - 2 and len(calls) == 1                # no free turns
    assert (pet.x, pet.y) == (p.x, p.y) and p.riding
    # Blocked at the second tile: one tile.
    from dungeon import WALL
    g.dungeon.tiles[p.y][p.x - 2] = WALL
    x = p.x
    h.key(pygame.K_LEFT)
    assert p.x == x - 1 and len(calls) == 2
    g._advance_turn = real
    no_errors(h)


def test_traps_on_either_tile_set_her_rider_down(make_game):
    g, h, pet = _with_bococho(make_game)
    p = g.player
    _mount(h, pet)
    g.player.immortal = True
    # On the second tile: it fires and he is thrown.
    g.dungeon.traps[(p.x - 2, p.y)] = {'type': 'alarm', 'message': 'A loud bell rings!',
                                       'damage': '0', 'revealed': False}
    p.PER = 0
    import random
    random.seed(1)
    x = p.x
    h.key(pygame.K_LEFT)
    said = ' '.join(h.said())
    assert p.x == x - 2 and not p.riding and 'tumble out of the saddle' in said
    # On the first tile: no second step.
    _mount(h, pet)
    g.dungeon.traps[(p.x - 1, p.y)] = {'type': 'alarm', 'message': 'A loud bell rings!',
                                       'damage': '0', 'revealed': False}
    x = p.x
    random.seed(1)
    h.key(pygame.K_LEFT)
    assert p.x == x - 1 and not p.riding
    no_errors(h)


def test_every_other_set_down(make_game):
    """A hazard, a quiz, the stairs (she follows), a status, the load, a
    blow, her being hurt, her sphere: each sets him down with its line."""
    import riding
    g, h, pet = _with_bococho(make_game)
    p = g.player
    lines = riding.data()['set_down']

    def check(reason):
        said = ' '.join(h.said())
        want = lines[reason].replace('{pet}', pet.name).split('{')[0]
        assert not p.riding and not pet.ridden and want in said, (reason, said)

    _mount(h, pet)
    g._hazard_hit_hero({'damage': '', 'hero': 'The floor cracks.'})
    check('hazard')
    _mount(h, pet)
    g.quiz_engine.start_quiz(mode='threshold', subject='animal', tier=1,
                             callback=lambda r: None, threshold=1)
    check('quiz')
    g.quiz_engine._end(False)
    g.state = 'player'
    _mount(h, pet)
    floor = g.dungeon_level
    g._change_level(floor + 1, enter_from_top=True, via='stairs')
    check('stairs')
    assert pet in g.pets and max(abs(pet.x - p.x), abs(pet.y - p.y)) <= 2   # she follows
    open_floor(g, p.x, p.y, 3)
    g.monsters = []
    g.dungeon.dark_rooms = set()
    _mount(h, pet)
    p.status_effects['stunned'] = 3
    h.wait()
    check('status')
    p.status_effects.pop('stunned', None)
    _mount(h, pet)
    g._blows_on_hero = g._hero_blows() + 1
    h.wait()
    check('blow')
    _mount(h, pet)
    pet.hp -= 3
    h.wait()
    check('hurt')
    pet.hp = pet.max_hp
    _mount(h, pet)
    from items import Item
    anvil = Item.__new__(Item)
    anvil.__dict__.update({'id': 'test_anvil', 'name': 'anvil', 'count': 1,
                           'weight': float(p.get_carry_limit() + 5)})
    p.inventory.append(anvil)
    h.wait()
    check('overloaded')
    p.inventory.remove(anvil)
    _mount(h, pet)
    g._companions_to_stasis()                              # the one-companion rule
    check('stored')
    assert pet not in g.pets and any(getattr(i, 'bound_pet', None) is pet for i in p.inventory)
    assert not pet.ridden
    no_errors(h)


def test_recall_and_her_special_set_him_down(make_game):
    g, h, pet = _with_bococho(make_game, level=55)
    _mount(h, pet)
    h.shift('P')
    h.key('s')                                             # her Charge: she runs on her own
    assert not g.player.riding and g.state == 'pet_specials'
    h.key(pygame.K_ESCAPE)
    h.key(pygame.K_ESCAPE)
    _mount(h, pet)
    h.shift('P')
    h.key('r')                                             # Recall: into her sphere
    assert not g.player.riding and pet not in g.pets
    no_errors(h)


def test_a_galloping_bird_is_loud():
    import senses
    import sleepers
    import riding

    class P:
        DEX = 10
        riding = False

        def has_effect(self, e):
            return False

        def load_tier(self):
            return ''

        def is_burdened(self):
            return False

        def is_heavy(self):
            return False

        boons_taken = {}
        armor_slots = []
    p = P()
    walk = senses.step_radius(p)
    f_walk = sleepers.factor(p, 'step')
    p.riding = True
    assert senses.step_radius(p) == walk + riding.data()['step_noise']
    assert sleepers.factor(p, 'step') == f_walk * riding.data()['sleeper_step_factor']


def test_old_saves_load_on_foot_and_without_the_camp():
    from player import Player
    import bococho_encounter as bc
    p = Player.__new__(Player)
    assert p.riding is False and p.saddlebag_lb == 0
    st = bc.old_save_state()
    assert st['floor'] is None and st['race'] is None


def test_the_effects_list_shows_riding(make_game, monkeypatch):
    import ui
    g, h, pet = _with_bococho(make_game)
    _mount(h, pet)
    seen = []
    real = ui.Sidebar._effect_chip

    def _chip(self, x, y, w, label, color, effect_id=None):
        seen.append(label)
        return real(self, x, y, w, label, color, effect_id)
    monkeypatch.setattr(ui.Sidebar, '_effect_chip', _chip)
    h.frame()
    assert 'Riding' in seen


def test_looking_at_the_camp_and_felling_varro_by_the_sword(make_game):
    """Observe on each of the camp's creatures, and Varro killed by blows
    (his corpse, the kill handler), break nothing."""
    import bococho_encounter as bc
    from test_bugbash_wb_e import blow
    g, h = _camp(make_game)
    h.shift('I')
    for m in list(g.monsters):
        stand_beside(g, m)
        g.target_cursor_x, g.target_cursor_y = m.x, m.y
        g._observe_targeting = True
        g._confirm_observe()
        assert h.said(), bc.role(m)
        g.state = 'player'
    varro = _varro(g)
    _open(h, varro)
    h.key('3')
    h.key(pygame.K_RETURN)
    varro.hp = 1
    stand_beside(g, varro)
    for _ in range(6):
        if not varro.alive:
            break
        blow(h, varro, 3)
    assert not varro.alive
    assert not any(bc.is_bird(m) for m in g.monsters)
    no_errors(h)


def test_the_camp_finds_room_on_every_floor_it_can_stand_on(make_game):
    """Every run has its camp: on each floor of 51-65 it may stand on (never
    a gate boss's), as the floor generator builds it, the game sets the
    camp up on first arrival."""
    import random
    import bococho_encounter as bc
    g, h = make_game(build='titivillus', name='Titivillus')
    for level in bc.candidate_floors():
        random.seed(level * 31)
        d, monsters, items = g.level_mgr.generate(level)
        g.dungeon, g.monsters, g.ground_items = d, monsters, items
        g.dungeon_level = level
        g.player.x, g.player.y = d.rooms[0].center
        g._bococho = dict(bc.old_save_state(), floor=level, seed=level)
        g._maybe_spawn_bococho(level)
        roles = sorted(bc.role(m) for m in g.monsters if bc.role(m))
        assert roles == ['bird', 'bird', 'varro', 'young'], (level, roles)
        assert g._bococho['spawned']
