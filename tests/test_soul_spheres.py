"""The six Soul Spheres (2026-10-18, Brandon's design).

THE SPHERE DECIDES WHAT IS INSIDE, NEVER THE FLOOR:

    Soul Sphere            a newborn, level 1 (stage 0)
    Greater Soul Sphere    at its first evolution, level 25 (stage 1)
    Master Sphere          at its final evolution, level 55 (stage 2)
    Hearth Sphere          always one of the family, level 1
    Greater Hearth Sphere  always one of the family, level 25
    Master Hearth Sphere   always one of the family, level 55

Ordinary spheres keep the rare family chance (Shep 1%, each cat 5%, a met
one's share back to the elemental lines). A Hearth Sphere holds Sherlock 40%,
Irene 40%, Shep 20% among those not yet met, and an elemental line at its
tier once all three are met. The old late-pickup grant (floor x 50 XP) is
gone. Which sphere turns up depends on the floor band, like any loot.

Dad is untouched: he comes only from the Unusual Soul Sphere, which is not
one of the six and is never sold, spawned or hinted at.

Randomised loot and deep floors are out of reach of a play-test, so the
rolls, the hatches, the spawns, the shops and the saves are pinned here on a
real headless Game.
"""
import hashlib
import json
import os
import pickle
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
from pet_system import (FAMILY_CATS, FAMILY_PETS, SHEP, Pet, _EVOLVE_1,  # noqa: E402
                        _EVOLVE_2, _SPECIES, growth, hatch_level, is_soul_sphere,
                        roll_family_sphere_pet, roll_sphere_species, sphere_chances,
                        sphere_for_floor, sphere_spec, spheres)

ELEMENTAL = ('electric', 'water', 'plant', 'fire')
PLAIN = ('soul_sphere', 'greater_soul_sphere', 'master_sphere')
HEARTH = ('hearth_sphere', 'greater_hearth_sphere', 'master_hearth_sphere')
SIX = PLAIN + HEARTH
LEVELS = (1, _EVOLVE_1, _EVOLVE_2)
NAMES = {'soul_sphere': 'Soul Sphere', 'greater_soul_sphere': 'Greater Soul Sphere',
         'master_sphere': 'Master Sphere', 'hearth_sphere': 'Hearth Sphere',
         'greater_hearth_sphere': 'Greater Hearth Sphere',
         'master_hearth_sphere': 'Master Hearth Sphere'}

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(name='__test_spheres__', build=None):
    from main import Game
    from game_states import STATE_PLAYER
    import items
    items.bind_unique_registry(set())
    random.seed(7)
    if isinstance(build, str):
        from welcome_screen import SECRET_BUILDS
        name, build = build, SECRET_BUILDS[build]
    g = Game(_screen(), player_name=name, secret_build=build)
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


def _no_rare(monkeypatch):
    """The ordinary spheres' rare rolls all miss: an elemental line hatches."""
    monkeypatch.setattr(pet_system, '_SHEP_RNG', _FixedRng(0.99))
    monkeypatch.setattr(pet_system, '_CAT_RNG', _FixedRng(0.99))


def _sphere(g, sid):
    from items import make_item_by_id
    s = make_item_by_id('artifact', sid)
    assert s is not None, sid
    g.player.inventory.append(s)
    return s


def _free_tile(g, exclude=()):
    px, py = g.player.x, g.player.y
    taken = set(exclude) | {(p.x, p.y) for p in g.pets}
    for r in range(1, 9):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                x, y = px + dx, py + dy
                if (max(abs(dx), abs(dy)) == r and g.dungeon.is_walkable(x, y)
                        and (x, y) not in taken):
                    return x, y
    raise AssertionError('no free floor')


def _throw(g, sid):
    s = _sphere(g, sid)
    tx, ty = _free_tile(g)
    g._throw_soul_sphere(s, None, tx, ty)
    return g.pets[-1]


def _messages(g, n=6):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


# ---------------------------------------------------------------- the data

def test_the_six_spheres_and_what_each_holds():
    table = spheres()
    assert tuple(table) == SIX                      # file order is the roll order
    for i, sid in enumerate(PLAIN):
        assert table[sid] == {**table[sid], 'tier': i + 1, 'hatch_level': LEVELS[i], 'family': False}
    for i, sid in enumerate(HEARTH):
        assert table[sid] == {**table[sid], 'tier': i + 1, 'hatch_level': LEVELS[i], 'family': True}
    assert 'unusual_soul_sphere' not in table       # Dad's sphere is not one of the six
    assert not is_soul_sphere('unusual_soul_sphere')


