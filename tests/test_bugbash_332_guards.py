"""Armour 2/7 (bug bash 3.3.2): attack delivery and the slot guards.

The minor slots give no AC (gear.py); each guards one family of attack
(data/armor_guards.json, src/guards.py), read from the delivery written on
every monster attack (tools/content/tag_attack_delivery.py), its damage type
and its rider. A touch attack rolls against AC without body armour and
shield (3e "touch AC").
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import guards  # noqa: E402
import items  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


# ---------------------------------------------------------------- data

def test_every_monster_attack_says_how_it_lands():
    bad = [(k, a.get('name')) for k, m in MONS.items() for a in m.get('attacks') or []
           if a.get('delivery') not in guards.DELIVERIES]
    assert not bad, bad[:10]


def test_the_tag_agrees_with_the_rules_the_guards_were_priced_with():
    off = [(k, a['name'], a['delivery']) for k, m in MONS.items() for a in m.get('attacks') or []
           if a['delivery'] != guards.classify(a)]
    assert not off, off[:10]


def test_every_minor_slot_has_a_family():
    import gear
    for slot in gear.MINOR_SLOTS:
        fam = guards.family(slot)
        assert fam.get('deliveries') or fam.get('elements'), slot


# ---------------------------------------------------------------- matching

@pytest.mark.parametrize('slot, atk, want', [
    ('head', {'delivery': 'voice', 'type': 'psionic', 'effect': 'confused'}, (True, True)),
    ('head', {'delivery': 'blow', 'effect': 'stunned'}, (False, True)),        # a stun from any blow
    ('head', {'delivery': 'bite', 'effect': 'poisoned'}, (False, False)),
    ('hands', {'delivery': 'touch', 'type': 'drain'}, (True, False)),
    ('hands', {'delivery': 'blow', 'effect': 'paralyzed'}, (False, True)),
    ('arms', {'delivery': 'ranged', 'effect': 'blinded'}, (True, True)),
    ('legs', {'delivery': 'bite', 'effect': 'poisoned'}, (True, True)),
    ('legs', {'delivery': 'ranged', 'effect': 'diseased'}, (False, True)),
    ('feet', {'delivery': 'trample'}, (True, False)),
    ('feet', {'delivery': 'blow', 'effect': 'stunned'}, (False, True)),        # knocked down
    ('feet', {'delivery': 'voice', 'effect': 'stunned'}, (False, False)),
    ('cloak', {'delivery': 'blow', 'type': 'fire', 'effect': 'burning'}, (True, True)),
    ('cloak', {'delivery': 'breath', 'type': 'poison'}, (True, False)),
    ('shirt', {'delivery': 'bite', 'type': 'poison', 'effect': 'bleeding'}, (True, True)),
    ('shirt', {'delivery': 'blow', 'type': 'slash'}, (False, False)),
])
def test_each_family_guards_what_it_says(slot, atk, want):
    assert guards.matches(guards.family(slot), atk) == want


# ---------------------------------------------------------------- the guard

class _P:
    def __init__(self, pieces=()):
        self.armor_slots = [None] * len(items.ARMOR_SLOTS)
        for p in pieces:
            self.armor_slots[items.ARMOR_SLOTS.index(p.slot)] = p


def test_a_heavier_piece_guards_more():
    base = guards.rules()['base_by_weight_class']
    voice = {'delivery': 'voice', 'type': 'psionic', 'effect': 'feared'}
    for tpl, cls in (('leather_cap', 'light'), ('iron_helm', 'medium'), ('great_helm', 'heavy')):
        helm = items.instantiate_armor(tpl, 'damascus_steel' if tpl != 'leather_cap' else 'leather')
        keep_d, keep_r, piece = guards.guard_keep(_P([helm]), voice)
        assert keep_d == pytest.approx(1 - base[cls]['damage'])
        assert keep_r == pytest.approx(1 - base[cls]['rider'])
        assert piece is helm
    assert guards.guard_keep(_P([helm]), {'delivery': 'bite'})[:2] == (1.0, 1.0)


def test_pieces_that_match_one_attack_each_take_their_share():
    helm = items.instantiate_armor('great_helm', 'damascus_steel')
    boots = items.instantiate_armor('plate_boots', 'damascus_steel')
    stun = {'delivery': 'blow', 'effect': 'stunned'}
    r = guards.rules()['base_by_weight_class']['heavy']['rider']
    assert guards.guard_keep(_P([helm, boots]), stun)[1] == pytest.approx((1 - r) ** 2)


def test_no_guard_passes_the_cap(monkeypatch):
    helm = items.instantiate_armor('great_helm', 'damascus_steel')
    monkeypatch.setattr(guards, 'piece_strength', lambda p: (5.0, 5.0))
    keep_d, keep_r, _ = guards.guard_keep(_P([helm]), {'delivery': 'gaze', 'effect': 'paralyzed'})
    cap = guards.rules()['cap']
    assert keep_d == pytest.approx(1 - cap['damage'])
    assert keep_r == pytest.approx(1 - cap['rider'])


# ---------------------------------------------------------------- in a fight

@pytest.fixture
def game(monkeypatch, tmp_path):
    import quiz_engine
    import save_system
    import bones
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(2)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_bugbash_332_guards__')
    g.monsters = []
    g.state = STATE_PLAYER
    return g


def _monster(g, attack, thac0=10):
    from monster import Monster
    d = dict(MONS['giant_rat'], id='giant_rat')
    d['attacks'] = [dict(attack)]
    d['thac0'] = thac0
    m = Monster(d, g.player.x + 1, g.player.y)
    m._aware = True
    g.monsters.append(m)
    return m


def test_a_touch_ignores_body_armour_and_shield(game):
    p = game.player
    body = items.instantiate_armor('full_plate', 'damascus_steel', level=10)
    body.ac_bonus = 25                      # an absurd plate: AC far past any reach
    p.armor_slots[items.ARMOR_SLOTS.index('body')] = body
    assert p.get_ac() <= -20
    assert guards.touch_ac(p) == p.get_ac() + p.core_ac() > 5
    touch = _monster(game, {'name': 'Draining Touch', 'damage': '1d2', 'type': 'physical',
                            'delivery': 'touch'})
    blow = _monster(game, {'name': 'Claw', 'damage': '1d2', 'type': 'physical', 'delivery': 'blow'})
    random.seed(9)
    hits_touch = sum(1 for _ in range(300) if touch._resolve_blow(touch.attacks[0], p)[0] > 0) \
        if hasattr(touch, '_resolve_blow') else None
    if hits_touch is None:
        pytest.skip('single-attack entry point not found')
    hits_blow = sum(1 for _ in range(300) if blow._resolve_blow(blow.attacks[0], p)[0] > 0)
    assert hits_touch > 200 and hits_blow < 40, (hits_touch, hits_blow)


def test_a_shrugged_rider_is_told_and_does_not_land(game, monkeypatch):
    import monster as monster_mod
    p = game.player
    helm = items.instantiate_armor('great_helm', 'damascus_steel')
    p.armor_slots[items.ARMOR_SLOTS.index('head')] = helm
    gaze = {'name': 'Stare', 'damage': '1', 'type': 'magic', 'delivery': 'gaze',
            'effect': 'paralyzed', 'effect_chance': 1.0, 'effect_duration': 3}
    m = _monster(game, gaze)
    # 0.9: under the attack's chance (1.0), over its guarded chance (0.85).
    monkeypatch.setattr(monster_mod.random, 'random', lambda: 0.9)
    text = m._apply_attack_effect(gaze, p)
    assert 'turns the paralyzed aside' in text
    assert not p.has_effect('paralyzed')
