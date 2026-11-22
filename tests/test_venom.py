"""Poison (Brandon, 2026-11-22: "two damage? why have these cure poison
potions... I think this is still rotated too weak"): each venom its own
strength by lore, doses that add a little, a CON save that halves, the
venom to come shown, cures worth carrying (src/venom.py)."""
import json
import os
import random
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import status_effects as S  # noqa: E402
import venom  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _hero(hp=100, con=10):
    p = Player()
    p.max_hp = p.hp = hp
    p.CON = con
    return p


def _bite(p, v, turns=6, dc=99, source=None):
    return S.apply_debuff_with_save(p, 'poisoned', turns, dc, source=source, venom=v)


def _poison_attacks():
    for kind, m in MONS.items():
        if isinstance(m, dict):
            for a in m.get('attacks') or ():
                if a.get('effect') == 'poisoned':
                    yield kind, m, a


# ---------------------------------------------------------------------------
# The data: every venom by lore, written once
# ---------------------------------------------------------------------------

def test_every_poison_attack_has_its_venom():
    seen = 0
    for kind, _m, a in _poison_attacks():
        seen += 1
        assert isinstance(a.get('venom'), int) and a['venom'] >= 1, (kind, a['name'])
    assert seen >= 80


def test_the_first_floors_venoms_stay_at_one():
    for kind, m, a in _poison_attacks():
        if (m.get('peak_weight') or 0) > 0 and max(int(m.get('min_level', 1)),
                                                     int(m.get('peak_floor', m.get('min_level', 1)))) <= 5:
            assert a['venom'] == 1, (kind, a['name'], a['venom'])


def test_the_deadly_venoms_bite_harder_than_the_mild_at_the_same_depth():
    import poison_pass_2026_11_22 as pp
    hydra = pp.VENOM[('hydra', 'Many-Headed Bite')]
    devil = pp.VENOM[('bearded_devil', 'Beard Barbs')]
    assert hydra[1] == 'deadly' and devil[1] == 'mild' and hydra[0] > devil[0]


def test_the_poison_pass_has_no_drift():
    import poison_pass_2026_11_22 as pp
    assert pp.run(check=True) == []


def test_what_is_not_venom_lays_something_else():
    def rider(kind, name):
        return next(a for a in MONS[kind]['attacks'] if a['name'] == name).get('effect')
    assert rider('rotting_zombie', 'Claw') is None
    assert rider('plague_zombie', 'Claw') == 'diseased'
    assert rider('green_slime', 'Drip') == 'corroding'


# ---------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------

def test_a_bite_does_its_venom_a_turn():
    p = _hero(hp=100)
    _bite(p, 3, turns=6)
    hp = p.hp
    S.tick_all(p)
    assert hp - p.hp == 3


def test_a_poison_with_no_venom_keeps_the_old_share():
    p = _hero(hp=100)
    p.add_effect('poisoned', 5)
    assert venom.strength(p) == S.dot_tick(p) == 2


def test_doses_add_half_never_past_one_and_a_half():
    p = _hero()
    _bite(p, 2, turns=6)
    assert p.status_effects['poisoned'] == 6
    _bite(p, 2, turns=6)
    assert p.status_effects['poisoned'] == 9
    for _ in range(10):
        _bite(p, 2, turns=6)
    assert p.status_effects['poisoned'] == 9


def test_the_strongest_venom_sets_the_tick():
    p = _hero()
    _bite(p, 2, turns=6)
    _bite(p, 5, turns=4)
    assert venom.strength(p) == 5
    _bite(p, 1, turns=4)
    assert venom.strength(p) == 5


def test_a_new_bout_starts_afresh():
    p = _hero()
    _bite(p, 5, turns=2)
    while p.status_effects.get('poisoned'):
        S.tick_all(p)
    p.add_effect('poisoned', 3)
    assert venom.strength(p) == S.dot_tick(p)


@pytest.mark.parametrize('saved', (True, False))
def test_a_hardy_body_throws_off_half(monkeypatch, saved):
    monkeypatch.setattr(random, 'randint', lambda a, b: 20 if saved else 1)
    p = _hero()
    ok, line = _bite(p, 3, turns=6, dc=12)
    assert ok and p.status_effects['poisoned'] == (3 if saved else 6)
    assert ('throws off half' in line) is saved


