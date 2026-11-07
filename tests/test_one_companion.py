"""One companion at a time (Brandon, 2026-11-06).

Throwing a sphere (new or bound), adopting the Emberpup, Waddlekind's hatch
and the Summon Guardian and Gate spells each put the companion at the hero's
side back into a Bound Soul Sphere in the pack first, state kept. Helpers
that come and go (Dad, a sketch, a kill's ally, Fenrir, the Army of
Darkness) and the unicorn stay out. Ash Ketchum starts with four spheres:
this is reachable in a minute of play, so it is also on the play-test list.
"""
import os
import pickle
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

import items  # noqa: E402
import pet_system  # noqa: E402
from pet_system import Pet, DadPet, UnicornPet, is_companion  # noqa: E402

pygame.init()


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name='__one_companion__', secret_build=None)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def _open_tile(g):
    p = g.player
    taken = {(q.x, q.y) for q in g.pets}
    for r in range(1, 6):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                x, y = p.x + dx, p.y + dy
                if (x, y) != (p.x, p.y) and (x, y) not in taken and g.dungeon.is_walkable(x, y):
                    return x, y
    raise AssertionError("no open tile near the hero")


def _throw(g, sphere):
    from game_states import STATE_PLAYER
    if sphere not in g.player.inventory:
        g.player.inventory.append(sphere)
    tx, ty = _open_tile(g)
    g._throw_soul_sphere(sphere, None, tx, ty)
    g.state = STATE_PLAYER          # past the naming popup


def _new_sphere():
    return items.make_item_by_id('artifact', 'soul_sphere')


def _companions(g):
    return [p for p in g.pets if is_companion(p)]


def _bound(g):
    return [i for i in g.player.inventory if getattr(i, 'bound_pet', None) is not None]


def test_a_second_sphere_puts_the_first_companion_to_sleep(game):
    _throw(game, _new_sphere())
    first = _companions(game)[0]
    first.level = 7
    _throw(game, _new_sphere())
    assert len(_companions(game)) == 1
    assert _companions(game)[0] is not first
    held = _bound(game)
    assert len(held) == 1 and held[0].bound_pet is first
    assert first.level == 7
    assert any('returns to its sphere' in t for t, _k in game.msg_log.entries)


def test_throwing_the_bound_sphere_swaps_them_back(game):
    _throw(game, _new_sphere())
    first = _companions(game)[0]
    _throw(game, _new_sphere())
    second = _companions(game)[0]
    _throw(game, _bound(game)[0])
    assert _companions(game) == [first]
    assert [s.bound_pet for s in _bound(game)] == [second]


def test_helpers_and_the_unicorn_stay_out(game):
    p = game.player
    dad = DadPet(p.x + 1, p.y, duration=50)
    uni = UnicornPet(p.x - 1, p.y)
    ally = Pet('fire', p.x, p.y + 1)
    ally._temp_duration = 5
    deadite = Pet('fire', p.x, p.y - 1)
    deadite._summoned_minion = True
    game.pets = [dad, uni, ally, deadite]
    assert not any(is_companion(x) for x in game.pets)
    _throw(game, _new_sphere())
    for helper in (dad, uni, ally, deadite):
        assert helper in game.pets
    assert len(_companions(game)) == 1
    assert _bound(game) == []


def test_an_old_deadite_without_its_mark_is_still_a_helper():
    d = Pet('fire', 0, 0)
    d.species = dict(d.species, element='shadow')
    assert not is_companion(d)


def test_a_save_with_several_companions_out_stores_all_but_the_new_one(game):
    p = game.player
    game.pets = [Pet('water', p.x + 1, p.y), Pet('plant', p.x - 1, p.y)]
    _throw(game, _new_sphere())
    assert len(_companions(game)) == 1
    assert len(_bound(game)) == 2


def test_a_full_pack_sets_the_sphere_down_never_loses_it(game, monkeypatch):
    _throw(game, _new_sphere())
    first = _companions(game)[0]
    monkeypatch.setattr(game.player, 'add_to_inventory', lambda item: False)
    tx, ty = _open_tile(game)
    s = _new_sphere()
    game._throw_soul_sphere(s, None, tx, ty)
    at_feet = [i for i in game.ground_items if getattr(i, 'bound_pet', None) is first]
    assert at_feet and (at_feet[0].x, at_feet[0].y) == (game.player.x, game.player.y)
    assert first not in game.pets


def test_a_bound_sphere_keeps_its_pet_through_a_save():
    pet = Pet('electric', 3, 4, level=12)
    sphere = _new_sphere()
    sphere.bound_pet = pet
    back = pickle.loads(pickle.dumps(sphere))
    assert back.bound_pet.level == 12 and back.bound_pet.species_key == 'electric'


@pytest.mark.parametrize('effect', ['summon_guardian', 'gate'])
def test_the_summoning_spells_swap_too(game, effect):
    _throw(game, _new_sphere())
    first = _companions(game)[0]
    game._apply_spell_effect({'effect': effect, 'tier': 3, 'name': effect, 'power': ''})
    comps = _companions(game)
    assert len(comps) == 1 and comps[0] is not first
    assert [s.bound_pet for s in _bound(game)] == [first]


def test_recall_still_works_and_uses_the_same_sphere(game):
    _throw(game, _new_sphere())
    pet = _companions(game)[0]
    pet.x, pet.y = game.player.x + 1, game.player.y
    game._pet_action_recall(pet)
    assert pet not in game.pets
    held = _bound(game)
    assert held and held[0].name == f"Bound Soul Sphere ({pet.name})"


def test_every_way_a_companion_joins_stores_the_one_before_it():
    """Each `self.pets.append(` either adds a helper that never counts, or
    comes right after `_companions_to_stasis()` (or the bound-sphere branch
    that calls it). A new join site has to choose."""
    helpers = {
        ('game_combat.py', 'dad'), ('game_combat.py', '_ally'),
        ('game_combat.py', 'pet'),          # the sketch (SketchedPet) sites
        ('game_encounters.py', 'pet'),      # the unicorn
        ('game_magic.py', 'pet'),           # checked below by context
        ('main.py', 'fenrir'),
    }
    src_dir = os.path.join(ROOT, 'src')
    for fname in os.listdir(src_dir):
        if not fname.endswith('.py'):
            continue
        lines = open(os.path.join(src_dir, fname), encoding='utf-8').read().splitlines()
        for i, line in enumerate(lines):
            m = re.search(r'self\.pets\.append\((\w+)\)', line)
            if not m:
                continue
            window = '\n'.join(lines[max(0, i - 12):i])
            if '_companions_to_stasis()' in window:
                continue
            ctx = '\n'.join(lines[max(0, i - 30):i])
            ok = (('SketchedPet' in ctx) or ('DadPet' in ctx) or ('UnicornPet' in ctx)
                  or ('_temp_duration' in ctx) or ('_summoned_minion' in ctx)
                  or ('fenrir' in ctx.lower()))
            assert ok, f"{fname}:{i + 1}: a pet joins without the one-companion rule"
            assert (fname, m.group(1)) in helpers or ok


def test_ash_ketchums_four_spheres_give_one_companion_and_three_sleepers(game):
    for _ in range(4):
        _throw(game, _new_sphere())
    assert len(_companions(game)) == 1
    assert len(_bound(game)) == 3
