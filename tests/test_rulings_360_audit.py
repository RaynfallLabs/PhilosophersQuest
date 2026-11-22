"""The 3.6.0 rulings build, as an independent audit found it (2026-11-22).

Each test is a way a ruling was half-wired, or untrue on the screen, after
its first build. Logic tests on a headless Game.
"""
from __future__ import annotations

import json
import os
import random
import types

import pytest

from test_bugbash_360_monsters import MONS, _mk, _msgs, _scene
from test_traders import _game as _shop_game
from test_traders import _trader

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def _data(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


def _item(cls, iid):
    import items
    it = items.make_item_by_id(cls, iid)
    it.buc, it.cursed = 'uncursed', False
    return it


# ------------------------------------------------------------------------ A1

def test_a1_the_shop_quotes_a_bundle_whole():
    import game_traders
    g = _shop_game()
    _trader(g, 'generalist')
    g._shop_merchant.purse = 100_000
    stack = _item('light', 'torch')
    stack.count, stack.id_level = 3, 5
    g.player.known_item_ids.add('torch')
    g.player.inventory = [stack]
    g._shop_tab = game_traders.TAB_SELL
    g._shop_selection = 0
    menu = g._trader_menu()
    assert 'each' not in menu['entries'][0]['detail']
    assert 'sell all 3' in menu['hint']


# ------------------------------------------------------------------------ A2

@pytest.mark.parametrize('venom', ['hydras_blood', 'upas_latex', 'eitr_venom', 'viper_venom'])
def test_a2_the_card_names_both_limits(venom):
    lore = _data('items', 'flask.json')[venom]['lore']
    assert 'no blood' in lore
    assert 'proof against poison' in lore or 'live upon venom' in lore
    assert 'long shrug it off' not in lore


# ------------------------------------------------------------------------ A4

@pytest.mark.parametrize('dropped_first', [True, False])
def test_a4_an_overflow_never_joins_what_he_set_down(dropped_first):
    from items import GoldPile, add_gold_to_tile
    g = _scene(('myrmekes', 2, 0))
    g.ground_items = []
    g.player_gold = 300
    p = g.player
    if dropped_first:
        g._drop_gold(5)
    add_gold_to_tile(g.ground_items, 4000, p.x, p.y, found=False)      # an overflow, a thief's return
    if not dropped_first:
        g._drop_gold(5)
    g._lore_powers_before(g.monsters[0])
    assert [i.amount for i in g.ground_items if isinstance(i, GoldPile)] == [4000]


# ------------------------------------------------------------------------ A6

def test_a6_a_great_foe_may_tear_free_as_it_does_from_the_cast():
    import hazards
    g = _scene(('kobold', 2, 0))
    m = g.monsters[0]
    asked = []
    g._inflict = lambda *a, **k: (asked.append(a[1]), (0, ''))[1]
    g._hazard_hit_monster(m, hazards.hazard_def('conjured_vine'))
    assert asked == ['immobilized'] and not m.has_effect('immobilized')
    assert 'hold it fast' not in ' '.join(_msgs(g, 2)) and 'hold him fast' not in ' '.join(_msgs(g, 2))


def test_a6_an_ordinary_foe_is_always_held():
    import hazards
    g = _scene(('kobold', 2, 0))
    m = g.monsters[0]
    g._hazard_hit_monster(m, hazards.hazard_def('conjured_vine'))
    assert m.has_effect('immobilized') and 'fast' in ' '.join(_msgs(g, 2))


@pytest.mark.parametrize('held', [False, True])
def test_a6_one_who_saves_is_not_told_he_is_held(held, monkeypatch):
    import decor
    import status_effects
    g = _scene()
    at = (g.player.x, g.player.y)
    decor.place_for(g.dungeon, at, 'conjured_vine', 99)
    monkeypatch.setattr(status_effects, 'apply_debuff_with_save',
                        lambda *a, **k: (held, 'It takes hold.' if held else 'You throw off the grip!'))
    g._hazard_step_hero(*at)
    said = ' '.join(_msgs(g, 3))
    assert ('hold you fast' in said) is held


def test_a6_the_card_names_both_ways_out():
    from spells import LEARNABLE_SPELLS
    desc = LEARNABLE_SPELLS['dionysus_vine_spell']['desc']
    assert 'you may save' in desc.lower() and 'break free' in desc


# ------------------------------------------------------------------------ A7

@pytest.mark.parametrize('turns', [3, 20, 60])
def test_a7_a_second_shield_never_shortens_the_eighty(turns):
    from player import Player
    p = Player()
    p.add_effect('shielded', 80, cap=80)
    p.add_effect('shielded', turns)
    assert p.status_effects['shielded'] == 80


def test_a7_a_second_shield_does_not_lengthen_it_either():
    from player import Player
    p = Player()
    p.add_effect('shielded', 50)
    p.add_effect('shielded', 50)
    assert p.status_effects['shielded'] == 60


# ------------------------------------------------------------------------ B1

def test_b1_the_lore_is_true_of_the_swords_that_thrust():
    import combat
    import splitting
    from items import instantiate_weapon
    sword = instantiate_weapon('longsword', 'steel')
    m = _mk('ochre_jelly', 5, 5)
    m.max_hp = m.hp = 200
    m._incoming_forms = combat.blow_forms_of(sword)
    assert not splitting.blow_splits(m, 10, 'physical')         # it thrusts, as into a pudding
    assert 'a blade that can only cut' in MONS['ochre_jelly']['lore']


# ------------------------------------------------------------------------ B5

def test_b5_a_saved_crypt_things_old_attack_still_has_its_verb():
    import monster
    assert monster._attack_verb({'name': 'Teleport'}) == 'bewilders'


# ------------------------------------------------------------------------ B6

def test_b6_the_blink_dog_does_not_blink_through_a_wall(monkeypatch):
    from dungeon import WALL
    g = _scene(('blink_dog', 5, 0))
    m = g.monsters[0]
    m.speed = 10
    m._tracking = True
    x = g.player.x + 2
    for y in range(g.player.y - 7, g.player.y + 8):
        g.dungeon.tiles[y][x] = WALL
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    monkeypatch.setattr(m, '_spots_player', lambda *a, **k: True)        # its nose has him
    for _ in range(3):
        m.take_turn(g.player, g.dungeon, g.monsters)
    assert m.x > x


def test_b6_short_of_gold_d_still_opens_drop():
    g = _scene(('xorn', 3, 0))
    m = g.monsters[0]
    m._tracking = True
    g.player_gold = 0
    g.player.inventory = []
    g._lore_powers_parley_tick(m)
    assert g._parley_offer() is False
    assert 'you have not' in ' '.join(_msgs(g, 2))


# -------------------------------------------------------------------- B6, B7

PARLEYS = ['xorn', 'sphinx', 'sphinx_lesser']


@pytest.mark.parametrize('kind', PARLEYS)
def test_b7_struck_first_it_never_offers_a_parley(kind):
    import lore_powers
    g = _scene((kind, 1, 0))
    m = g.monsters[0]
    m.max_hp = m.hp = 9000
    g._damage_by = 'hero'
    m.take_damage(50)
    m._tracking = True
    assert not lore_powers.calls(m, g.player, g.dungeon, g.monsters)
    g._lore_powers_parley_tick(m)
    assert m.__dict__.get('_lp_parley') == 'angry'


@pytest.mark.parametrize('mark', ['_struck', '_opened'])
@pytest.mark.parametrize('kind', PARLEYS)
def test_b7_one_already_fighting_in_a_save_does_not_stop_to_parley(kind, mark):
    import lore_powers
    g = _scene((kind, 2, 0))
    m = g.monsters[0]
    m.__dict__[mark] = True
    m._tracking = True
    assert not lore_powers.calls(m, g.player, g.dungeon, g.monsters)
    g._lore_powers_parley_tick(m)
    assert m.__dict__.get('_lp_parley') == 'angry'


@pytest.mark.parametrize('state', ['waiting', 'calm'])
def test_b7_poison_he_lays_breaks_the_peace(state):
    g = _scene(('sphinx', 3, 0))
    m = g.monsters[0]
    m.resistances = []
    m._lp_parley = state
    if state == 'calm':
        m._lp_calm = True
    got = g._inflict(m, 'poisoned', 8, roll=False)[0]
    assert got and m._lp_parley == 'angry' and not m.__dict__.get('_lp_calm')


def test_b7_a_poison_that_never_took_breaks_nothing():
    g = _scene(('xorn', 3, 0))
    m = g.monsters[0]
    m._lp_parley, m._lp_calm = 'calm', True
    assert not g._inflict(m, 'poisoned', 8, roll=False)[0]
    assert m._lp_calm


# ----------------------------------------------------------------------- B12

def test_b12_the_tell_says_what_breaking_it_does():
    import tells
    assert 'falls still' in tells.parts(_mk('ushabti_overseer', 5, 5), 'summon_kind')[2]
    assert 'falls still' not in tells.parts(_mk('imp_lord', 5, 5), 'summon_kind')[2]


def test_b12_an_overseer_turned_into_something_else_holds_no_workers():
    import game_magic
    g = _scene(('ushabti_overseer', 3, 0), ('ushabti_worker', 2, 1))
    boss, worker = g.monsters
    worker._summoned_by = boss
    game_magic._polymorph_swap(g, boss, _mk('giant_rat', boss.x, boss.y))
    assert not worker.alive


# ------------------------------------------------------------------------ C1

def test_c1_the_kit_row_names_the_statuses():
    g = _scene()
    row = g._get_item_stats_brief(_item('accessory', 'sailors_amulet'))
    assert 'cold_resist' not in row and 'Cold Resist and Warning' in row


# -------------------------------------------------------------------- C1, C14

def test_c1_a_timed_warning_does_not_cost_an_old_save_the_amulets():
    import gear_saves
    from player import Player
    p = Player()
    amulet = _item('accessory', 'sailors_amulet')
    amulet.effects = {'status': 'cold_resist', 'duration': -1}
    p.amulet_slot = amulet
    p.status_effects.update(cold_resist=-1, warning=8)
    gear_saves.migrate(p, [amulet])
    assert p.status_effects['warning'] == -1


def test_c14_a_timed_resistance_does_not_cost_an_old_save_the_swords():
    import gear_saves
    from player import Player
    p = Player()
    sword = _item('weapon', 'shamshir_e_zomorrodnegar')
    sword.on_equip_status = ''
    p.weapon = sword
    p.status_effects['magic_resist'] = 10
    gear_saves.migrate(p, [sword])
    assert p.status_effects['magic_resist'] == -1


# ------------------------------------------------------------------------ C8

def test_c8_a_zombie_performer_is_spared_but_no_innocent():
    import monster
    z = types.SimpleNamespace(is_allied=True, is_sk_zombie=True)
    assert monster.is_bystander(z) and not monster.is_innocent(z)


# ------------------------------------------------------------------------ C9

def test_c9_an_unknown_blade_is_named_in_a_sentence(monkeypatch):
    g = _scene(('kobold', 1, 0))
    m = g.monsters[0]
    m.max_hp = m.hp = 5000
    w = _item('weapon', 'kladenets')
    w.id_level = 0
    g.player.known_item_ids.discard('kladenets')
    g.player.weapon = w
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    g._self_swing(m)
    said = ' '.join(_msgs(g, 2))
    assert 'swings of itself' in said and 'Your A ' not in said


def test_a6_the_vines_line_fills_the_pronoun_in():
    import hazards
    g = _scene(('kobold', 2, 0))
    g._hazard_hit_monster(g.monsters[0], hazards.hazard_def('conjured_vine'))
    said = ' '.join(_msgs(g, 2))
    assert 'vines wind round' in said and '{' not in said


def test_b7_a_vents_blow_does_not_cost_him_the_parley():
    """Only the hero's blow or his pet's ends a parley."""
    import lore_powers
    g = _scene(('sphinx', 2, 0))
    m = g.monsters[0]
    m.max_hp = m.hp = 9000
    g._damage_by = 'hazard'
    m.take_damage(50)
    g._damage_by = 'hero'
    m._tracking = True
    assert lore_powers.calls(m, g.player, g.dungeon, g.monsters)
