"""The gold economy: one income line, and everything priced against it."""
import os
import random
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import economy  # noqa: E402


def test_income_is_a_rising_line_that_matches_what_floors_pay():
    assert economy.floor_income(1) == 240 and economy.floor_income(100) == 9150
    vals = [economy.floor_income(f) for f in range(1, 101)]
    assert vals == sorted(vals)
    # the real generator, a mid floor: ground gold + chests + monster drops
    import level_manager
    from items import Container, GoldPile
    totals = []
    for _ in range(6):
        _d, mons, items = level_manager.LevelManager().generate(15)
        g = sum(i.amount for i in items if isinstance(i, GoldPile))
        c = sum(ch.gold[0] + (ch.gold[1] - ch.gold[0]) * 0.85
                for ch in items if isinstance(ch, Container) and ch.gold)
        m = sum(sum((mo.treasure or {}).get('gold', [0, 0])) / 2 for mo in mons)
        totals.append(g + 0.7 * c + 1.2 * m)
    measured = sum(totals) / len(totals)
    assert 0.45 * economy.floor_income(15) < measured < 2.2 * economy.floor_income(15)


def test_nice_numbers():
    assert economy.nice(33) == 35 and economy.nice(437) == 440 and economy.nice(1234) == 1250
    assert economy.nice(0) == 0 and economy.nice(1) == 5


def test_merchant_prices_are_a_share_of_the_floor():
    class It:
        def __init__(self, cls, tier=3, unique=False):
            self.item_class, self.quiz_tier, self.is_unique = cls, tier, unique
    for floor in (1, 20, 60, 95):
        income = economy.floor_income(floor)
        assert 0.08 * income <= economy.merchant_price(It('potion', 1), floor) <= 0.3 * income
        assert 1.2 * income < economy.merchant_price(It('accessory'), floor) < 2.5 * income
        assert economy.merchant_price(It('weapon', unique=True), floor) > 2.5 * income
    # floor 1 is no longer pocket change (a potion was 5 gold against 235 earned)
    assert economy.merchant_price(It('potion', 1), 1) >= 25
    import mystery_system
    assert mystery_system._merchant_price is economy.merchant_price


def test_encounter_gold_is_scaled_once_and_labels_follow():
    enc = {'tag': 't', 'options': [
        {'label': 'Buy a potion from him (30g)', 'outcome': 'He takes your 30 gold.',
         'cost': {'type': 'gold', 'amount': 30}, 'reward': None},
        {'label': 'Pay 80 gold to enchant your weapon (+1)', 'outcome': 'Done.',
         'cost': {'type': 'gold', 'amount': 80},
         'reward': {'type': 'multi', 'rewards': [{'type': 'gold', 'min': 50, 'max': 80}]}},
        {'label': 'Leave', 'outcome': 'You leave on level 30.', 'cost': None, 'reward': None},
    ]}
    out = economy.price_encounter(enc)
    assert enc['options'][0]['cost']['amount'] == 30            # the source is untouched
    o0, o1, o2 = out['options']
    assert o0['cost']['amount'] == 180
    assert o0['label'] == 'Buy a potion from him (180g)'
    assert o0['outcome'] == 'He takes your 180 gold.'
    assert o1['cost']['amount'] == 480 and '480 gold' in o1['label'] and '(+1)' in o1['label']
    assert o1['reward']['rewards'][0] == {'type': 'gold', 'min': 300, 'max': 480}
    assert o2['outcome'] == 'You leave on level 30.'            # not a price: left alone
    assert economy.price_encounter(out) is out                   # never scaled twice


def test_every_run_gets_priced_encounters_worth_deciding_over():
    import flavor_encounters
    import npc_encounters
    random.seed(11)
    shares = []
    for picker in (flavor_encounters.select_flavor_encounters,
                   npc_encounters.select_encounter_levels):
        for level, enc in picker().items():
            assert enc.get('_gold_priced'), enc.get('tag')
            for opt in enc.get('options') or []:
                cost = opt.get('cost')
                if isinstance(cost, dict) and cost.get('type') == 'gold' and 'amount' in cost:
                    shares.append(cost['amount'] / economy.floor_income(level))
    assert len(shares) >= 10
    assert 0.05 < sorted(shares)[len(shares) // 2] < 0.45       # was about 0.03
    for enc in flavor_encounters.FLAVOR_ENCOUNTERS:
        assert not enc.get('_gold_priced')                       # the pool itself is never mutated


def test_gold_lives_on_the_game_not_on_the_player():
    """The bribe and Brisingamen used `player.gold`, which does not exist."""
    for name in ('game_menus.py', 'main.py', 'game_divine.py', 'game_combat.py'):
        src = open(os.path.join(ROOT, 'src', name), encoding='utf-8').read()
        code = '\n'.join(line.split('#')[0] for line in src.splitlines())
        assert 'pl.gold' not in code and 'player.gold ' not in code and 'player.gold+' not in code, name
    from player import Player
    assert not hasattr(Player(), 'gold')


def test_bribe_charges_the_purse_and_holds_the_monster():
    import game_menus
    mon = types.SimpleNamespace(alive=True, is_boss=False, intelligence=10, x=2, y=1,
                                name='Orc', kind='orc', status_effects={}, is_unique_named=False)
    pl = types.SimpleNamespace(x=1, y=1)
    msgs = []
    g = types.SimpleNamespace(player=pl, monsters=[mon], visible={(2, 1)}, dungeon_level=20,
                              player_gold=5000, add_message=lambda t, k='info': msgs.append(t))
    random.seed(2)
    game_menus.MenuMixin._activate_gold_offering(g)
    lo, hi = economy.BRIBE_SHARE
    spent = 5000 - g.player_gold
    assert 0.9 * lo * economy.floor_income(20) <= spent <= 1.1 * hi * economy.floor_income(20)
    assert mon.status_effects.get('paralyzed') == economy.BRIBE_TURNS


def test_found_gold_follows_the_floor():
    rng = random.Random(1)
    shallow = [economy.roll_share(rng, 3, economy.GRAVE_RICH_SHARE) for _ in range(50)]
    deep = [economy.roll_share(rng, 80, economy.GRAVE_RICH_SHARE) for _ in range(50)]
    assert max(shallow) < min(deep)
    assert economy.written_gold(50) == 300 and economy.written_gold(0) == 0
    src = open(os.path.join(ROOT, 'src', 'game_divine.py'), encoding='utf-8').read()
    assert src.count('economy.roll_share(_rng, self.dungeon_level') == 3
