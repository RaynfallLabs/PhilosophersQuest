"""Shift+L swaps a light in and out (Brandon, 2026-11-22): "we need an easy way
to swap a light source in and out, like the readied weapon".

One key and one turn, whatever moves with it: the shield, or the two-hander
and the readied one-hander. Behaviour tests on a headless Game through the
key itself; how it feels in the hand is Brandon's play-test.
"""
import copy
import os
import pickle
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import items  # noqa: E402
import lights  # noqa: E402


@pytest.fixture
def g():
    from main import Game
    random.seed(11)
    items.bind_unique_registry(set())
    game = Game(pygame.display.set_mode((1, 1)), player_name='__light_swap__')
    game.monsters, game.pets = [], []
    game._popup_queue_list().clear()
    from game_states import STATE_PLAYER
    game.state = STATE_PLAYER
    p = game.player
    p.weapon = p.ranged_weapon = p.shield = None
    p.readied_weapon = None
    p.inventory = []
    game.turns = []
    game._advance_turn = lambda *a, **k: game.turns.append(1)
    game.said = []
    game.add_message = lambda text, *a, **k: game.said.append(text)
    return game


def _press(g, char='L'):
    key = getattr(pygame, f'K_{char.lower()}')
    ev = types.SimpleNamespace(type=pygame.KEYDOWN, key=key, unicode=char,
                               mod=pygame.KMOD_SHIFT if char.isupper() else 0)
    g.handle_event(ev)


def _light(g, lid='torch', n=1, fuel=None):
    it = items.make_item_by_id('light', lid)
    it.count = n
    if fuel is not None:
        it.fuel = fuel
    g.player.inventory.append(it)
    return it


def _shield(g):
    sh = copy.copy(next(s for s in items.load_items('shield')
                        if not lights.is_light(s) and not getattr(s, 'equip_chain_mode', '')))
    sh.buc, sh.cursed = 'uncursed', False
    g.player.shield = sh
    return sh


def _weapon(g, two_handed):
    for seed in range(400):
        w = items.pick_random_weapon_for_floor(1 + seed % 30, random.Random(seed))
        if (w is not None and bool(getattr(w, 'two_handed', False)) is two_handed
                and not getattr(w, 'requires_ammo', None)):
            w = copy.copy(w)
            w.buc, w.cursed = 'uncursed', False
            return w
    raise AssertionError('no such weapon')


def _pack_count(g, lid):
    return sum(int(getattr(i, 'count', 1) or 1) for i in g.player.inventory if i.id == lid)


def test_one_press_lights_a_torch_one_press_puts_it_away(g):
    _light(g, 'torch', 3)
    _press(g)
    assert lights.is_lit(g.player.shield) and g.player.shield.id == 'torch'
    assert _pack_count(g, 'torch') == 2 and g.turns == [1]
    _press(g)
    assert g.player.shield is None
    assert _pack_count(g, 'torch') == 3 and g.turns == [1, 1]


def test_the_shield_comes_off_and_goes_back_in_one_turn_each_way(g):
    sh = _shield(g)
    _light(g)
    _press(g)
    assert lights.held(g.player) is not None and any(i is sh for i in g.player.inventory)
    assert g.turns == [1]
    _press(g)
    assert g.player.shield is sh and not any(i is sh for i in g.player.inventory)
    assert g.turns == [1, 1]


def test_a_cursed_shield_stays_and_costs_no_turn(g):
    sh = _shield(g)
    sh.buc, sh.cursed = 'cursed', True
    _light(g)
    _press(g)
    assert g.player.shield is sh and g.turns == [] and g.said


def test_no_light_costs_no_turn_and_says_so(g):
    sh = _shield(g)
    _press(g)
    assert g.player.shield is sh and g.turns == []
    assert g.said == [lights.line('none_to_take')]


def test_the_last_torch_burns_out_and_the_key_gives_the_shield_back(g):
    sh = _shield(g)
    _light(g, fuel=1)
    _press(g)
    g._light_tick()
    assert g.player.shield is None
    _press(g)
    assert g.player.shield is sh and g.turns == [1, 1]


def test_a_two_hander_gives_way_to_the_readied_sidearm_and_comes_back(g):
    big, side = _weapon(g, True), _weapon(g, False)
    g.player.weapon = big
    g.player.inventory.append(side)
    g.player.readied_weapon = side
    _light(g)
    _press(g)
    assert g.player.weapon is side and g.player.readied_weapon is big
    assert lights.is_lit(lights.held(g.player)) and g.turns == [1]
    _press(g)
    assert g.player.weapon is big and g.player.readied_weapon is side
    assert g.player.shield is None and g.turns == [1, 1]


