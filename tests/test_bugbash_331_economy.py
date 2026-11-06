"""Bug bash 3.3.1, the traders: prices that cannot be farmed.

C6: arrows sold as a whole stack for one flat price, whatever the count, so
twenty single arrows sold for twenty times what the stack of twenty did
(floor 5: 10 gold as a stack, 200 as singles, against 40 to buy).
C7: a ware too heavy to carry was set at the hero's feet with no record of
its price, so the resale cap (never more than half of what was paid) did
not hold for it.

Logic tests on a real headless Game; how the shop reads is a play-test.
"""
import copy
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

import economy  # noqa: E402
import items  # noqa: E402


@pytest.fixture(autouse=True)
def _no_saves(monkeypatch, tmp_path):
    import save_system
    import bones
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda name: str(tmp_path / f'save_{name}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    yield


def _game(name='__bb331_econ__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(7)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1, 1)), player_name=name)
    g.monsters = [m for m in g.monsters if not getattr(m, '_npc_encounter_tag', None)]
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _trader(g, stock, kind='generalist'):
    from mystery_system import MerchantNPC, build_trader
    g.ground_items = [i for i in g.ground_items if not isinstance(i, MerchantNPC)]
    m = build_trader(kind, g.dungeon_level, random.Random(11))
    m.stock = list(stock)
    m.prices = [economy.stock_price(it, g.dungeon_level, m.markup) for it in m.stock]
    m.purse = 100000
    m.x, m.y = g.player.x + 1, g.player.y
    g.ground_items.append(m)
    g._open_shop()
    return m


def _arrows(n, kind='iron_arrow'):
    a = copy.copy(next(i for i in items.load_items('ammo') if i.id == kind))
    a.count = n
    return a


@pytest.mark.parametrize('level', [1, 5, 20, 60])
def test_split_arrows_never_sell_for_more_than_the_stack(level):
    whole = economy.sell_offer(_arrows(20), level, known=True, identified=True)
    singles = sum(economy.sell_offer(_arrows(1), level, known=True, identified=True)
                  for _ in range(20))
    halves = 2 * economy.sell_offer(_arrows(10), level, known=True, identified=True)
    assert singles <= whole and halves <= whole
    assert economy.sell_offer(_arrows(40), level, known=True, identified=True) >= whole


def test_an_average_bundle_keeps_its_price():
    """iron arrows roll 10-30: a bundle of 20 sells as the old flat price did."""
    lv = 20
    flat = economy.nice(economy.merchant_price(_arrows(20), lv) * economy.SELL_RATE_IDENTIFIED)
    assert abs(economy.sell_offer(_arrows(20), lv, known=True, identified=True) - flat) <= 5


def test_bought_arrows_split_into_singles_never_return_more_than_half_the_price():
    g = _game()
    g.dungeon_level = 20
    m = _trader(g, [_arrows(20)])
    g.player_gold = 10000
    paid = g._trader_price(0)
    g._trader_buy(0)
    stack = next(i for i in g.player.inventory if getattr(i, 'id', '') == 'iron_arrow')
    got = 0
    g._shop_tab = 1
    while stack.count > 1:
        one = g.player.drop_stack(stack, 1)
        g.player.inventory.append(one)
        offer, why = g._trader_offer(one)
        if why is None:
            gold = g.player_gold
            g._trader_sell(one)
            got += g.player_gold - gold
    offer, why = g._trader_offer(stack)
    if why is None:
        gold = g.player_gold
        g._trader_sell(stack)
        got += g.player_gold - gold
    assert got <= paid * economy.RESALE_CAP_OF_PAID
    assert m is g._shop_merchant


@pytest.mark.parametrize('level', [1, 10, 40, 90])
def test_a_traders_price_never_names_a_curse_ring(level):
    """C8: unknown rings cost 1,050-2,650 on floor 10 and a curse ring 105,
    so the tag told the hero which ring was a curse (the leak shop_worth_floor
    closed for potions, scrolls and wands in 2026-10). No ware sells for less
    than the hero is offered for it unknown."""
    accs = items.load_items('accessory')
    common = [a for a in accs if economy.item_worth(a) == 1.0 and not getattr(a, 'is_unique', False)]
    for a in accs:
        if getattr(a, 'is_unique', False):
            continue
        same_tier = [c for c in common if economy._item_tier(c) == economy._item_tier(a)]
        if same_tier:
            assert economy.stock_price(a, level) >= economy.stock_price(same_tier[0], level), a.id
        assert economy.stock_price(a, level) >= economy.sell_offer(
            a, level, known=False, identified=False), a.id


def _scribe(g):
    """The bookseller (scribe service) beside the hero, a ring to study."""
    from mystery_system import MerchantNPC, build_trader
    g.ground_items = [i for i in g.ground_items if not isinstance(i, MerchantNPC)]
    m = build_trader('bookseller', g.dungeon_level, random.Random(3))
    m.x, m.y = g.player.x + 1, g.player.y
    g.ground_items.append(m)
    g._open_shop()
    ring = copy.copy(next(a for a in items.load_items('accessory')
                          if not getattr(a, 'is_unique', False) and hasattr(a, 'id_level')))
    ring.identified = False
    g.player.inventory.append(ring)
    g.player_gold = 5000
    return m, ring


def test_odins_free_identify_takes_no_scribes_fee(monkeypatch):
    """C9: the scribe's service ran the identify, the Cloak of Odin's free
    identify answered it with no question, and the fee was taken anyway."""
    import chain_passives
    real = chain_passives.player_has_passive
    monkeypatch.setattr(chain_passives, 'player_has_passive',
                        lambda p, f: f == 'identify_one_per_floor_free' or real(p, f))
    g = _game()
    _m, ring = _scribe(g)
    gold = g.player_gold
    g._trader_service_on('id_retry', ring)
    assert not g._needs_identify(ring)                     # Odin named it
    assert g.player_gold == gold                           # and the scribe asked nothing
    assert not chain_passives.is_charge_available(g.player, 'identify_one_per_floor_free')


def test_the_scribe_is_paid_when_he_sits_in_on_a_question(monkeypatch):
    from quiz_engine import QuizState
    g = _game()
    _m, ring = _scribe(g)
    gold = g.player_gold
    g._trader_service_on('id_retry', ring)
    assert g.quiz_engine.state == QuizState.ASKING         # a question is up
    assert g.player_gold < gold


def test_no_fee_when_a_mastered_tier_answers_for_you():
    """A mastered philosophy tier auto-passes: no question, no scribe."""
    import philosophy_mastery
    g = _game()
    _m, ring = _scribe(g)
    tier = philosophy_mastery.identify_tier(ring, g.player)
    g.quiz_engine._mastered.add(('philosophy', tier))
    gold = g.player_gold
    g._trader_service_on('id_retry', ring)
    assert not g._needs_identify(ring)
    assert g.player_gold == gold


def test_a_ware_set_at_your_feet_keeps_its_price_for_the_resale_cap(monkeypatch):
    """Bought on floor 3 and too heavy to carry; carried down to floor 40 and
    sold, it fetched four times what it cost."""
    g = _game()
    g.dungeon_level = 3
    import traders
    armour = copy.copy(next(a for a in items.load_items('armor')
                            if getattr(a, 'slot', '') == 'body' and not traders.is_quest_piece(a)))
    armour.identified = True
    _trader(g, [armour])
    g.player_gold = 10000
    paid = g._trader_price(0)
    monkeypatch.setattr(g.player, 'add_to_inventory', lambda item: False)
    g._trader_buy(0)
    assert any(i is armour for i in g.ground_items)          # at the hero's feet
    assert getattr(armour, '_bought_for', None) == paid
    monkeypatch.undo()
    g.dungeon_level = 40                                      # carried deep, sold there
    _trader(g, [])
    g.player.inventory.append(armour)
    offer, why = g._trader_offer(armour)
    assert why is None and offer <= paid * economy.RESALE_CAP_OF_PAID