def test_every_sphere_has_a_name_a_look_a_weight_and_lore():
    from items import make_item_by_id
    from naming import proper_name
    seen_unknown = set()
    for sid in SIX:
        it = make_item_by_id('artifact', sid)
        assert it.name == NAMES[sid] == proper_name(NAMES[sid])
        assert it.item_class == 'artifact' and it.weight == 0.5
        assert it.id_level == 0 and not it.identified       # like today's soul_sphere
        assert it.unidentified_name and 'sphere' in it.unidentified_name.lower()
        assert it.unidentified_name != it.name
        seen_unknown.add(it.unidentified_name)
        assert len(it.lore) > 120 and 'Unusual' not in it.lore
        assert 'they ' not in f' {it.lore.lower()} '.replace('.', ' ')     # no singular they
        assert 1 <= it.id_tier <= 5
    assert len(seen_unknown) == 6                   # each looks like itself


def test_hatch_levels_are_the_evolution_thresholds():
    assert LEVELS == (1, 25, 55)
    assert pet_system.tier_level(1) == 1 and pet_system.tier_level(2) == _EVOLVE_1
    assert pet_system.tier_level(3) == _EVOLVE_2
    for sid in SIX:
        assert hatch_level(sid) == LEVELS[sphere_spec(sid)['tier'] - 1]
    assert hatch_level('unusual_soul_sphere') == 1


# ---------------------------------------------------------------- each tier hatches at its level

@pytest.mark.parametrize('sid', PLAIN)
def test_each_plain_sphere_hatches_an_elemental_at_its_level_and_stage(sid, monkeypatch):
    from game_states import STATE_PET_NAME_INPUT
    _no_rare(monkeypatch)
    g = _game()
    pet = _throw(g, sid)
    tier = sphere_spec(sid)['tier']
    assert pet.species_key in ELEMENTAL
    assert (pet.level, pet.stage, pet.xp) == (LEVELS[tier - 1], tier - 1, 0)
    assert pet.max_hp == pet.hp == growth('health', pet.level)
    assert pet.base_damage == growth('bite', pet.level)
    assert len(pet.available_specials()) == tier - 1
    assert pet.hatch_sphere == sid
    assert g.state == STATE_PET_NAME_INPUT
    assert g._pet_name_input_buffer == pet.species_name
    assert sid in g.player.known_item_ids              # throwing it taught what it was
    want = _SPECIES[pet.species_key]['stages'][tier - 1]
    assert (want.get('hatch_msg') or want['msg']) in _messages(g, 3)


@pytest.mark.parametrize('sid', HEARTH)
def test_each_hearth_sphere_hatches_a_family_pet_at_its_level(sid, monkeypatch):
    monkeypatch.setattr(pet_system, '_FAMILY_SPHERE_RNG', _FixedRng(0.9))   # the last 20%: Shep
    g = _game()
    pet = _throw(g, sid)
    tier = sphere_spec(sid)['tier']
    assert pet.species_key == SHEP
    assert (pet.level, pet.stage) == (LEVELS[tier - 1], tier - 1)
    assert pet.species_name == ('Shep', 'Shep the Farmhound', 'Shep the Legend')[tier - 1]
    assert SHEP in g.player.family_cats_met
    assert g._naming_story['title'] == 'SHEP IS HERE!'
    assert g._pet_name_input_buffer == pet.species_name


def test_a_greater_sphere_shep_is_the_farmhound_with_sic_em_and_his_rescue():
    pet = Pet(SHEP, level=hatch_level('greater_hearth_sphere'))
    assert pet.name == 'Shep the Farmhound'
    assert [s['id'] for s in pet.available_specials()] == ['sic_em']
    assert pet.rescue_ready(1)
    legend = Pet(SHEP, level=hatch_level('master_hearth_sphere'))
    assert legend.name == 'Shep the Legend'
    assert [s['id'] for s in legend.available_specials()] == ['sic_em', 'sic_em_all']


@pytest.mark.parametrize('key,names', [
    ('sherlock', ('Sherlock', 'Sherlock the Stout', 'Sherlock the Immovable')),
    ('irene', ('Irene', 'Irene the Skyleaper', 'Irene the Seraph')),
])
def test_the_cats_hatch_at_each_tier_with_their_own_words(key, names, monkeypatch):
    r = 0.1 if key == 'sherlock' else 0.5
    monkeypatch.setattr(pet_system, '_FAMILY_SPHERE_RNG', _FixedRng(r))
    for sid, name in zip(HEARTH, names):
        g = _game()
        pet = _throw(g, sid)
        assert pet.species_key == key and pet.species_name == name
        tier = sphere_spec(sid)['tier']
        assert len(pet.available_specials()) == tier - 1
        assert pet_system.hatch_message(pet) in _messages(g, 3)
        if tier > 1:
            assert name in pet_system.hatch_message(pet)


def test_every_line_has_hatch_words_for_each_grown_stage():
    for key in ELEMENTAL + FAMILY_PETS:
        stages = _SPECIES[key]['stages']
        for st in (1, 2):
            words = stages[st].get('hatch_msg', '')
            assert stages[st]['name'] in words, (key, st)
            assert '{' not in words and 'they ' not in words.lower(), (key, st)