def test_a_two_hander_with_no_sidearm_says_how_and_moves_nothing(g):
    big = _weapon(g, True)
    g.player.weapon = big
    _light(g)
    _press(g)
    assert g.player.weapon is big and g.player.shield is None and g.turns == []
    assert 'K, then R' in g.said[-1]


def test_a_slung_shield_waits_for_the_light_then_returns_with_the_one_hander(g):
    sh = _shield(g)
    big, side = _weapon(g, True), _weapon(g, False)
    g.player.weapon = side
    import known_by_hand
    known_by_hand.learn(g.player, sh)
    g.player.inventory.append(big)
    g.player.readied_weapon = big
    _press(g, 's')                      # the two-hander out, the shield slung
    assert g.player.weapon is big and g.player.shield is None
    _light(g)
    _press(g)
    assert g.player.weapon is side and lights.held(g.player) is not None
    _press(g)
    assert g.player.weapon is big and g.player.shield is None
    _press(g, 's')
    assert g.player.weapon is side and g.player.shield is sh


def test_a_weapon_readied_since_is_the_heros_choice(g):
    big, side, other = _weapon(g, True), _weapon(g, False), _weapon(g, False)
    g.player.weapon = big
    g.player.inventory += [side, other]
    g.player.readied_weapon = side
    _light(g)
    _press(g)
    g.player.readied_weapon = other
    _press(g)
    assert g.player.weapon is side and g.player.readied_weapon is other


def test_readying_a_light_chooses_it_and_it_can_be_unreadied(g):
    torch = _light(g, 'torch')
    best = max((k for k in _light_ids() if k != 'torch'),
               key=lambda k: lights.sight_of(items.make_item_by_id('light', k)))
    _light(g, best)
    assert lights.pick(g.player).id == best
    assert any(a['id'] == 'ready' and a['label'] == 'Ready'
               for a in g._item_actions(torch, 'pack'))
    g._ready_light(torch)
    assert lights.pick(g.player) is torch and g._readied_mark(torch)
    assert any(a['label'] == 'Unready' for a in g._item_actions(torch, 'pack'))
    g._unready_light(torch)
    assert lights.pick(g.player).id == best


def _light_ids():
    import json
    with open(os.path.join(ROOT, 'data', 'items', 'light.json'), encoding='utf-8') as f:
        return [k for k, v in json.load(f).items() if isinstance(v, dict)]


def test_a_part_burnt_torch_is_taken_before_a_fresh_one(g):
    _light(g, 'torch', 3)
    stub = _light(g, 'torch', fuel=50)
    assert lights.pick(g.player) is stub


def test_a_dry_lantern_is_filled_as_it_is_drawn(g):
    lid = next(k for k in _light_ids()
               if lights.fuel_kind(items.make_item_by_id('light', k)) == 'oil')
    lt = _light(g, lid, fuel=0)
    assert lights.pick(g.player) is None
    g.player.inventory.append(items.make_item_by_id('flask', 'flask_of_fire_oil'))
    _press(g)
    assert g.player.shield is lt and lights.is_lit(lt) and g.turns == [1]
    assert lights.fuel_left(lt) == lights.burn_of(lt)


def test_stowing_a_soaked_light_does_not_dry_it(g):
    lt = _light(g)
    lt._wet = 5
    _press(g)
    assert g.player.shield is lt and not lights.is_lit(lt)
    assert g.said[-1] == lights.line('taken_up_wet', light=g._bare_name(lt))


def test_a_helpless_hero_cannot_swap(g):
    _light(g)
    g._helpless_turn = lambda: True
    _press(g)
    assert g.player.shield is None


def test_plain_l_is_still_the_message_log(g):
    _light(g)
    _press(g, 'l')
    assert g.player.shield is None and g.turns == []


def test_a_save_from_before_the_key_loads_with_nothing_set_aside():
    from player import Player
    p = Player()
    for k in ('_light_kind', '_light_aside', '_light_sidearm'):
        p.__dict__.pop(k, None)
    back = pickle.loads(pickle.dumps(p))
    assert back._light_kind == '' and back._light_aside is None and back._light_sidearm is None


def test_the_help_and_the_card_name_the_key():
    import json
    with open(os.path.join(ROOT, 'data', 'ui', 'gear_and_load.json'), encoding='utf-8') as f:
        page = json.load(f)
    rows = [k for s in page['sections'] for k, _v in s.get('rows', ())]
    assert 'Shift+L' in rows
    assert any('Shift+L' in s for s in lights.card_lines(items.make_item_by_id('light', 'torch')))


def test_the_kit_calls_a_readied_light_readied(g):
    torch = _light(g)
    assert g._kit_source_label('pack', torch) == 'In Pack'
    g._ready_light(torch)
    assert g._kit_source_label('pack', torch) == 'Readied'
    assert 'Shift+L' in g._kit_status_line('pack', torch)[0]
