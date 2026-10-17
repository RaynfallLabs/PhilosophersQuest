"""Sherlock and Irene (2026-10-17): the family's two Sphynx cats, rare Soul
Sphere hatches. Each cat is a 5% chance per hatch (until met this run); the
four elemental lines share the rest evenly.

Logic tests on the pet tables and on a real headless Game. A 5% hatch is not
something a short play-test reaches, so the roll, the hatch, the specials and
the save are pinned here; how the cats LOOK and feel in play is Brandon's call.
"""
import os
import random
import struct
import sys
from collections import Counter

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import pet_system  # noqa: E402
from pet_system import (FAMILY_CAT_CHANCE, FAMILY_CATS, Pet, _SPECIES,  # noqa: E402
                        _EVOLVE_1, _EVOLVE_2, roll_family_cat,
                        roll_soul_sphere_species, random_species)

ELEMENTAL = ('electric', 'water', 'plant', 'fire')
STAGE_NAMES = {
    'sherlock': ['Sherlock', 'Sherlock the Stout', 'Sherlock the Immovable'],
    'irene': ['Irene', 'Irene the Skyleaper', 'Irene the Seraph'],
}

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(name='__test_family_cats__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(7)
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    g.visible = {(x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)}
    return g


class _FixedRng:
    def __init__(self, value):
        self.value = value

    def random(self):
        return self.value


def _free_tiles_near(g, n=1, exclude=()):
    px, py = g.player.x, g.player.y
    out = []
    for r in range(1, 8):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                x, y = px + dx, py + dy
                if (max(abs(dx), abs(dy)) == r and g.dungeon.is_walkable(x, y)
                        and (x, y) not in exclude and (x, y) not in out):
                    out.append((x, y))
                    if len(out) >= n:
                        return out
    return out


def _sphere(g, sid='soul_sphere'):
    from items import make_item_by_id
    s = make_item_by_id('artifact', sid)
    g.player.inventory.append(s)
    return s


# ---------------------------------------------------------------- the roll

def test_each_cat_is_five_percent_and_the_lines_share_the_rest():
    rng = random.Random(20261017)
    n = 200_000
    seen = Counter()
    state = random.getstate()
    for _ in range(n):
        seen[roll_family_cat((), rng) or 'normal'] += 1
    assert random.getstate() == state          # the global stream never moves
    assert FAMILY_CAT_CHANCE == 0.05
    for cat in FAMILY_CATS:
        assert abs(seen[cat] / n - 0.05) < 0.003, (cat, seen[cat] / n)
    assert abs(seen['normal'] / n - 0.90) < 0.004

    # the whole hatch, with Shep (test_shep.py) still to meet:
    # Shep 1%, each cat still 5%, 22.25% x 4
    random.seed(11)
    shep_rng = random.Random(3)
    whole = Counter(roll_soul_sphere_species((), rng, shep_rng) for _ in range(n))
    for cat in FAMILY_CATS:
        assert abs(whole[cat] / n - 0.05) < 0.003, (cat, whole[cat] / n)
    for line in ELEMENTAL:
        assert abs(whole[line] / n - 0.2225) < 0.006, (line, whole[line] / n)
    assert set(whole) == set(ELEMENTAL) | set(FAMILY_CATS) | {'shep'}


def test_a_cat_already_met_gives_its_share_back_to_the_normal_roll():
    rng = random.Random(5)
    n = 100_000
    one = Counter(roll_family_cat({'sherlock'}, rng) or 'normal' for _ in range(n))
    assert one['sherlock'] == 0
    assert abs(one['irene'] / n - 0.05) < 0.003
    assert abs(one['normal'] / n - 0.95) < 0.004
    both = Counter(roll_soul_sphere_species({'sherlock', 'irene', 'shep'}, rng) for _ in range(20_000))
    assert set(both) == set(ELEMENTAL)


def test_the_ordinary_pool_never_holds_a_cat():
    random.seed(1)
    assert {random_species() for _ in range(2000)} == set(ELEMENTAL)


# ---------------------------------------------------------------- hatching on a real Game

def test_a_soul_sphere_hatches_each_cat_with_its_name_ready(monkeypatch):
    from game_states import STATE_PET_NAME_INPUT, STATE_PLAYER
    g = _game()
    (tx, ty), = _free_tiles_near(g)
    monkeypatch.setattr(pet_system, '_SHEP_RNG', _FixedRng(0.99))   # not Shep's 1%
    monkeypatch.setattr(pet_system, '_CAT_RNG', _FixedRng(0.01))    # Sherlock's 5%
    g._throw_soul_sphere(_sphere(g), None, tx, ty)
    cat = g.pets[-1]
    assert cat.species_key == 'sherlock' and cat.name == 'Sherlock'
    assert g.state == STATE_PET_NAME_INPUT
    assert g._pet_name_input_buffer == 'Sherlock'
    assert g.player.family_cats_met == {'sherlock'}
    assert any('Sherlock' in str(e[0]) and 'yawns' in str(e[0]) for e in g.msg_log.entries[-3:])
    g._pet_name_input(pygame.K_RETURN, '')                 # keep the default
    assert cat.nickname == '' and cat.name == 'Sherlock' and g.state == STATE_PLAYER

    # The same roll again: Sherlock is met, so his share goes to the ordinary lines.
    (tx, ty), = _free_tiles_near(g, exclude={(cat.x, cat.y)})
    g._throw_soul_sphere(_sphere(g), None, tx, ty)
    assert g.pets[-1].species_key in ELEMENTAL
    g._pet_name_input(pygame.K_ESCAPE, '')

    monkeypatch.setattr(pet_system, '_CAT_RNG', _FixedRng(0.07))    # Irene's 5%
    taken = {(p.x, p.y) for p in g.pets}
    (tx, ty), = _free_tiles_near(g, exclude=taken)
    g._throw_soul_sphere(_sphere(g), None, tx, ty)
    assert g.pets[-1].species_key == 'irene'
    assert g._pet_name_input_buffer == 'Irene'
    assert g.player.family_cats_met == {'sherlock', 'irene'}


def test_the_unusual_soul_sphere_can_hatch_a_cat_instead_of_dad(monkeypatch):
    g = _game()
    g.dungeon_level = 2
    (tx, ty), = _free_tiles_near(g)
    monkeypatch.setattr(pet_system, '_SHEP_RNG', _FixedRng(0.99))   # not Shep's 1%
    monkeypatch.setattr(pet_system, '_CAT_RNG', _FixedRng(0.06))
    g._throw_unusual_sphere(_sphere(g, 'unusual_soul_sphere'), None, tx, ty)
    assert [p.species_key for p in g.pets] == ['irene']

    monkeypatch.setattr(pet_system, '_CAT_RNG', _FixedRng(0.50))    # no cat: Dad as ever
    g2 = _game()
    g2.dungeon_level = 2
    (tx, ty), = _free_tiles_near(g2)
    g2._throw_unusual_sphere(_sphere(g2, 'unusual_soul_sphere'), None, tx, ty)
    assert getattr(g2.pets[-1], 'is_dad', False)


def test_a_cat_in_a_bound_sphere_counts_as_met():
    s = type('S', (), {})()
    s.bound_pet = Pet('irene')
    assert pet_system.family_cats_present(None, [], [s]) == {'irene'}
    assert pet_system.family_cats_present(None, [Pet('sherlock')], []) == {'sherlock'}


# ---------------------------------------------------------------- growing up

@pytest.mark.parametrize('key', FAMILY_CATS)
def test_each_cat_levels_and_evolves_through_all_three_stages(key):
    pet = Pet(key)
    assert pet.species_name == STAGE_NAMES[key][0]
    assert pet.available_specials() == []
    msgs = []
    while pet.level < _EVOLVE_2:
        msgs += pet.gain_xp(500)
    assert pet.stage == 2
    assert pet.species_name == STAGE_NAMES[key][2]
    for stage in (1, 2):                       # each evolution announced once, in its own words
        want = _SPECIES[key]['stages'][stage]['msg'].format(old=STAGE_NAMES[key][stage - 1])
        assert msgs.count(want) == 1, (want, msgs)
    assert {s['unlock_stage'] for s in pet.available_specials()} == {1, 2}
    # every stage keeps the cat's own name
    assert all(n.startswith(key.capitalize()) for n in STAGE_NAMES[key])
    assert [s['name'] for s in _SPECIES[key]['stages']] == STAGE_NAMES[key]


def test_a_nicknamed_cat_still_evolves_by_its_own_name():
    pet = Pet('irene')
    pet.nickname = 'Bean'
    assert pet.name == 'Bean, Irene'
    msgs = pet.gain_xp(20 * sum(range(1, _EVOLVE_1)))
    assert pet.stage == 1 and pet.name == 'Bean, Irene the Skyleaper'
    assert 'Bean, Irene, grows grander: now Irene the Skyleaper!' in msgs


# ---------------------------------------------------------------- power in line

def test_cats_are_as_strong_as_the_other_lines_and_no_stronger():
    for level in (1, 25, 55, 90):
        ref = Pet('electric')
        ref.level = level
        ref._refresh_stats()
        for key in FAMILY_CATS:
            cat = Pet(key)
            cat.level = level
            cat._refresh_stats()
            assert (cat.max_hp, cat.base_damage) == (ref.max_hp, ref.base_damage)
    for stage in (1, 2):
        others = [s for k in ELEMENTAL for s in _SPECIES[k]['specials'] if s['unlock_stage'] == stage]
        lo = min(s['damage_mult'] for s in others)
        hi = max(s['damage_mult'] for s in others)
        cds = {s['cooldown'] for s in others}
        for key in FAMILY_CATS:
            (mine,) = [s for s in _SPECIES[key]['specials'] if s['unlock_stage'] == stage]
            assert lo <= mine['damage_mult'] <= hi, (key, mine['id'])
            assert mine['cooldown'] in cds, (key, mine['id'])
            assert mine.get('status_chance', 0) <= 0.75
            assert mine['targeting'] in ('single', 'aoe', 'line', 'cone')
            assert mine['desc']
            assert all(w[0].isupper() for w in mine['name'].split()), mine['name']   # Title Case


# ---------------------------------------------------------------- specials on a real Game

def _monster(x, y, hp=5000):
    import json
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = json.load(f)
    mid = next(k for k, v in mons.items() if isinstance(v, dict) and v.get('attacks')
               and not v.get('is_boss') and tuple(v.get('footprint') or (1, 1)) == (1, 1))
    m = Monster({**mons[mid], 'id': mid}, x, y)
    m.hp = m.max_hp = hp
    return m


def _grown(key, x, y):
    pet = Pet(key, x, y)
    pet.level = _EVOLVE_2
    pet._refresh_stats()
    pet.hp = pet.max_hp
    return pet


def _special(key, sid):
    return next(s for s in _SPECIES[key]['specials'] if s['id'] == sid)


def _open_spot(g, need=4):
    """A tile with clear floor `need` tiles out in a straight line east."""
    for y in range(2, g.dungeon.height - 2):
        for x in range(2, g.dungeon.width - need - 2):
            if all(g.dungeon.is_walkable(x + i, y + j) for i in range(-1, need + 1) for j in (-1, 0, 1)):
                return x, y
    raise AssertionError('no open floor')


def _clear_player(g, x, y):
    g.player.x, g.player.y = x, y - 1 if g.dungeon.is_walkable(x, y - 1) else y + 1


def test_belly_flop_squashes_adjacent_foes_then_naps():
    g = _game()
    x, y = _open_spot(g)
    _clear_player(g, x - 1, y)
    cat = _grown('sherlock', x, y)
    cat.hp = cat.max_hp // 2
    g.pets = [cat]
    m = _monster(x + 1, y)
    far = _monster(x + 3, y)
    g.monsters = [m, far]
    g._resolve_pet_special(cat, _special('sherlock', 'belly_flop'), x, y)
    assert m.hp == m.max_hp - int(cat.base_damage * 1.5)
    assert far.hp == far.max_hp
    assert cat.hp == cat.max_hp // 2 + int(cat.max_hp * 0.20)
    assert any('dropped turkey' in str(e[0]) for e in g.msg_log.entries[-4:])


def test_midnight_aria_draws_foes_in_then_yowls():
    g = _game()
    x, y = _open_spot(g)
    _clear_player(g, x - 1, y)
    cat = _grown('sherlock', x, y)
    g.pets = [cat]
    m = _monster(x + 4, y)
    g.monsters = [m]
    g._resolve_pet_special(cat, _special('sherlock', 'midnight_aria'), x, y)
    assert max(abs(m.x - x), abs(m.y - y)) == 1            # came over to make it stop
    assert m.hp == m.max_hp - int(cat.base_damage * 1.6)
    assert any('3 a.m.' in str(e[0]) for e in g.msg_log.entries[-4:])


def test_pounce_and_seraph_dive_carry_irene_to_her_prey():
    for sid, mult in (('pounce', 1.5), ('seraph_dive', 2.0)):
        g = _game()
        x, y = _open_spot(g)
        _clear_player(g, x - 1, y)
        cat = _grown('irene', x, y)
        g.pets = [cat]
        m = _monster(x + 4, y)
        g.monsters = [m]
        g._resolve_pet_special(cat, _special('irene', sid), m.x, m.y)
        assert max(abs(cat.x - m.x), abs(cat.y - m.y)) == 1, sid
        assert m.hp == m.max_hp - int(cat.base_damage * mult), sid


def test_the_player_can_trigger_a_cat_special_and_it_cools_down():
    g = _game()
    x, y = _open_spot(g)
    _clear_player(g, x - 1, y)
    cat = _grown('sherlock', x, y)
    g.pets = [cat]
    g.monsters = [_monster(x + 1, y)]
    g._begin_pet_special_targeting(cat, _special('sherlock', 'belly_flop'))
    g._confirm_pet_special_target()
    assert cat.special_cooldown('belly_flop') > 0


# ---------------------------------------------------------------- save and load

def test_a_cat_survives_save_and_load():
    from save_system import save_game, load_game, delete_save
    name = '__test_family_cat_save__'
    g = _game(name)
    cat = _grown('irene', g.player.x + 1, g.player.y)
    cat.nickname = ''
    g.pets = [cat]
    g.player.family_cats_met = {'irene'}
    try:
        assert save_game(g)
        state = load_game(name)
        g2 = _game(name)
        g2.load_state(state)
        (back,) = [p for p in g2.pets if p.species_key == 'irene']
        assert back.name == 'Irene the Seraph' and back.level == _EVOLVE_2
        assert {s['id'] for s in back.available_specials()} == {'pounce', 'seraph_dive'}
        assert g2.player.family_cats_met == {'irene'}
        assert g2._family_cats_present() == {'irene'}
    finally:
        delete_save(name)


# ---------------------------------------------------------------- art

def _png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    return struct.unpack('>II', head[16:24])


@pytest.mark.parametrize('key', FAMILY_CATS)
def test_every_stage_has_its_sprite(key):
    import renderer
    for stage in range(3):
        pet = Pet(key)
        pet.level = (1, _EVOLVE_1, _EVOLVE_2)[stage]
        mid = pet.species_name.lower().replace(' ', '_')    # as game_render looks it up
        path = os.path.join(renderer._SPRITE_DIR, mid + '.png')
        assert os.path.exists(path), mid
        assert _png_size(path) == (64, 64), mid