# ---------------------------------------------------------------- ordinary spheres keep the rare chance

@pytest.mark.parametrize('sid', PLAIN)
def test_every_plain_sphere_keeps_shep_one_and_each_cat_five(sid):
    cats, sheps = random.Random(41), random.Random(42)
    n = 200_000
    random.seed(3)
    seen = Counter(roll_sphere_species(sid, (), cats, sheps) for _ in range(n))
    assert abs(seen[SHEP] / n - 0.01) < 0.0012
    for cat in FAMILY_CATS:
        assert abs(seen[cat] / n - 0.05) < 0.003, (cat, seen[cat] / n)
    for line in ELEMENTAL:
        assert abs(seen[line] / n - 0.2225) < 0.006, (line, seen[line] / n)
    # Shep met: his share back to the lines, the cats unchanged.
    met = Counter(roll_sphere_species(sid, {SHEP}, cats, sheps) for _ in range(n))
    assert met[SHEP] == 0
    for cat in FAMILY_CATS:
        assert abs(met[cat] / n - 0.05) < 0.003
    for line in ELEMENTAL:
        assert abs(met[line] / n - 0.225) < 0.006
    everyone = {roll_sphere_species(sid, set(FAMILY_PETS), cats, sheps) for _ in range(5000)}
    assert everyone == set(ELEMENTAL)


# ---------------------------------------------------------------- hearth spheres guarantee the family

def test_a_hearth_sphere_is_sherlock_40_irene_40_shep_20():
    rng = random.Random(2026)
    n = 200_000
    state = random.getstate()
    seen = Counter(roll_family_sphere_pet((), rng) for _ in range(n))
    assert random.getstate() == state                  # the shared stream never moves
    assert set(seen) == set(FAMILY_PETS)
    assert abs(seen['sherlock'] / n - 0.40) < 0.005
    assert abs(seen['irene'] / n - 0.40) < 0.005
    assert abs(seen[SHEP] / n - 0.20) < 0.004
    for sid in HEARTH:                                 # every tier holds the same
        whole = Counter(roll_sphere_species(sid, (), family_rng=rng) for _ in range(20_000))
        assert set(whole) == set(FAMILY_PETS), sid


@pytest.mark.parametrize('met,want', [
    ({SHEP}, {'sherlock': 0.5, 'irene': 0.5}),
    ({'sherlock'}, {'irene': 2 / 3, SHEP: 1 / 3}),
    ({'irene'}, {'sherlock': 2 / 3, SHEP: 1 / 3}),
    ({'sherlock', 'irene'}, {SHEP: 1.0}),
    ({'sherlock', SHEP}, {'irene': 1.0}),
])
def test_a_met_family_pet_gives_his_share_to_the_unmet(met, want):
    rng = random.Random(77)
    n = 100_000
    seen = Counter(roll_family_sphere_pet(met, rng) for _ in range(n))
    assert set(seen) == set(want)
    for k, share in want.items():
        assert abs(seen[k] / n - share) < 0.006, (k, seen[k] / n)


@pytest.mark.parametrize('sid', HEARTH)
def test_with_the_whole_family_met_a_hearth_sphere_gives_an_elemental_at_its_tier(sid):
    assert roll_family_sphere_pet(set(FAMILY_PETS), _FixedRng(0.0)) is None
    g = _game()
    g.player.family_cats_met = set(FAMILY_PETS)
    pet = _throw(g, sid)
    tier = sphere_spec(sid)['tier']
    assert pet.species_key in ELEMENTAL
    assert (pet.level, pet.stage) == (LEVELS[tier - 1], tier - 1)


def test_a_family_pet_walking_or_bound_counts_as_met_for_a_hearth_sphere(monkeypatch):
    monkeypatch.setattr(pet_system, '_FAMILY_SPHERE_RNG', _FixedRng(0.0))   # Sherlock's slice
    g = _game()
    x, y = _free_tile(g)
    g.pets.append(Pet('sherlock', x, y))
    from items import make_item_by_id
    bound = make_item_by_id('artifact', 'soul_sphere')
    bound.bound_pet = Pet('irene')
    g.player.inventory.append(bound)
    pet = _throw(g, 'hearth_sphere')
    assert pet.species_key == SHEP                     # the only one left


# ---------------------------------------------------------------- no floor read at hatch

@pytest.mark.parametrize('sid', SIX)
def test_the_floor_never_changes_what_hatches(sid, monkeypatch):
    _no_rare(monkeypatch)
    monkeypatch.setattr(pet_system, '_FAMILY_SPHERE_RNG', _FixedRng(0.1))
    out = []
    for floor in (1, 40, 90):
        g = _game()
        g.dungeon_level = floor
        g.player.deepest_floor_reached = floor
        random.seed(5)
        pet = _throw(g, sid)
        out.append((pet.species_key, pet.level, pet.xp, pet.max_hp, pet.base_damage))
    assert out[0] == out[1] == out[2]