def test_a_venom_ward_halves_strength_and_turns():
    p = _hero()
    p.add_effect('venom_ward', 100)
    _bite(p, 5, turns=6)
    assert p.status_effects['poisoned'] == 3 and venom.strength(p) == 3


def test_poison_resist_keeps_it_off_whole():
    p = _hero()
    p.add_effect('poison_resist', 50)
    ok, _ = _bite(p, 5, turns=6)
    assert venom.to_come(p) == 0


def test_what_is_to_come_is_shown_and_warns():
    p = _hero(hp=100)
    _bite(p, 4, turns=6)
    assert venom.to_come(p) == 24
    assert venom.chip(p) == 'Poisoned: 24 to come'
    p.hp = 20
    assert venom.deadly(p) and venom.chip(p) == 'Poisoned: 24 to come'
    assert 'kill you' in venom.warn_once(p) and venom.warn_once(p) == ""


def test_to_come_counts_toughness():
    p = _hero(hp=100, con=30)        # 20% toughness
    _bite(p, 10, turns=5)
    assert venom.per_turn(p) == 8 and venom.to_come(p) == 40
    hp = p.hp
    while p.status_effects.get('poisoned'):
        S.tick_all(p)
    assert hp - p.hp == 40


def test_the_bite_names_its_maker_and_the_toll():
    p = _hero(hp=100)
    m = Monster({**MONS['ettercap'], 'id': 'ettercap'}, 1, 1)
    ok, line = _bite(p, 3, turns=6, source=m)
    assert ok and "venom is in you: 18 to come" in line


def test_a_monster_blow_passes_its_venom(monkeypatch):
    m = Monster({**MONS['ettercap'], 'id': 'ettercap'}, 1, 1)
    atk = next(a for a in m.attacks if a.get('effect') == 'poisoned')
    m.attacks = [atk]               # its bite alone (which it picks is the random stream's)
    p = _hero(hp=100)
    p.get_ac = lambda: 10
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    monkeypatch.setattr(random, 'randint', lambda a, b: b)
    for _ in range(4):
        m.attack(p)
        if p.status_effects.get('poisoned'):
            break
    assert venom.strength(p) == atk['venom']


def test_an_older_saves_monster_takes_its_venom():
    import effect_rules
    m = Monster({**MONS['ettercap'], 'id': 'ettercap'}, 1, 1)
    m.__dict__['_effects_pass'] = 1
    for a in m.attacks:
        a.pop('venom', None)
    assert effect_rules.refresh_monster(m)
    assert next(a for a in m.attacks if a.get('effect') == 'poisoned')['venom'] >= 1


# ---------------------------------------------------------------------------
# Cures worth carrying
# ---------------------------------------------------------------------------

def test_every_stall_of_floors_two_to_twenty_sells_the_cure():
    import traders
    for defn in traders.data()['traders'].values():
        for floor in (2, 11, 20):
            stock = traders.build_stock(defn, floor, random.Random(floor))
            assert any(getattr(i, 'id', '') == 'potion_of_cure_poison' for i in stock), floor
            ware = next(i for i in stock if getattr(i, 'id', '') == 'potion_of_cure_poison')
            assert not getattr(ware, '_counter', None)        # unmarked, as every potion


def test_the_apothecary_always_has_it():
    import traders
    defn = traders.data()['traders']['apothecary']
    for seed in range(8):
        stock = traders.build_stock(defn, 30, random.Random(seed))
        assert any(getattr(i, 'id', '') == 'potion_of_cure_poison' for i in stock), seed


def test_the_cure_saves_more_than_a_heal_potion_costs_more():
    """One bite of an ordinary venom costs about a fifth of the hero's HP:
    the cure saves that, for less than a healing potion costs."""
    import economy
    from items import make_item_by_id
    cure = make_item_by_id('potion', 'potion_of_cure_poison')
    heal = make_item_by_id('potion', 'potion_of_healing')
    assert economy.merchant_price(cure, 10) < economy.merchant_price(heal, 10)


def test_a_prayer_of_four_lifts_the_venom():
    import game_divine
    from test_prayer import _make_prayer_game
    g = _make_prayer_game(karma=0, at_altar=False)
    g.player.add_effect('poisoned', 6)
    game_divine.DivineMixin._resolve_simple_prayer(g, 4, False)
    assert not g.player.has_effect('poisoned')
