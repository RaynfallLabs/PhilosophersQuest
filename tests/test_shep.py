"""Shep (2026-10-17): the family farm dog from Brandon's dad's bedtime stories,
an ultra-rare Soul Sphere hatch. "Sic 'em, Shep!"

Shep is 1% per hatch (rolled first, on his own random stream), each family cat
stays at 5%, and the four elemental lines share the rest. Once he is met this
run his 1% goes back to the elemental lines. His line is about a tenth
stronger than the others (special multipliers only), and his rescue, He
Always Comes, brings him streaking in once a floor when the hero is down to a
quarter of his health with a foe beside him.

A 1% hatch is out of reach of a play-test, so the roll, the hatch, the
abilities, the rescue and the save are pinned here on a real headless Game.
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
from pet_system import (FAMILY_CAT_CHANCE, FAMILY_CATS, FAMILY_PETS, SHEP,  # noqa: E402
                        SHEP_CHANCE, Pet, _SPECIES, _EVOLVE_1, _EVOLVE_2,
                        family_pets_present, random_species, roll_rare_sphere_pet,
                        roll_shep, roll_soul_sphere_species)

ELEMENTAL = ('electric', 'water', 'plant', 'fire')
STAGE_NAMES = ['Shep', 'Shep the Farmhound', 'Shep the Legend']

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1, 1))
    return _SCREEN


def _game(name='__test_shep__'):
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


def _sphere(g, sid='soul_sphere'):
    from items import make_item_by_id
    s = make_item_by_id('artifact', sid)
    g.player.inventory.append(s)
    return s


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


def _messages(g, n=8):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


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


def _shep(x, y, level=1):
    pet = Pet(SHEP, x, y)
    pet.level = level
    pet._refresh_stats()
    pet.hp = pet.max_hp
    return pet


def _special(sid):
    return next(s for s in _SPECIES[SHEP]['specials'] if s['id'] == sid)


def _open_room(g, half=4):
    """A centre tile with clear floor `half` tiles out every way (carved out
    of the hero's own floor when this map has no room that big)."""
    for y in range(half + 1, g.dungeon.height - half - 1):
        for x in range(half + 1, g.dungeon.width - half - 1):
            if all(g.dungeon.is_walkable(x + i, y + j)
                   for i in range(-half, half + 1) for j in range(-half, half + 1)):
                return x, y
    from dungeon import FLOOR
    x = min(max(g.player.x, half + 1), g.dungeon.width - half - 2)
    y = min(max(g.player.y, half + 1), g.dungeon.height - half - 2)
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            g.dungeon.tiles[y + j][x + i] = FLOOR
    return x, y


def _far_walkable(g, x, y, min_dist=12):
    for yy in range(g.dungeon.height):
        for xx in range(g.dungeon.width):
            if max(abs(xx - x), abs(yy - y)) >= min_dist and g.dungeon.is_walkable(xx, yy):
                return xx, yy
    raise AssertionError('no far floor')


# ---------------------------------------------------------------- the roll

def test_shep_is_one_percent_each_cat_stays_five_and_the_lines_share_the_rest():
    cats, sheps = random.Random(20261017), random.Random(1984)
    n = 400_000
    state = random.getstate()
    seen = Counter(roll_rare_sphere_pet((), cats, sheps) or 'normal' for _ in range(n))
    assert random.getstate() == state            # the shared stream never moves
    assert SHEP_CHANCE == 0.01 and FAMILY_CAT_CHANCE == 0.05
    assert abs(seen[SHEP] / n - 0.01) < 0.0008, seen[SHEP] / n
    for cat in FAMILY_CATS:
        assert abs(seen[cat] / n - 0.05) < 0.002, (cat, seen[cat] / n)

    random.seed(11)
    whole = Counter(roll_soul_sphere_species((), cats, sheps) for _ in range(n))
    assert set(whole) == set(ELEMENTAL) | set(FAMILY_PETS)
    assert abs(whole[SHEP] / n - 0.01) < 0.0008
    for cat in FAMILY_CATS:
        assert abs(whole[cat] / n - 0.05) < 0.002, (cat, whole[cat] / n)
    for line in ELEMENTAL:                       # (100 - 1 - 5 - 5) / 4
        assert abs(whole[line] / n - 0.2225) < 0.004, (line, whole[line] / n)


def test_shep_is_rolled_first_on_his_own_stream():
    # A hit on Shep's stream is Shep, whatever the cats' stream says.
    assert roll_rare_sphere_pet((), _FixedRng(0.01), _FixedRng(0.0099)) == SHEP
    assert roll_rare_sphere_pet((), _FixedRng(0.01), _FixedRng(0.0100)) == 'sherlock'
    assert roll_shep((), _FixedRng(0.0)) == SHEP
    assert roll_shep((), _FixedRng(0.5)) is None


def test_shep_already_met_gives_his_one_percent_back_to_the_elemental_lines():
    cats, sheps = random.Random(5), random.Random(6)
    n = 400_000
    whole = Counter(roll_soul_sphere_species({SHEP}, cats, sheps) for _ in range(n))
    assert whole[SHEP] == 0
    for cat in FAMILY_CATS:                      # the cats do not take his share
        assert abs(whole[cat] / n - 0.05) < 0.002, (cat, whole[cat] / n)
    for line in ELEMENTAL:                       # (100 - 5 - 5) / 4
        assert abs(whole[line] / n - 0.225) < 0.004, (line, whole[line] / n)
    # A sure hit on his stream is nothing once he is met.
    assert roll_shep({SHEP}, _FixedRng(0.0)) is None
    everyone = Counter(roll_soul_sphere_species(set(FAMILY_PETS), cats, sheps) for _ in range(20_000))
    assert set(everyone) == set(ELEMENTAL)


def test_shep_counts_as_met_walking_bound_or_remembered():
    sphere = type('S', (), {})()
    sphere.bound_pet = Pet(SHEP)
    assert family_pets_present(None, [], [sphere]) == {SHEP}
    assert family_pets_present(None, [Pet(SHEP)], []) == {SHEP}
    player = type('P', (), {'family_cats_met': {SHEP}})()
    assert family_pets_present(player, [], []) == {SHEP}


def test_the_ordinary_pool_never_holds_shep():
    random.seed(2)
    assert {random_species() for _ in range(3000)} == set(ELEMENTAL)


def test_summon_guardian_and_gate_never_bring_shep(monkeypatch):
    # Even with every rare stream forced to a sure hit, the summons draw from
    # the ordinary pool only.
    monkeypatch.setattr(pet_system, '_SHEP_RNG', _FixedRng(0.0))
    monkeypatch.setattr(pet_system, '_CAT_RNG', _FixedRng(0.0))
    g = _game()
    seen = set()
    for effect in ('summon_guardian', 'gate'):
        for _ in range(60):
            g.pets = []
            g._apply_spell_effect({'effect': effect, 'tier': 3})
            seen |= {p.species_key for p in g.pets}
    assert seen and seen <= set(ELEMENTAL), seen


def test_the_qa_switch_forces_a_shep_hatch(monkeypatch):
    monkeypatch.setenv('PQ_QA_MODE', '1')
    monkeypatch.setenv('PQ_FORCE_SPHERE', 'shep')
    monkeypatch.setattr(pet_system, '_SHEP_RNG', _FixedRng(0.99))
    assert roll_soul_sphere_species(()) == SHEP
    assert roll_soul_sphere_species({SHEP}) in ELEMENTAL     # still once a run
    monkeypatch.setenv('PQ_QA_MODE', '0')                    # only in QA mode
    assert roll_rare_sphere_pet((), _FixedRng(0.5)) is None


# ---------------------------------------------------------------- hatching on a real Game

def test_a_soul_sphere_hatches_shep_with_his_name_ready(monkeypatch):
    from game_states import STATE_PET_NAME_INPUT, STATE_PLAYER
    g = _game()
    (tx, ty), = _free_tiles_near(g)
    monkeypatch.setattr(pet_system, '_SHEP_RNG', _FixedRng(0.005))
    g._throw_soul_sphere(_sphere(g), None, tx, ty)
    shep = g.pets[-1]
    assert shep.species_key == SHEP and shep.name == 'Shep'
    assert g.state == STATE_PET_NAME_INPUT
    assert g._pet_name_input_buffer == 'Shep'               # the popup defaults to "Shep"
    assert g._naming_story['title'] == 'SHEP IS HERE!'
    assert SHEP in g.player.family_cats_met
    assert any('It is Shep.' in m for m in _messages(g, 4))
    g._pet_name_input(pygame.K_RETURN, '')                  # keep the default
    assert shep.nickname == '' and shep.name == 'Shep' and g.state == STATE_PLAYER
    assert any('Some names you don' in m for m in _messages(g, 3))

    # The same lucky roll again: he is met, so the sphere gives an ordinary line.
    monkeypatch.setattr(pet_system, '_CAT_RNG', _FixedRng(0.99))
    taken = {(p.x, p.y) for p in g.pets}
    (tx, ty), = _free_tiles_near(g, exclude=taken)
    g._throw_soul_sphere(_sphere(g), None, tx, ty)
    assert g.pets[-1].species_key in ELEMENTAL
    assert g._naming_story is None


def test_a_nickname_for_shep_keeps_shep_in_his_name(monkeypatch):
    g = _game()
    (tx, ty), = _free_tiles_near(g)
    monkeypatch.setattr(pet_system, '_SHEP_RNG', _FixedRng(0.0))
    g._throw_soul_sphere(_sphere(g), None, tx, ty)
    shep = g.pets[-1]
    g._pet_name_input_buffer = 'Rex'
    g._pet_name_input(pygame.K_RETURN, '')
    assert shep.name == 'Rex, Shep' and shep.call_name == 'Rex'
    assert any("He'll answer to Rex" in m for m in _messages(g, 3))


def test_the_unusual_soul_sphere_can_hatch_shep_instead_of_dad(monkeypatch):
    g = _game()
    g.dungeon_level = 2
    (tx, ty), = _free_tiles_near(g)
    monkeypatch.setattr(pet_system, '_SHEP_RNG', _FixedRng(0.002))
    g._throw_unusual_sphere(_sphere(g, 'unusual_soul_sphere'), None, tx, ty)
    assert [p.species_key for p in g.pets] == [SHEP]


# ---------------------------------------------------------------- growing up

def test_shep_evolves_through_three_stages_all_named_shep():
    pet = Pet(SHEP)
    assert pet.species_name == 'Shep'
    assert pet.available_specials() == []
    msgs = []
    while pet.level < _EVOLVE_2:
        msgs += pet.gain_xp(500)
    assert pet.stage == 2 and pet.species_name == 'Shep the Legend'
    for stage in (1, 2):
        want = _SPECIES[SHEP]['stages'][stage]['msg'].format(old=STAGE_NAMES[stage - 1])
        assert msgs.count(want) == 1, (want, msgs)
    assert [s['name'] for s in _SPECIES[SHEP]['stages']] == STAGE_NAMES
    assert all('Shep' in n for n in STAGE_NAMES)
    assert [s['id'] for s in pet.available_specials()] == ['sic_em', 'sic_em_all']


def test_a_nicknamed_shep_evolves_by_his_own_name():
    pet = Pet(SHEP)
    pet.nickname = 'Rex'
    pet.gain_xp(20 * sum(range(1, _EVOLVE_1)))
    assert pet.stage == 1 and pet.name == 'Rex, Shep the Farmhound'


# ---------------------------------------------------------------- power: a tenth above the rest

def test_shep_is_slightly_stronger_than_the_cats_and_no_more():
    # Same growth table as every pet...
    for level in (1, 25, 55, 90):
        ref, shep = Pet('electric'), Pet(SHEP)
        for p in (ref, shep):
            p.level = level
            p._refresh_stats()
        assert (shep.max_hp, shep.base_damage) == (ref.max_hp, ref.base_damage)
    # ...and special multipliers 10-15% above the cats' at each stage.
    for stage in (1, 2):
        cats = [s for k in FAMILY_CATS for s in _SPECIES[k]['specials'] if s['unlock_stage'] == stage]
        (mine,) = [s for s in _SPECIES[SHEP]['specials'] if s['unlock_stage'] == stage]
        cat_avg = sum(s['damage_mult'] for s in cats) / len(cats)
        assert 1.10 <= mine['damage_mult'] / cat_avg <= 1.15, (stage, mine['damage_mult'], cat_avg)
        assert mine['cooldown'] == cats[0]['cooldown']         # cooldowns unchanged
        assert mine.get('status_chance', 0) <= 0.75
        assert mine['desc']
    rescue = _SPECIES[SHEP]['rescue']
    assert rescue['damage_mult'] == 1.5 and rescue['hp_share'] == 0.25


# ---------------------------------------------------------------- Sic 'Em!

def test_sic_em_streaks_to_the_target_and_bites_hard(monkeypatch):
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x - 3, y - 3
    shep = _shep(x - 3, y, level=_EVOLVE_1)
    g.pets = [shep]
    m = _monster(x + 4, y)                 # seven tiles: beyond any cat's reach
    g.monsters = [m]
    monkeypatch.setattr(random, 'random', lambda: 0.0)     # the knockdown lands
    g._resolve_pet_special(shep, _special('sic_em'), m.x, m.y)
    assert max(abs(shep.x - m.x), abs(shep.y - m.y)) == 1
    assert m.hp == m.max_hp - int(shep.base_damage * 1.7)
    assert m.status_effects.get('stunned', 0) >= 2
    assert any("Sic 'em, Shep!" in s for s in _messages(g, 4))


def test_sic_em_shouts_his_nickname_and_reaches_seven_tiles():
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x - 3, y - 3
    shep = _shep(x - 3, y, level=_EVOLVE_1)
    shep.nickname = 'Rex'
    g.pets = [shep]
    m = _monster(x + 4, y)
    g.monsters = [m]
    g._begin_pet_special_targeting(shep, _special('sic_em'))
    assert (g.target_cursor_x, g.target_cursor_y) == (m.x, m.y)
    g._confirm_pet_special_target()
    assert m.hp < m.max_hp and shep.special_cooldown('sic_em') >= 249   # (one turn ticked)
    assert any("Sic 'em, Rex!" in s for s in _messages(g, 8))


def test_sic_em_at_nothing_gets_a_puzzled_look():
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x - 3, y - 3
    shep = _shep(x - 3, y, level=_EVOLVE_1)
    g.pets = [shep]
    g._resolve_pet_special(shep, _special('sic_em'), x + 2, y)
    said = _messages(g, 3)
    assert any('finds nobody there' in s for s in said)
    assert not any("Sic 'em" in s for s in said)


# ---------------------------------------------------------------- Sic 'Em All!

def test_sic_em_all_brings_him_from_anywhere_and_bites_every_foe_beside_you():
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    fx, fy = _far_walkable(g, x, y)
    shep = _shep(fx, fy, level=_EVOLVE_2)
    g.pets = [shep]
    foes = [_monster(x + 1, y), _monster(x - 1, y), _monster(x, y + 1)]
    bystander = _monster(x + 3, y)
    g.monsters = foes + [bystander]
    turn = g.turn_count
    g._begin_pet_special_targeting(shep, _special('sic_em_all'))   # no cursor
    for m in foes:
        assert m.hp <= m.max_hp - int(shep.base_damage * 2.0)   # (then his own turn too)
    assert bystander.hp == bystander.max_hp
    assert max(abs(shep.x - x), abs(shep.y - y)) == 1
    assert shep.special_cooldown('sic_em_all') > 0 and g.turn_count > turn
    assert any("ALL of 'em!" in s for s in _messages(g, 30))


# ---------------------------------------------------------------- He Always Comes

def _rescue_scene(level=1):
    g = _game()
    x, y = _open_room(g)
    g.player.x, g.player.y = x, y
    fx, fy = _far_walkable(g, x, y)
    shep = _shep(fx, fy, level=level)
    g.pets = [shep]
    g.visible.discard((fx, fy))                  # out of the hero's sight
    foe = _monster(x + 1, y)
    g.monsters = [foe]
    g.player.hp = max(1, g.player.max_hp // 4)   # 25%: on the line
    return g, shep, foe


def test_he_always_comes_when_the_hero_is_down_with_a_foe_beside_him(monkeypatch):
    g, shep, foe = _rescue_scene()
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    g._do_pet_turns()
    assert max(abs(shep.x - g.player.x), abs(shep.y - g.player.y)) == 1
    assert max(abs(shep.x - foe.x), abs(shep.y - foe.y)) == 1
    assert foe.hp == foe.max_hp - int(shep.base_damage * 1.5)   # the rescue was his turn
    assert foe.status_effects.get('stunned', 0) >= 2
    said = _messages(g, 10)
    assert any('black-and-white blur comes streaking out of the dark' in s for s in said)
    assert any('runaway hay wagon' in s for s in said)
    assert not shep.rescue_ready(g.player.deepest_floor_reached)


def test_the_rescue_is_once_a_floor_and_comes_back_on_a_new_floor():
    g, shep, foe = _rescue_scene()
    g._do_pet_turns()
    assert not shep.rescue_ready(g.player.deepest_floor_reached)
    # Still down, still a foe beside him: no second rescue on this floor.
    before = sum('streaking out of the dark' in s for s in _messages(g, 40))
    g.player.hp = 1
    g._do_pet_turns()
    assert sum('streaking out of the dark' in s for s in _messages(g, 40)) == before
    # A floor reached for the first time gives it back.
    g._change_level(g.dungeon_level + 1, True)
    assert g.player.deepest_floor_reached >= 2
    assert shep.rescue_ready(g.player.deepest_floor_reached)


def test_no_rescue_above_a_quarter_health_or_with_no_foe_beside_the_hero():
    g, shep, foe = _rescue_scene()
    g.player.hp = g.player.max_hp // 4 + 2
    g._do_pet_turns()
    assert shep.rescue_ready(g.player.deepest_floor_reached)

    g, shep, foe = _rescue_scene()
    foe.x += 2                                   # two tiles off: not beside him
    g._do_pet_turns()
    assert shep.rescue_ready(g.player.deepest_floor_reached)

    g, shep, foe = _rescue_scene()
    foe.is_allied = True                         # a friend is not a threat
    g._do_pet_turns()
    assert shep.rescue_ready(g.player.deepest_floor_reached)


def test_a_dead_shep_does_not_come():
    g, shep, foe = _rescue_scene()
    shep.alive = False
    g._do_pet_turns()
    assert foe.hp == foe.max_hp


def test_shep_the_legend_takes_them_all_down_and_stands_guard():
    g, shep, foe = _rescue_scene(level=_EVOLVE_2)
    x, y = g.player.x, g.player.y
    others = [_monster(x - 1, y), _monster(x, y - 1)]
    g.monsters += others
    g._do_pet_turns()
    for m in [foe] + others:
        assert m.hp <= m.max_hp - int(shep.base_damage * 1.5)
    assert g.player.has_effect('shielded')
    assert any('farm dog through a flock of crows' in s for s in _messages(g, 12))


def test_the_pet_card_shows_whether_he_will_come():
    g, shep, foe = _rescue_scene()
    lines = g._pet_rescue_lines(shep)
    assert lines[0][0] == 'He Always Comes: Ready'
    g._do_pet_turns()
    assert g._pet_rescue_lines(shep)[0][0] == 'He Always Comes: Spent Until A New Floor'
    assert g._pet_rescue_lines(Pet('electric')) == []


# ---------------------------------------------------------------- save and load

def test_shep_survives_save_and_load():
    from save_system import save_game, load_game, delete_save
    name = '__test_shep_save__'
    g = _game(name)
    shep = _shep(g.player.x + 1, g.player.y, level=_EVOLVE_2)
    shep.nickname = 'Rex'
    shep.spend_rescue(g.player.deepest_floor_reached)
    g.pets = [shep]
    g.player.family_cats_met = {SHEP}
    try:
        assert save_game(g)
        state = load_game(name)
        g2 = _game(name)
        g2.load_state(state)
        (back,) = [p for p in g2.pets if p.species_key == SHEP]
        assert back.name == 'Rex, Shep the Legend' and back.level == _EVOLVE_2
        assert {s['id'] for s in back.available_specials()} == {'sic_em', 'sic_em_all'}
        assert not back.rescue_ready(g2.player.deepest_floor_reached)
        assert g2._family_cats_present() == {SHEP}
    finally:
        delete_save(name)


# ---------------------------------------------------------------- art

def _png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    return struct.unpack('>II', head[16:24])


@pytest.mark.parametrize('stage', range(3))
def test_every_stage_has_its_sprite(stage):
    import renderer
    pet = Pet(SHEP)
    pet.level = (1, _EVOLVE_1, _EVOLVE_2)[stage]
    mid = pet.species_name.lower().replace(' ', '_')         # as game_render looks it up
    path = os.path.join(renderer._SPRITE_DIR, mid + '.png')
    assert os.path.exists(path), mid
    assert _png_size(path) == (64, 64), mid