def test_the_emberpup_and_the_duck_start_from_their_own_story():
    # The Emberpup: a pup, level 1 on any floor. The duck: what it learned
    # riding on the hero's head for 2026 turns (1 XP every 3 turns).
    assert pet_system.DUCK_OF_DOOM_HATCH_XP == pet_system.DUCK_OF_DOOM_TURNS_REQUIRED // 3
    levels = set()
    for floor in (5, 60):
        g = _game()
        g.dungeon_level = floor
        g.player.armor_slots[0] = type('D', (), {'id': 'duck_of_doom'})()
        g.player.quirk_progress = {'duck_of_doom_turns': 2026}
        g._duck_of_doom_transform()
        (duck,) = [p for p in g.pets if p.species_key == 'duck_of_doom']
        levels.add((duck.level, duck.xp))
        assert duck.stage == 0
    assert len(levels) == 1


# ---------------------------------------------------------------- QA switches

def test_pq_force_sphere_tier_sets_the_level_of_any_sphere(monkeypatch):
    _no_rare(monkeypatch)
    monkeypatch.setenv('PQ_QA_MODE', '1')
    for tier in (1, 2, 3):
        monkeypatch.setenv('PQ_FORCE_SPHERE_TIER', str(tier))
        for sid in ('soul_sphere', 'master_hearth_sphere'):
            assert hatch_level(sid) == LEVELS[tier - 1]
    monkeypatch.setenv('PQ_FORCE_SPHERE_TIER', '3')
    monkeypatch.setenv('PQ_FORCE_SPHERE', 'shep')
    g = _game()
    pet = _throw(g, 'soul_sphere')
    assert pet.species_key == SHEP and pet.name == 'Shep the Legend'
    monkeypatch.setenv('PQ_QA_MODE', '0')               # only in QA mode
    assert hatch_level('soul_sphere') == 1
    monkeypatch.setenv('PQ_QA_MODE', '1')
    monkeypatch.setenv('PQ_FORCE_SPHERE_TIER', '7')     # nonsense is ignored
    assert hatch_level('greater_soul_sphere') == 25


def test_pq_force_sphere_still_forces_a_family_pet_from_any_sphere(monkeypatch):
    monkeypatch.setenv('PQ_QA_MODE', '1')
    monkeypatch.setenv('PQ_FORCE_SPHERE', 'irene')
    monkeypatch.setattr(pet_system, '_FAMILY_SPHERE_RNG', _FixedRng(0.9))
    assert roll_sphere_species('greater_hearth_sphere', ()) == 'irene'
    assert roll_sphere_species('master_sphere', ()) == 'irene'


# ---------------------------------------------------------------- spawn bands

def test_the_spawn_table_by_band():
    want = {
        10: {'soul_sphere': 0.08, 'hearth_sphere': 0.008},
        50: {'soul_sphere': 0.03, 'greater_soul_sphere': 0.04,
             'hearth_sphere': 0.003, 'greater_hearth_sphere': 0.004},
        80: {'soul_sphere': 0.01, 'greater_soul_sphere': 0.02, 'master_sphere': 0.02,
             'hearth_sphere': 0.001, 'greater_hearth_sphere': 0.002, 'master_hearth_sphere': 0.002},
    }
    for floor, shares in want.items():
        got = {k: v for k, v in sphere_chances(floor) if v}
        assert got == pytest.approx(shares), floor
    # each Hearth Sphere a tenth of its tier, in the same bands
    for f in range(1, 101):
        ch = dict(sphere_chances(f))
        for plain, hearth in zip(PLAIN, HEARTH):
            assert ch[hearth] == pytest.approx(ch[plain] / 10), (f, hearth)
        if f < 34:
            assert ch['greater_soul_sphere'] == 0
        if f < 60:
            assert ch['master_sphere'] == 0 and ch['master_hearth_sphere'] == 0


@pytest.mark.parametrize('floor', (10, 50, 80))
def test_the_spawn_rates_hold_over_many_floors(floor):
    """Seeded: 300,000 floors' worth of rolls land on the table."""
    rng = random.Random(1000 + floor)
    n = 300_000
    seen = Counter(sphere_for_floor(floor, rng) for _ in range(n))
    for sid, chance in sphere_chances(floor):
        tol = max(0.0006, 4 * (chance * (1 - chance) / n) ** 0.5)
        assert abs(seen[sid] / n - chance) <= tol, (floor, sid, seen[sid] / n, chance)
    assert sum(seen[s] for s in SIX) + seen[None] == n


def test_floors_spawn_only_their_bands_spheres():
    from dungeon import generate_dungeon, spawn_items
    allowed = {4: {'soul_sphere', 'hearth_sphere'},
               85: set(SIX)}
    for floor, ok in allowed.items():
        found = Counter()
        for s in range(40):
            random.seed(31000 + s + floor)
            d = generate_dungeon(80, 50, floor)
            for it in spawn_items(d.rooms, floor, d):
                if is_soul_sphere(it):
                    found[it.id] += 1
                    assert d.is_walkable(it.x, it.y)
        assert set(found) <= ok, (floor, found)


