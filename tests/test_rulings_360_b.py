"""Brandon's rulings on the 3.6.0 bug bash, group B (2026-11-22: "All as
recommended"): monsters that are what their lore says.

  B1   the Ochre Jelly divides under an edge or lightning
  B3   the Grick's hide turns blade and point
  B5   the Crypt Thing's attack is no longer called Teleport (the real
       teleport is for later)
  B6   the Blink Dog blinks; the Xorn bargains for gold or treasure
  B7   both Sphinxes ask one philosophy question
  B8   the Redcap is weak to holy
  B10  the Shadow Assassin and Shadow Archer are weak to holy
  B12  the Ushabti Overseer's workers fall still with it
  B13  one of the two skeleton archers is the Skeleton Bowman

Logic tests on a headless Game. How these fights read is a play-test's to
judge.
"""
from __future__ import annotations

import json
import os
import random
import types

import pygame
import pytest

from test_bugbash_360_monsters import MONS, _mk, _msgs, _scene

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def _data(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


# ------------------------------------------------------------------------ B1

@pytest.mark.parametrize('form', ['slash', 'lightning'])
def test_b1_an_edge_or_a_bolt_divides_the_ochre_jelly(form):
    import splitting
    m = _mk('ochre_jelly', 5, 5)
    m.max_hp = m.hp = 200
    assert splitting.blow_splits(m, 10, form)


def test_b1_fire_does_not_divide_it():
    import splitting
    m = _mk('ochre_jelly', 5, 5)
    m.max_hp = m.hp = 200
    assert isinstance(MONS['ochre_jelly'].get('splits'), dict)
    assert not splitting.blow_splits(m, 10, 'fire')


def test_b1_the_edge_is_no_longer_resisted_and_the_lore_says_it_divides():
    d = MONS['ochre_jelly']
    assert 'slash' not in d['resistances'] and 'lightning' in d['resistances']
    assert 'only divides it' in d['lore']


# ------------------------------------------------------------------------ B3

def test_b3_the_gricks_hide_turns_blade_and_point():
    d = MONS['grick']
    assert {'slash', 'pierce'} <= set(d['resistances'])
    assert 'blunt' not in d['resistances'] and 'magic' in d['weaknesses']
    assert 'takes little hurt' in d['lore']


# ------------------------------------------------------------------------ B5

def test_b5_the_crypt_things_attack_no_longer_says_teleport():
    import monster
    names = [a['name'] for a in MONS['crypt_thing']['attacks']]
    assert names == ['Bewilder', 'Claw']
    assert 'Teleport' not in _data('combat_lines.json')['attack_verbs']
    m = _mk('crypt_thing', 5, 5)
    assert monster._attack_verb(m.attacks[0]) == 'bewilders'
    assert m.attacks[0]['effect'] == 'confused'


# ------------------------------------------------------------------------ B6

def test_b6_the_blink_dog_blinks_in_beside_him_and_bites(monkeypatch):
    g = _scene(('blink_dog', 5, 0))
    m = g.monsters[0]
    m.speed = 10
    m._tracking = True
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    assert m.take_turn(g.player, g.dungeon, g.monsters)
    assert max(abs(m.x - g.player.x), abs(m.y - g.player.y)) == 1


def test_b6_the_blink_dogs_words_are_true_again():
    d = MONS['blink_dog']
    assert d['can_phase_blink'] and 0 < d['phase_blink_chance'] <= 0.3
    assert 'leap a short way in an instant' in d['lore']
    assert 'blink' in _data('items', 'ingredient.json')['blink_dog_prime']['description'].split(',')[1]


def _bargain(gold):
    g = _scene(('xorn', 3, 0))
    m = g.monsters[0]
    m._tracking = True
    g.player_gold = gold
    g.player.inventory = []
    g._lore_powers_parley_tick(m)
    return g, m


def test_b6_a_xorn_calls_for_gold_before_it_fights():
    g = _scene(('xorn', 4, 0))
    m = g.monsters[0]
    m._aware = False
    m.speed = 10
    m.perception_range = 10
    struck = []
    m.attack = lambda p: (struck.append(1), (0, ''))[1]
    g._advance_turn()
    assert m.__dict__.get('_lp_parley') == 'waiting' and not struck
    said = ' '.join(_msgs(g, 12))
    assert 'gold' in said and 'Press D' in said and 'answer' not in said


def _pick(g, key):
    g._ask_input(getattr(pygame, f'K_{key.lower()}'))


def test_b6_gold_paid_it_lets_him_be():
    import economy
    g, m = _bargain(100_000)
    g._advance_turn = lambda: None
    assert g._parley_offer() and g._ask_data
    _pick(g, 'P')
    paid = 100_000 - g.player_gold
    income = economy.roll_share(random, g.dungeon_level, (1.0, 1.0))
    assert 0 < paid <= max(1, income * 2)
    assert m.__dict__.get('_lp_calm')
    import lore_powers
    assert lore_powers.holds_fire(m)


def test_b6_its_price_is_set_once():
    g, m = _bargain(100_000)
    g._parley_offer()
    first = m.__dict__['_lp_toll']
    g._ask_input(pygame.K_ESCAPE)
    assert m.__dict__['_lp_parley'] == 'waiting' and g.player_gold == 100_000
    g._parley_offer()
    assert m.__dict__['_lp_toll'] == first


def test_b6_refused_it_fights():
    g, m = _bargain(100_000)
    g._advance_turn = lambda: None
    g._parley_offer()
    _pick(g, 'R')
    assert g.player_gold == 100_000 and m.__dict__['_lp_parley'] == 'angry'


def test_b6_with_too_little_nothing_is_taken():
    g, m = _bargain(0)
    assert g._parley_offer()
    assert not getattr(g, '_ask_data', None) and not m.__dict__.get('_lp_calm')
    assert 'you have not' in ' '.join(_msgs(g, 3))


def test_b6_his_blow_breaks_the_bargain(monkeypatch):
    import lore_powers
    g, m = _bargain(100_000)
    g._advance_turn = lambda: None
    g._parley_offer()
    _pick(g, 'P')
    monkeypatch.setattr(lore_powers, '_striker', lambda: 'hero')
    lore_powers.after_damage(m, 5)
    assert not m.__dict__.get('_lp_calm') and m.__dict__['_lp_parley'] == 'angry'


def test_b6_the_xorns_bargain_is_told_and_walls_stay_legend():
    d = MONS['xorn']
    assert 'gladly parley' in d['lore'] and 'passes through' not in d['lore']
    assert not d.get('can_phase_walls')


# ------------------------------------------------------------------------ B7

SPHINXES = [('sphinx', 2), ('sphinx_lesser', 3)]


@pytest.mark.parametrize('kind,tier', SPHINXES)
def test_b7_a_sphinx_asks_one_philosophy_question(kind, tier):
    g = _scene((kind, 3, 0))
    m = g.monsters[0]
    m._tracking = True
    g._lore_powers_parley_tick(m)
    assert m.__dict__.get('_lp_parley') == 'waiting'
    asked = {}
    g.quiz_engine.start_quiz = lambda **kw: asked.update(kw)
    g._advance_turn = lambda: None
    assert g._parley_offer()
    assert (asked['subject'], asked['tier'], asked['total_qs']) == ('philosophy', tier, 1)
    asked['callback'](types.SimpleNamespace(success=True))
    assert m.__dict__.get('_lp_calm')


@pytest.mark.parametrize('kind,_tier', SPHINXES)
def test_b7_a_poor_answer_brings_the_riddle_curse(kind, _tier):
    g = _scene((kind, 3, 0))
    m = g.monsters[0]
    m._tracking = True
    g._lore_powers_parley_tick(m)
    asked = {}
    g.quiz_engine.start_quiz = lambda **kw: asked.update(kw)
    g._advance_turn = lambda: None
    g._parley_offer()
    asked['callback'](types.SimpleNamespace(success=False))
    assert m.__dict__['_lp_parley'] == 'angry' and m._opener_now['name'] == 'Riddle Curse'


@pytest.mark.parametrize('dist', [1, 2, 3, 5])
@pytest.mark.parametrize('kind,_tier', SPHINXES)
def test_b7_she_calls_before_she_strikes(kind, _tier, dist):
    g = _scene((kind, dist, 0))
    m = g.monsters[0]
    # The Sphinx lies in wait and calls as he comes near (spring_reach 2), or
    # from farther off once he has spotted her.
    import surprise
    m._aware = MONS[kind]['ai_pattern'] == 'ambush' and dist > surprise.spring_reach()
    m.speed = 10
    m.perception_range = 10
    struck = []
    m.attack = lambda p: (struck.append(1), (0, ''))[1]
    for _ in range(3):
        g._advance_turn()
    assert m.__dict__.get('_lp_parley') == 'waiting' and not struck
    assert not m.__dict__.get('_mimic_surprise'), 'one that calls out is no surprise'


def test_b7_the_hidden_sphinx_strikes_no_one_from_afar():
    g = _scene(('sphinx', 5, 0))
    m = g.monsters[0]
    m._aware = False
    struck = []
    m.attack = lambda p: (struck.append(1), (0, ''))[1]
    for _ in range(3):
        g._advance_turn()
    assert not struck and not m.__dict__.get('_lp_parley')


@pytest.mark.parametrize('kind', ['sphinx', 'sphinx_lesser', 'xorn'])
def test_b7_the_tell_is_its_own_and_not_the_blue_mens(kind):
    import tells
    said = ' '.join(tells.parts(_mk(kind, 5, 5), 'parley'))
    assert 'water' not in said and 'verse' not in said
    assert ('gold' if kind == 'xorn' else 'philosophy') in said


def test_b7_the_blue_mens_tell_is_as_it_was():
    import tells
    said = ' '.join(tells.parts(_mk('blue_men_of_the_minch', 5, 5), 'parley'))
    assert 'water' in said and 'verse' in said


def test_b7_the_lore_promises_the_riddle_again():
    assert 'attempting her puzzle' in MONS['sphinx']['lore']
    assert 'ask her riddle only once' in MONS['sphinx_lesser']['lore']
    assert 'ask riddles' in _data('items', 'ingredient.json')['sphinx_prime']['description']


# ------------------------------------------------------------------- B8, B10

@pytest.mark.parametrize('kind', ['redcap', 'shadow_assassin', 'shadow_archer'])
def test_b8_b10_holy_power_burns_them(kind):
    assert 'holy' in MONS[kind]['weaknesses']
    assert kind in _data('family_affinity.json')['unholy']['cursed']
    assert 'holy' in MONS[kind]['lore']


def test_b10_the_void_wyrm_is_left():
    assert 'holy' not in MONS['void_wyrm']['weaknesses']


# ----------------------------------------------------------------------- B12

def _gang():
    g = _scene(('ushabti_overseer', 3, 0), ('ushabti_worker', 2, 1),
               ('ushabti_worker', 2, -1), ('ushabti_worker', 4, 2))
    boss, a, b, loose = g.monsters
    a._summoned_by = b._summoned_by = boss
    return g, boss, (a, b), loose


def test_b12_the_workers_it_called_fall_still_with_it():
    g, boss, called, loose = _gang()
    g.ground_items = []
    before = g.level_mgr.monsters_killed
    boss.hp, boss.alive = 0, False
    g._on_monster_killed(boss)
    assert not any(w.alive for w in called) and loose.alive
    assert g.level_mgr.monsters_killed == before + 1, 'no kill for the workers'
    from items import Corpse
    assert not [i for i in g.ground_items
                if isinstance(i, Corpse) and i.monster_id == 'ushabti_worker']
    assert any('fall still' in t for t in _msgs(g, 20))
    g._reap_unnoticed_kills()
    assert g.level_mgr.monsters_killed == before + 1


def test_b12_no_other_summoners_creatures_fall():
    g, boss, called, _loose = _gang()
    boss.kind = 'imp_lord'
    boss.hp, boss.alive = 0, False
    g._on_monster_killed(boss)
    assert all(w.alive for w in called)


def test_b12_the_lore_says_they_fall_quiet():
    assert 'fall quiet' in MONS['ushabti_overseer']['lore']


# ----------------------------------------------------------------------- B13

def test_b13_the_skeleton_bowman_has_a_name_of_its_own():
    assert MONS['skeletal_archer']['name'].lower() == 'skeleton bowman'
    assert 'skeletal archer' not in MONS['skeletal_archer']['lore'].lower()
    names = [str(v.get('name', '')).lower() for v in MONS.values() if isinstance(v, dict)]
    assert names.count('skeleton bowman') == 1
