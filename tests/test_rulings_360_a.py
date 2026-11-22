"""Brandon's rulings on the 3.6.0 bug bash, group A (2026-11-22: "All as
recommended").

  A1  traders buy lights, a bundle at a time, and no bundle makes money
  A2  a venom does nothing to what has no blood
  A4  the gold-digging ants take only gold the hero set down
  A5  a squeeze meets the hide, the material, the guards and the reflections
      an ordinary blow meets; still no dodge
  A6  Dionysus's Vine always takes hold: the saving throw is the way out
  A7  Absolute Ward lasts the 80 turns written

Logic tests on a headless Game. How a sale or a squeeze reads in play is a
play-test's to judge.
"""
from __future__ import annotations

import json
import os
import random

import pytest

from test_bugbash_360_monsters import MONS, _hold, _mk, _msgs, _scene
from test_traders import _game as _shop_game
from test_traders import _trader

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def _data(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


# ------------------------------------------------------------------------ A1

def _shop(kind='generalist'):
    g = _shop_game()
    g.player.inventory = []
    g.player_gold = 0
    m = _trader(g, kind)
    m.purse = 100_000
    return g, m


def _light(lid, n=1):
    import items
    it = items.make_item_by_id('light', lid)
    it.count, it.id_level = n, 5
    return it


def test_a1_a_bundle_of_torches_sells_whole_in_one_sale():
    g, m = _shop()
    stack = _light('torch', 6)
    g.player.inventory.append(stack)
    g.player.known_item_ids.add('torch')
    offer, why = g._trader_offer(stack)
    assert why is None and offer > 0
    g._trader_sell(stack)
    assert not any(i.id == 'torch' for i in g.player.inventory)
    assert 100_000 - m.purse == offer                # paid once, for all six


def test_a1_a_lantern_and_a_named_lamp_sell_where_lights_are_bought():
    import items
    g, _m = _shop()
    ids = ['horn_lantern'] + [k for k, v in _data('items', 'light.json').items()
                              if isinstance(v, dict) and v.get('is_unique')
                              and k not in items.scripted_only_ids()]
    for lid in ids:
        it = _light(lid)
        g.player.inventory.append(it)
        g.player.known_item_ids.add(lid)
        offer, why = g._trader_offer(it)
        assert why is None and offer > 0, (lid, why)


def test_a1_a_trader_who_does_not_deal_in_lights_says_so():
    g, _m = _shop('apothecary')
    torch = _light('torch')
    g.player.inventory.append(torch)
    assert "doesn't deal in that" in g._trader_offer(torch)[1]


@pytest.mark.parametrize('n', [1, 3, 6, 12])
def test_a1_torches_bought_never_sell_back_at_a_profit(n):
    import economy
    g, m = _shop()
    stack = _light('torch', n)
    paid = max(1, economy.merchant_price(stack, g.dungeon_level, m.markup))
    g.player.inventory.append(stack)
    g.player.known_item_ids.add('torch')
    g._trader_mark_bought(stack, {}, paid)
    got = 0
    for _ in range(n + 1):                           # press Sell till none are left
        row = next((i for i in g.player.inventory if i.id == 'torch'), None)
        if row is None:
            break
        purse = m.purse
        g._trader_sell(row)
        got += purse - m.purse
    assert not any(i.id == 'torch' for i in g.player.inventory)
    assert got <= paid / 2 + 1


# ------------------------------------------------------------------------ A2

VENOMS = [k for k, v in _data('items', 'flask.json').items()
          if isinstance(v, dict)
          and ((v.get('coat') or {}).get('rider') or {}).get('effect') == 'poisoned']


def _bloodless():
    """The kinds with no blood that nothing else already proofs against poison."""
    out = []
    for kind, d in sorted(MONS.items()):
        if 'poison' in d['resistances'] + d.get('shrugs_off', []) or 'poisoned' in d['status_immune']:
            continue
        if not _mk(kind, 0, 0).can_bleed():
            out.append(kind)
    return out


def test_a2_there_are_bloodless_kinds_to_protect():
    assert len(VENOMS) == 4 and len(_bloodless()) >= 10


@pytest.mark.parametrize('venom', VENOMS)
def test_a2_a_venom_does_nothing_to_what_has_no_blood(venom, monkeypatch):
    import coatings
    from items import instantiate_weapon, make_item_by_id
    from player import Player
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    poisoned = []
    for kind in _bloodless():
        p = Player()
        p.weapon = instantiate_weapon('longsword', 'steel')
        coatings.apply(p, make_item_by_id('flask', venom))
        m = _mk(kind, 0, 0)
        m.max_hp = m.hp = 500
        out = coatings.after_blow(p, m, p.weapon, 6)
        coatings.drain()
        if m.has_effect('poisoned') or not any('does nothing' in t for t, _k in out):
            poisoned.append(kind)
    assert not poisoned


def test_a2_the_living_are_still_poisoned(monkeypatch):
    import coatings
    from items import instantiate_weapon, make_item_by_id
    from player import Player
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    p = Player()
    p.weapon = instantiate_weapon('longsword', 'steel')
    coatings.apply(p, make_item_by_id('flask', 'viper_venom'))
    rat = _mk('giant_rat', 0, 0)
    rat.max_hp = rat.hp = 500
    coatings.after_blow(p, rat, p.weapon, 6)
    coatings.drain()
    assert rat.has_effect('poisoned')


@pytest.mark.parametrize('venom', VENOMS)
def test_a2_the_card_says_blood_again(venom):
    lore = _data('items', 'flask.json')[venom]['lore']
    assert 'poison cannot harm' not in lore and 'poison can harm' not in lore
    assert 'blood' in lore


# ------------------------------------------------------------------------ A4

def _piles(g):
    from items import GoldPile
    return [i for i in g.ground_items if isinstance(i, GoldPile)]


def test_a4_an_ant_leaves_gold_the_hero_never_set_down():
    from items import add_gold_to_tile
    g = _scene(('myrmekes', 5, 0))
    g.ground_items = []
    m = g.monsters[0]
    add_gold_to_tile(g.ground_items, 5000, m.x + 1, m.y)
    add_gold_to_tile(g.ground_items, 40, m.x + 1, m.y, found=False)   # a thief's return, an overflow
    g._lore_powers_before(m)
    assert len(_piles(g)) == 2 and not m.__dict__.get('_lp_busy')


def test_a4_gold_the_hero_drops_still_stops_it():
    g = _scene(('myrmekes', 2, 0))
    g.ground_items = []
    m = g.monsters[0]
    g.player_gold = 300
    g._drop_gold(120)
    g._lore_powers_before(m)
    assert not _piles(g) and m.__dict__.get('_lp_busy')


def test_a4_a_drop_beside_found_gold_gives_up_only_what_was_dropped():
    from items import add_gold_to_tile
    g = _scene(('myrmekes', 2, 0))
    g.ground_items = []
    add_gold_to_tile(g.ground_items, 5000, g.player.x, g.player.y)
    g.player_gold = 300
    g._drop_gold(120)
    g._lore_powers_before(g.monsters[0])
    assert [p.amount for p in _piles(g)] == [5000]


# ------------------------------------------------------------------------ A5

def _squeeze(kind='naga_guardian', roll=40):
    g = _scene((kind, 1, 0), hp=9000)
    m = g.monsters[0]
    m.max_hp = m.hp = 5000
    _hold(g, m)
    return g, m


def _squeezed(g, m):
    import holds
    g.player.hp = g.player.max_hp
    m._squeeze_now = True
    return holds.blow(m, g.player)


@pytest.fixture
def even(monkeypatch):
    """Every die the same, and nothing turning a blow aside but what a test adds."""
    import dice
    import guards
    monkeypatch.setattr(dice, 'roll', lambda *a, **k: 40)
    monkeypatch.setattr(guards, 'guard_keep', lambda *a, **k: (1.0, 1.0, None))
    return monkeypatch


def test_a5_a_squeeze_meets_the_guards(even):
    import guards
    g, m = _squeeze()
    plain, _line = _squeezed(g, m)
    even.setattr(guards, 'guard_keep', lambda *a, **k: (0.5, 1.0, None))
    kept, _line = _squeezed(g, m)
    assert 0 < kept < plain and abs(kept - plain / 2) <= 1


def test_a5_a_squeeze_meets_the_lions_hide(even):
    import armor_procs
    g, m = _squeeze()
    plain, _line = _squeezed(g, m)
    real = armor_procs.player_has_armor_proc
    even.setattr(armor_procs, 'player_has_armor_proc',
                 lambda p, f: f == 'unskinnable' or real(p, f))
    hide, _line = _squeezed(g, m)
    assert 0 < hide < plain and abs(hide - plain / 2) <= 1


def test_a5_a_squeeze_meets_the_armours_material(even):
    g, m = _squeeze()
    plain, _line = _squeezed(g, m)
    m._through_material_weakness = lambda p, dmg, dtype: (max(1, dmg // 2), '')
    kept, _line = _squeezed(g, m)
    assert 0 < kept < plain


def test_a5_a_guts_acid_can_be_sent_back(even):
    import chain_passives
    g, m = _squeeze('gelatinous_cube')
    even.setattr(chain_passives, 'get_reflect_spell_chance', lambda p: 1.0)
    before = m.hp
    actual, line = _squeezed(g, m)
    assert actual > 0 and m.hp < before and 'reflects back' in line


def test_a5_a_squeeze_still_cannot_be_dodged(even):
    g, m = _squeeze()
    m._slipped = lambda *a, **k: True
    actual, _line = _squeezed(g, m)
    assert actual > 0


# ------------------------------------------------------------------------ A6

def test_a6_the_vine_always_takes_hold_and_the_save_is_the_way_out():
    import hazards
    vine = hazards.hazard_def('conjured_vine')
    assert vine['chance'] == 1.0 and vine['save'] is True
    rng = random.Random(3)
    assert all(hazards.step_fires(vine, heavy=h, levitating=False, rng=rng)
               for h in (False, True) for _ in range(300))
    assert not hazards.step_fires(vine, heavy=False, levitating=True, rng=rng)


def test_a6_the_card_and_the_cast_say_so():
    from spells import LEARNABLE_SPELLS
    assert 'may catch' not in LEARNABLE_SPELLS['dionysus_vine_spell']['desc']
    g = _scene(('kobold', 3, 0))
    g._cast_entangle(g.monsters[0], 4)
    said = ' '.join(_msgs(g, 4))
    assert 'Vines burst up' in said and 'may catch' not in said


# ------------------------------------------------------------------------ A7

def _read(g, sid, buc='uncursed'):
    import items
    sc = items.make_item_by_id('scroll', sid)
    sc.buc = buc
    g.player.status_effects.clear()
    g._apply_scroll_effect(sc)


def test_a7_absolute_ward_lasts_its_eighty_turns():
    g = _scene()
    _read(g, 'scroll_of_absolute_ward')
    st = g.player.status_effects
    assert st['shielded'] == st['fire_shield'] == 80
    assert any('for 80 turns' in t for t in _msgs(g))


def test_a7_the_lesser_rites_are_as_they_were():
    g = _scene()
    _read(g, 'scroll_of_aegis')
    assert g.player.status_effects['shielded'] == 50


def test_a7_leaves_a_cursed_rite_exactly_as_it_was():
    """Blessed and cursed are another ruling's to change."""
    g = _scene()
    _read(g, 'scroll_of_absolute_ward', 'cursed')
    assert g.player.status_effects['shielded'] == 60
    assert 'fire_shield' not in g.player.status_effects