def test_a_hidden_treasure_chamber_can_hold_a_sphere(monkeypatch):
    """The treasure chamber re-runs the loot pass (structures=False), so a
    sphere turns up in one at its band's chance like anywhere else."""
    from dungeon import generate_dungeon, spawn_items
    random.seed(9)
    d = generate_dungeon(80, 50, 70)
    # (the module spawn_items will import, whatever another test reloaded)
    monkeypatch.setattr(sys.modules['pet_system'], 'sphere_for_floor',
                        lambda level, rng: 'master_sphere')
    room = max(d.rooms, key=lambda r: r.width * r.height)
    got = spawn_items([room, room], 70, d, structures=False)
    assert any(getattr(i, 'id', '') == 'master_sphere' for i in got)


def test_no_random_pool_hands_out_a_sphere():
    """Spheres come from the floor roll and the traders only: never a chest,
    a divine gift, a reward pool or a thief's pack."""
    import container_system
    from items import is_random_loot, load_items
    for it in load_items('artifact'):
        if is_soul_sphere(it):
            assert not is_random_loot(it), it.id
    pool = container_system._build_common_pool({'loot_table': {'artifact': 1}}, 100)
    assert not any(is_soul_sphere(i) for i in pool)


# ---------------------------------------------------------------- traders

def _sphere_entries(kind):
    import traders
    defn = traders.kind_def(kind)
    return {'stock': [e for e in defn['stock'] if 'id' in e], 'stock_size': [[1, 100, 20]]}


def _stocked(kind, floor, n=600):
    import traders
    defn = _sphere_entries(kind)
    got = Counter()
    for s in range(n):
        for it in traders.build_stock(defn, floor, random.Random(s)):
            got[it.id] += 1
    return got


def test_grindle_carries_soul_and_greater_spheres_by_band():
    assert set(_stocked('generalist', 10)) == {'soul_sphere'}
    assert set(_stocked('generalist', 50)) == {'soul_sphere', 'greater_soul_sphere'}
    deep = _stocked('generalist', 85)
    assert set(deep) == {'soul_sphere', 'greater_soul_sphere'}
    shallow = _stocked('generalist', 10)
    assert 0.18 < shallow['soul_sphere'] / 600 < 0.32


def test_the_sutler_sometimes_carries_a_soul_or_greater_sphere_at_each_gate():
    assert set(_stocked('sutler', 19)) == {'soul_sphere'}
    assert set(_stocked('sutler', 39)) == {'soul_sphere', 'greater_soul_sphere'}
    assert set(_stocked('sutler', 79)) == {'greater_soul_sphere'}


def test_vesper_rarely_carries_a_master_or_a_hearth_sphere():
    v62, v85 = _stocked('abyssal', 62, 1500), _stocked('abyssal', 85, 1500)
    assert set(v62) == {'master_sphere', 'greater_hearth_sphere'}
    assert set(v85) == {'master_sphere', 'greater_hearth_sphere', 'master_hearth_sphere'}
    assert v85['master_sphere'] / 1500 < 0.15
    assert v85['master_hearth_sphere'] / 1500 < 0.06


def test_no_trader_ever_stocks_dads_sphere_or_a_master_before_floor_60():
    import traders
    for kind, defn in traders.data()['traders'].items():
        for e in defn.get('stock', ()):
            assert e.get('id') != 'unusual_soul_sphere'
            if e.get('id') in ('master_sphere', 'master_hearth_sphere'):
                assert e['floors'][0] >= 60, kind


def test_a_sphere_he_has_is_never_crowded_off_the_shelf():
    import copy as _copy
    import traders
    defn = _copy.deepcopy(traders.kind_def('generalist'))
    for e in defn['stock']:
        if 'id' in e:
            e['chance'] = 1.0
    stock = traders.build_stock(defn, 50, random.Random(3))
    ids = [i.id for i in stock]
    assert 'soul_sphere' in ids and 'greater_soul_sphere' in ids


def test_sphere_prices_follow_the_tier_and_hearth_costs_more():
    import economy
    from items import make_item_by_id
    p = {sid: economy.merchant_price(make_item_by_id('artifact', sid), 70) for sid in SIX}
    assert p['soul_sphere'] < p['greater_soul_sphere'] < p['master_sphere']
    assert p['hearth_sphere'] < p['greater_hearth_sphere'] < p['master_hearth_sphere']
    for plain, hearth in zip(PLAIN, HEARTH):
        assert p[hearth] > p[plain]
    assert p['soul_sphere'] >= 1.5 * economy.floor_income(70)


