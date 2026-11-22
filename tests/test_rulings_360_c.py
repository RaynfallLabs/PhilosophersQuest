"""Brandon's rulings on the 3.6.0 bug bash, group C (2026-11-22: "All as
recommended"): items that do what their lore says.

  C1   the Sailor's Amulet senses danger as well as bearing cold
  C7   the Soul Reaver's dead "innocent" branch is gone
  C8   who is innocent is said in one place, and the Ring of Gyges uses it
  C9   the Samosek strikes back by itself, one blow taken in four
  C10  one Chandrahas is retired; old copies and old ids still work
  C11  Pandora's Box and Aladdin's Lamp are parked: nothing can grant one
  C12  the healing herb stops bleeding
  C14  the Shamshir-e Zomorrodnegar gives magic resistance in the hand
  C15  Omnisight shows blessed or cursed for everything on the floor, in the
       pack and worn

(C3 is for the ranger's arrow recovery.) Logic tests on a headless Game. How
a counter-stroke reads in play is a play-test's to judge.
"""
from __future__ import annotations

import json
import os
import random
import types

import pytest

from test_bugbash_360_monsters import _mk, _msgs, _scene

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def _data(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


def _src(name):
    with open(os.path.join(ROOT, 'src', name), encoding='utf-8') as f:
        return f.read()


def _item(cls, iid):
    import items
    it = items.make_item_by_id(cls, iid)
    it.buc, it.cursed = 'uncursed', False
    return it


def _hero():
    from player import Player
    return Player()


# ------------------------------------------------------------------------ C1

def test_c1_the_amulet_lends_both_senses_and_takes_both_away():
    p = _hero()
    p._apply_equip(_item('accessory', 'sailors_amulet'))
    assert p.has_effect('cold_resist') and p.has_effect('warning')
    other = next(k for k, v in _data('items', 'accessory.json').items()
                 if isinstance(v, dict) and v.get('slot') == 'amulet' and k != 'sailors_amulet'
                 and (v.get('effects') or {}).get('status') not in ('warning', 'cold_resist')
                 and not (v.get('effects') or {}).get('status2'))
    p._apply_equip(_item('accessory', other))
    assert not p.has_effect('cold_resist') and not p.has_effect('warning')


def test_c1_another_warning_worn_keeps_the_warning():
    p = _hero()
    amulet = _item('accessory', 'sailors_amulet')
    p._apply_equip(amulet)
    assert p._still_granted('warning', None)
    assert not p._still_granted('warning', amulet)


def test_c1_taken_off_by_hand_both_go():
    g = _scene()
    amulet = _item('accessory', 'sailors_amulet')
    g.player._apply_equip(amulet)
    g._take_off_now('amulet', amulet)
    assert g.player.amulet_slot is None
    assert not g.player.has_effect('cold_resist') and not g.player.has_effect('warning')


def test_c1_one_worn_in_an_old_save_gains_the_sense():
    import gear_saves
    p = _hero()
    amulet = _item('accessory', 'sailors_amulet')
    amulet.effects = {'status': 'cold_resist', 'duration': -1}
    p.amulet_slot = amulet
    p.status_effects['cold_resist'] = -1
    gear_saves.migrate(p, [amulet])
    assert p.has_effect('warning') and p.has_effect('cold_resist')


def test_c1_the_lore_and_the_source_line_say_it():
    assert 'feels trouble coming' in _data('items', 'accessory.json')['sailors_amulet']['lore']
    g = _scene()
    amulet = _item('accessory', 'sailors_amulet')
    g.player._apply_equip(amulet)
    assert 'Sailor' in g._get_effect_source('warning')


# ------------------------------------------------------------------------ C7

def test_c7_the_dead_branch_is_gone():
    assert 'growth_on_innocent_kill' not in _data('items', 'weapon.json')['soul_reaver']
    for f in ('combat.py', 'items.py'):
        assert 'growth_on_innocent_kill' not in _src(f), f


# ------------------------------------------------------------------------ C8

@pytest.mark.parametrize('mark', ['_npc_encounter_tag', '_flavor_encounter_tag', '_is_unicorn',
                                  'is_allied', 'is_escort'])
def test_c8_who_is_innocent_is_said_in_one_place(mark):
    import monster
    assert monster.is_innocent(types.SimpleNamespace(**{mark: True}))


def test_c8_a_foe_is_no_innocent():
    import monster
    assert not monster.is_innocent(_mk('kobold', 3, 3))


class _Quiz:
    def __init__(self, score):
        self.score = score

    def start_quiz(self, callback=None, **_kw):
        callback(types.SimpleNamespace(score=self.score, success=True))


def _gyges(score, monkeypatch, **marks):
    import combat
    import karma
    taken = []
    monkeypatch.setattr(karma, 'adjust', lambda g, n, **kw: taken.append(n))
    g = _scene()
    p = g.player
    p.accessory_slots[0] = _item('accessory', 'ring_of_gyges')
    p.status_effects['invisible'] = 20
    p._combat_game_ref = g
    m = _mk('giant_rat', p.x + 1, p.y)
    m.__dict__.update(marks)
    for _ in range(2):
        combat.player_attack(p, m, _Quiz(score), lambda *a, **k: None)
    return taken


@pytest.mark.parametrize('mark', ['is_allied', '_npc_encounter_tag', '_is_unicorn'])
def test_c8_the_ring_fires_on_an_innocent_whom_no_blow_can_hurt(mark, monkeypatch):
    assert _gyges(4, monkeypatch, **{mark: True}) == [-1]


def test_c8_a_whiff_is_no_wrong(monkeypatch):
    assert _gyges(0, monkeypatch, is_allied=True) == []


def test_c8_a_foe_costs_nothing(monkeypatch):
    assert _gyges(4, monkeypatch) == []


# ------------------------------------------------------------------------ C9

def _samosek(dx=1):
    g = _scene(('kobold', dx, 0))
    m = g.monsters[0]
    m.max_hp = m.hp = 5000
    g.player.weapon = _item('weapon', 'kladenets')
    return g, m


def test_c9_its_chance_is_one_in_four():
    d = _data('items', 'weapon.json')['kladenets']
    assert d['counter_attack_chance'] == 0.25 and '_note' not in d


def test_c9_it_swings_of_itself_at_the_one_who_struck_him(monkeypatch):
    g, m = _samosek()
    monkeypatch.setattr(random, 'random', lambda: 0.2)
    g._self_swing(m)
    assert m.hp < 5000 and 'swings of itself' in ' '.join(_msgs(g, 3))


def test_c9_three_times_in_four_it_does_not(monkeypatch):
    g, m = _samosek()
    monkeypatch.setattr(random, 'random', lambda: 0.3)
    g._self_swing(m)
    assert m.hp == 5000


def test_c9_it_cannot_reach_an_archer(monkeypatch):
    g, m = _samosek(dx=4)
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    g._self_swing(m)
    assert m.hp == 5000


def test_c9_no_other_sword_does(monkeypatch):
    g, m = _samosek()
    g.player.weapon = _item('weapon', 'shamshir_e_zomorrodnegar')
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    g._self_swing(m)
    assert m.hp == 5000


def test_c9_a_sword_from_an_old_save_does_too(monkeypatch):
    g, m = _samosek()
    g.player.weapon.counter_attack_chance = 0.0
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    g._self_swing(m)
    assert m.hp < 5000


@pytest.mark.parametrize('dmg,swings', [(5, 1), (0, 0)])
def test_c9_a_blow_taken_is_what_sets_it_off(dmg, swings):
    g, m = _samosek()
    m.speed = 10
    m.take_turn = lambda *a, **k: True
    m.attack = lambda p: (dmg, 'The Kobold hits you.')
    seen = []
    g._self_swing = lambda who: seen.append(who)
    g._do_monster_turns()
    assert len(seen) == swings


def test_c9_the_lore_says_it_fights_of_itself():
    lore = _data('items', 'weapon.json')['kladenets']['lore']
    assert 'fights of itself' in lore and 'in their tales' not in lore


# ----------------------------------------------------------------------- C10

def test_c10_one_chandrahas_is_left_the_one_with_the_legends_condition():
    w = _data('items', 'weapon.json')
    assert 'chandrahasa' not in w
    assert w['chandrahas']['karma_disappear_proc'] > 0


def test_c10_the_old_id_gives_the_one_that_stayed():
    assert _item('weapon', 'chandrahasa').id == 'chandrahas'


def test_c10_an_old_ghosts_sword_is_the_one_that_stayed():
    import items
    assert items.current_id('weapon', 'chandrahasa') == 'chandrahas'
    assert items.current_id('weapon', 'kladenets') == 'kladenets'
    assert 'current_id(' in _src('bones.py')


def test_c10_an_old_copy_keeps_its_own_power():
    import pickle

    from items import Weapon
    d = dict(_data('items', 'weapon.json')['chandrahas'], id='chandrahasa',
             low_hp_damage_bonus=True)
    old = pickle.loads(pickle.dumps(Weapon(d)))
    assert old.low_hp_damage_bonus and old.base_damage > 0
    g = _scene()
    g.player.inventory.append(old)
    assert g._display_name(old)


# ----------------------------------------------------------------------- C11

PARKED = ('pandoras_box', 'aladdins_lamp')


@pytest.mark.parametrize('iid', PARKED)
def test_c11_nothing_can_grant_a_parked_item(iid):
    import items
    assert _data('items', 'artifact.json')[iid]['parked'] is True
    assert items.make_item_by_id('artifact', iid) is None
    assert iid in items.scripted_only_ids()


# ----------------------------------------------------------------------- C12

def test_c12_the_herb_stops_bleeding():
    import food_system
    p = _hero()
    p.add_effect('bleeding', 8)
    said = ' '.join(food_system.eat_food(p, _item('food', 'healing_herb')))
    assert not p.has_effect('bleeding') and 'bleeding' in said


def test_c12_one_from_an_old_save_does_too():
    import food_system
    p = _hero()
    p.add_effect('bleeding', 8)
    herb = _item('food', 'healing_herb')
    herb.__dict__.pop('stops', None)
    food_system.eat_food(p, herb)
    assert not p.has_effect('bleeding')


def test_c12_bread_does_not():
    import food_system
    from items import Food
    p = _hero()
    p.add_effect('bleeding', 8)
    food_system.eat_food(p, Food({'id': 'plain', 'name': 'plain loaf', 'symbol': '%', 'color': [1, 1, 1], 'weight': 0.2, 'min_level': 1, 'hp_restore': 2}))
    assert p.has_effect('bleeding')


def test_c12_the_card_and_the_lore_say_so():
    g = _scene()
    assert 'stops bleeding' in g._food_restores_text(_item('food', 'healing_herb'))
    assert 'staunch bleeding' in _data('items', 'food.json')['healing_herb']['lore']


# ----------------------------------------------------------------------- C14

def test_c14_in_the_hand_it_guards_from_sorcery_and_out_of_it_does_not():
    p = _hero()
    p._apply_equip(_item('weapon', 'shamshir_e_zomorrodnegar'))
    assert p.has_effect('magic_resist')
    p._apply_equip(_item('weapon', 'kladenets'))
    assert not p.has_effect('magic_resist')


def test_c14_one_wielded_in_an_old_save_gains_it():
    import gear_saves
    p = _hero()
    sword = _item('weapon', 'shamshir_e_zomorrodnegar')
    sword.on_equip_status = ''
    p.weapon = sword
    gear_saves.migrate(p, [sword])
    assert sword.on_equip_status == 'magic_resist' and p.has_effect('magic_resist')


def test_c14_the_lore_says_so():
    assert 'sorcery' in _data('items', 'weapon.json')['shamshir_e_zomorrodnegar']['lore']


# ----------------------------------------------------------------------- C15

def _hidden(cls, iid):
    it = _item(cls, iid)
    it.buc, it.buc_known, it.id_level = 'uncursed', False, 0
    return it


def _all_about(g):
    p = g.player
    p.known_item_ids.clear()
    far = _hidden('potion', 'potion_of_regeneration')
    far.x, far.y = 1, 1
    g.ground_items = [far]
    g.visible = {(p.x, p.y)}
    pack = _hidden('weapon', 'kladenets')
    p.inventory = [pack]
    p.belt_slot = _hidden('accessory', next(
        k for k, v in _data('items', 'accessory.json').items()
        if isinstance(v, dict) and v.get('slot') == 'belt'))
    return far, pack, p.belt_slot


def test_c15_omnisight_sees_the_whole_floor_the_pack_and_the_belt():
    from spells import LEARNABLE_SPELLS
    g = _scene()
    three = _all_about(g)
    g._mm_acting(g._cast_spell_effect, LEARNABLE_SPELLS['omnisight_spell'], None)
    assert all(i.buc_known for i in three)


def test_c15_the_lesser_sights_are_as_they_were():
    from spells import LEARNABLE_SPELLS
    g = _scene()
    three = _all_about(g)
    for sid, sp in LEARNABLE_SPELLS.items():
        if sp.get('effect') == 'identify_item' and sp['tier'] < 5:
            g._mm_acting(g._cast_spell_effect, sp, None)
    assert not any(i.buc_known for i in three)


def test_c15_the_card_and_the_lore_say_everything():
    from spells import LEARNABLE_SPELLS
    desc = LEARNABLE_SPELLS['omnisight_spell']['desc']
    assert 'every item on the floor' in desc and 'but the belt' not in desc
    assert 'all things on the floor' in _data('items', 'spellbook.json')['spellbook_omnisight']['lore']