def test_a_trader_buys_a_sphere_but_never_a_bound_one():
    import traders
    from items import make_item_by_id
    defn = traders.kind_def('generalist')
    assert traders.SELLABLE_ARTIFACTS == set(spheres())
    for sid in SIX:
        it = make_item_by_id('artifact', sid)
        assert traders.refusal(defn, it, known=True, cursed_known=False) is None, sid
    bound = make_item_by_id('artifact', 'soul_sphere')
    bound.bound_pet = Pet('irene')
    assert traders.refusal(defn, bound, known=True, cursed_known=False) == 'Not for sale'
    dads = make_item_by_id('artifact', 'unusual_soul_sphere')
    assert traders.refusal(defn, dads, known=True, cursed_known=False) == 'Not for sale'


def test_selling_a_sphere_on_a_real_game_pays_a_share_and_takes_it():
    import traders
    from mystery_system import MerchantNPC
    g = _game()
    s = _sphere(g, 'greater_soul_sphere')
    defn = traders.kind_def('generalist')
    x, y = _free_tile(g)
    m = MerchantNPC(x, y, [], [], kind='generalist', level=40, defn=defn)
    g.ground_items.append(m)
    g._trader_open(m)
    offer, why = g._trader_offer(s)
    assert why is None and offer > 0


# ---------------------------------------------------------------- Dad is unchanged

def test_dad_still_comes_from_the_unusual_soul_sphere_for_five_turns(monkeypatch):
    _no_rare(monkeypatch)
    g = _game()
    g.dungeon_level = 2
    s = _sphere(g, 'unusual_soul_sphere')
    tx, ty = _free_tile(g)
    g._throw_unusual_sphere(s, None, tx, ty)
    (dad,) = g.pets
    assert getattr(dad, 'is_dad', False) and dad.name == 'Dad'
    assert dad.turns_remaining == 5
    assert dad.take_damage(10 ** 6) == 0 and dad.get_attack_damage() == 999999
    assert s not in g.player.inventory


def test_the_unusual_sphere_keeps_its_own_rare_roll_and_boss_floor_rule(monkeypatch):
    from boss_levels import BOSS_LEVELS
    monkeypatch.setattr(pet_system, '_SHEP_RNG', _FixedRng(0.0))
    g = _game()
    g.dungeon_level = 2
    s = _sphere(g, 'unusual_soul_sphere')
    tx, ty = _free_tile(g)
    g._throw_unusual_sphere(s, None, tx, ty)
    assert [p.species_key for p in g.pets] == [SHEP] and g.pets[0].level == 1
    g2 = _game()
    g2.dungeon_level = sorted(BOSS_LEVELS)[0]
    s2 = _sphere(g2, 'unusual_soul_sphere')
    g2._throw_unusual_sphere(s2, None, *_free_tile(g2))
    assert s2 in g2.player.inventory and not g2.pets           # kept on a boss floor


def test_no_help_or_hint_names_dads_sphere():
    with open(os.path.join(ROOT, 'data', 'hints.json'), encoding='utf-8') as f:
        hints = f.read()
    assert 'unusual' not in hints.lower()
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    i = src.index('def _draw_help_screen')
    assert 'unusual' not in src[i:i + 12000].lower()


# ---------------------------------------------------------------- starting kits

def test_ash_ketchum_starts_with_four_plain_soul_spheres():
    g = _game(build='ash ketchum')
    sph = [i for i in g.player.inventory if is_soul_sphere(i)]
    assert [i.id for i in sph] == ['soul_sphere'] * 4
    assert all(getattr(i, 'bound_pet', None) is None for i in sph)


def test_the_qa_hero_carries_one_of_each_sphere():
    from welcome_screen import SECRET_BUILDS
    assert SECRET_BUILDS['titivillus'].get('_qa_tools')
    g = _game(build='titivillus')
    assert sorted(i.id for i in g.player.inventory if is_soul_sphere(i)) == sorted(SIX)
    assert not any(i.id == 'unusual_soul_sphere' for i in g.player.inventory)


# ---------------------------------------------------------------- the throw menu, kit and sheet

def test_the_throw_menu_offers_every_sphere_bound_or_not():
    from items import make_item_by_id
    g = _game()
    for sid in SIX:
        _sphere(g, sid)
    bound = make_item_by_id('artifact', 'soul_sphere')
    bound.bound_pet = Pet('water')
    g.player.inventory.append(bound)
    g._open_throw_menu()
    listed = [i for i in g.throw_menu_items if is_soul_sphere(i)]
    assert sorted(i.id for i in listed) == sorted(SIX + ('soul_sphere',))
    other = g._THROW_TABS[2][1]
    assert all(other(i) for i in listed)                 # under "Other"


def test_a_sphere_can_be_dropped_identified_and_read_from_the_sheet():
    g = _game()
    s = _sphere(g, 'master_sphere')
    ids = {a['id'] for a in g._item_actions(s, 'pack')}
    assert {'drop', 'identify', 'lore'} <= ids and 'equip' not in ids
    before = g.player.get_current_weight()
    g.player.remove_from_inventory(s)
    assert g.player.get_current_weight() == pytest.approx(before - 0.5)


def test_the_kit_and_the_character_sheet_list_every_sphere():
    g = _game()
    for sid in SIX:
        _sphere(g, sid)
    kit = [it.id for _src, it in g._kit_rows_for_slug('consumables') if is_soul_sphere(it)]
    assert sorted(kit) == sorted(SIX)
    g._open_character_sheet()
    g._charsheet_set_pack_filter('lore')
    sheet = [e['item'].id for e in g._charsheet_pack_entries() if is_soul_sphere(e['item'])]
    assert sorted(sheet) == sorted(SIX)
    s = next(i for i in g.player.inventory if i.id == 'greater_hearth_sphere')
    acts = {a['id']: a for a in g._item_actions(s, 'pack')}
    assert acts['drop']['enabled'] and acts['lore']['enabled']


def test_spheres_never_stack_so_each_keeps_its_own_tier():
    from items import Item, make_item_by_id
    a, b = make_item_by_id('artifact', 'soul_sphere'), make_item_by_id('artifact', 'soul_sphere')
    assert not isinstance(a, Item._STACKABLE_CLASSES)
    g = _game()
    g.player.add_to_inventory(a)
    g.player.add_to_inventory(b)
    assert sum(1 for i in g.player.inventory if i.id == 'soul_sphere') == 2


def test_an_unknown_sphere_shows_its_look_until_thrown_or_identified(monkeypatch):
    _no_rare(monkeypatch)
    g = _game()
    s = _sphere(g, 'greater_soul_sphere')
    g.player.known_item_ids.discard('greater_soul_sphere')
    assert g._display_name(s) == s.unidentified_name == 'Silver-Caged Sphere'
    tx, ty = _free_tile(g)
    g._throw_soul_sphere(s, None, tx, ty)
    second = _sphere(g, 'greater_soul_sphere')
    assert g._display_name(second) == 'Greater Soul Sphere'


# ---------------------------------------------------------------- theft, payment, bones

def test_a_thief_never_takes_a_sphere_and_no_npc_takes_a_bound_one():
    import npc_encounters
    import theft
    from items import make_item_by_id
    g = _game()
    for sid in SIX:
        _sphere(g, sid)
    bound = make_item_by_id('artifact', 'soul_sphere')
    bound.bound_pet = Pet(SHEP)
    g.player.inventory.append(bound)
    assert not any(is_soul_sphere(i) for i in theft.stealable(g.player))
    assert not npc_encounters.offerable(bound)


def test_bones_keep_only_worn_gear_so_no_sphere_crosses_runs(tmp_path, monkeypatch):
    import bones
    monkeypatch.setattr(bones, '_bones_dir', lambda: str(tmp_path))
    g = _game()
    for sid in SIX:
        _sphere(g, sid)
    bones.save_bones('x', 7, 'test', g.player, 10)
    saved = json.load(open(os.path.join(str(tmp_path), 'bones_L7.json'), encoding='utf-8'))
    assert not any(e['id'] in SIX for e in saved['gear'])


# ---------------------------------------------------------------- bound spheres

def test_a_bound_sphere_gives_back_its_pet_exactly_as_it_was():
    from game_states import STATE_PLAYER
    g = _game()
    g.dungeon_level = 3
    x, y = _free_tile(g)
    irene = Pet('irene', x, y, level=60)
    irene.nickname = 'Bean'
    irene.kills_count = 12
    irene.xp = 33
    irene.hatch_sphere = 'master_hearth_sphere'
    g.pets = [irene]
    g.player.x, g.player.y = x - 1 if g.dungeon.is_walkable(x - 1, y) else x, y
    if max(abs(irene.x - g.player.x), abs(irene.y - g.player.y)) > 1:
        g.player.x, g.player.y = x, y + 1
    g._pet_action_recall(irene)
    (bound,) = [i for i in g.player.inventory if getattr(i, 'bound_pet', None) is irene]
    assert not g.pets
    g.state = STATE_PLAYER
    tx, ty = _free_tile(g)
    g._throw_soul_sphere(bound, None, tx, ty)
    (back,) = g.pets
    assert back is irene and back.level == 60 and back.xp == 33 and back.kills_count == 12
    assert back.name == 'Bean, Irene the Seraph' and back.hatch_sphere == 'master_hearth_sphere'
    assert g.state == STATE_PLAYER                         # no naming popup for an old friend


def test_a_sphere_with_no_room_to_open_comes_down_whole():
    """A Master Sphere thrown into a dead end is not wasted: it rolls to a
    stop unbroken, to be thrown again somewhere with room."""
    g = _game()
    x, y = g.player.x, g.player.y
    for yy in range(g.dungeon.height):                 # one tile beside the hero, a monster on it
        for xx in range(g.dungeon.width):
            g.dungeon.tiles[yy][xx] = 1 if (xx, yy) in {(x, y), (x + 1, y)} else 0
    from test_shep import _monster
    g.monsters = [_monster(x + 1, y)]
    s = _sphere(g, 'master_sphere')
    g._throw_soul_sphere(s, g.monsters[0], x + 1, y)
    assert s in g.ground_items and s not in g.player.inventory and not g.pets
    assert g.dungeon.is_walkable(s.x, s.y)
    assert any('unbroken' in m for m in _messages(g, 3))


# ---------------------------------------------------------------- save and load

def test_spheres_and_a_tier_hatched_pet_survive_save_and_load(monkeypatch):
    from save_system import delete_save, load_game, save_game
    _no_rare(monkeypatch)
    name = '__test_spheres_save__'
    g = _game(name)
    for sid in SIX:
        _sphere(g, sid)
    pet = _throw(g, 'greater_soul_sphere')
    pet.nickname = 'Zip'
    try:
        assert save_game(g)
        g2 = _game(name)
        g2.load_state(load_game(name))
        assert sorted(i.id for i in g2.player.inventory if is_soul_sphere(i)) == sorted(SIX)
        (back,) = [p for p in g2.pets if p.nickname == 'Zip']
        assert back.level == 25 and back.stage == 1
        assert pet_system.hatch_source(back) == 'Greater Soul Sphere'
        # a sphere loaded from the save still hatches its own tier
        s = next(i for i in g2.player.inventory if i.id == 'master_sphere')
        tx, ty = _free_tile(g2)
        g2._throw_soul_sphere(s, None, tx, ty)
        assert g2.pets[-1].level == 55
    finally:
        delete_save(name)


def test_an_old_saves_soul_sphere_and_pet_still_work(monkeypatch):
    """A save from before the six: a pickled soul_sphere with the old look
    and lore, and a pet with no hatch_sphere."""
    from items import make_item_by_id
    _no_rare(monkeypatch)
    old = make_item_by_id('artifact', 'soul_sphere')
    old.unidentified_name = 'crimson sphere'
    old.__dict__.pop('id_tier', None)
    old = pickle.loads(pickle.dumps(old))
    assert is_soul_sphere(old) and hatch_level(old) == 1
    g = _game()
    g.player.inventory.append(old)
    tx, ty = _free_tile(g)
    g._throw_soul_sphere(old, None, tx, ty)
    assert g.pets[-1].level == 1
    legacy = Pet('fire')
    legacy.__dict__.pop('hatch_sphere', None)
    legacy = pickle.loads(pickle.dumps(legacy))
    assert pet_system.hatch_source(legacy) is None


# ---------------------------------------------------------------- the pet card

def test_the_pet_card_says_which_sphere_it_hatched_from(monkeypatch):
    g = _game()
    x, y = _free_tile(g)
    pet = Pet('fire', x, y, level=25)
    pet.hatch_sphere = 'greater_soul_sphere'
    plain = Pet('water', x, y)
    g.pets = [pet, plain]
    g.pet_menu_items = [pet, plain]
    seen = {}
    monkeypatch.setattr(g, '_draw_decision_menu', lambda **kw: seen.update(kw))
    g._draw_pet_menu()
    lines = [[d[0] for d in e['details'] if isinstance(d, tuple)] for e in seen['entries']]
    assert 'Hatched From: Greater Soul Sphere' in lines[0]
    assert not any(t.startswith('Hatched From') for t in lines[1])


# ---------------------------------------------------------------- art

def _png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    return struct.unpack('>II', head[16:24])


def test_every_sphere_has_its_own_distinct_64px_art_everywhere():
    import lore_art
    import renderer
    item_dir = os.path.join(ROOT, 'assets', 'tiles', 'items')
    with open(os.path.join(ROOT, 'tools', 'content', 'genart', 'installed_items.json'),
              encoding='utf-8') as f:
        installed = set(json.load(f)['items'])
    digests = set()
    for sid in SIX:
        own = os.path.join(item_dir, sid + '.png')
        path = renderer._resolve_item_sprite_path(sid)
        assert os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(own)), sid
        assert _png_size(own) == (64, 64), sid
        assert sid in installed, sid
        assert lore_art.art_path('item', sid) == path
        with open(own, 'rb') as f:
            digests.add(hashlib.sha1(f.read()).hexdigest())
    assert len(digests) == 6
    with open(os.path.join(item_dir, 'unusual_soul_sphere.png'), 'rb') as f:
        assert hashlib.sha1(f.read()).hexdigest() not in digests


def test_the_map_the_menus_and_the_lore_page_draw_each_sphere():
    import lore_art
    g = _game()
    for sid in SIX:
        assert g.renderer._get_item_sprite(sid) is not None, sid
        assert g._get_menu_sprite(sid) is not None, sid
        assert lore_art.plate('item', sid, 200) is not None, sid
