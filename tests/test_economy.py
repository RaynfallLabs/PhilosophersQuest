"""The gold economy: one income line, gold by lore, and everything priced
against it (economy refactor 2026-10-17; ECONOMY_REFACTOR_PROPOSAL.md).

S1-S10 each pin a SAFE-NOW fix from the proposal; D1/D3-D7 the design work.
Trader and shop behaviour is in test_traders.py. These are logic tests: how
gold FEELS over a run is Brandon's play-test.
"""
import copy
import json
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

pygame.init()

import economy  # noqa: E402

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(seed=7, name='__test_economy__'):
    from main import Game
    from game_states import STATE_PLAYER
    import items
    random.seed(seed)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _data(name):
    return json.load(open(os.path.join(ROOT, 'data', name), encoding='utf-8'))


def _encounters():
    out = []
    for fn in ('npc_encounters.json', 'flavor_encounters.json'):
        d = _data(fn)
        encs = d if isinstance(d, list) else d.get('encounters', d)
        out += list(encs.values()) if isinstance(encs, dict) else encs
    return [e for e in out if isinstance(e, dict)]


# ------------------------------------------------------------------ the income line

def test_income_is_the_refit_line():
    assert economy.floor_income(1) == 206 and economy.floor_income(100) == 7730
    vals = [economy.floor_income(f) for f in range(1, 101)]
    assert vals == sorted(vals)


def test_the_generator_pays_about_the_line():
    """The real floor generator on a mid floor: coin piles and lairs, chest
    gold (container_system.chest_gold, a passed lock), monster purses. The
    full measurement is tools/balance/gold_sim.py."""
    import level_manager
    import container_system
    from items import Container, GoldPile
    totals = []
    rng = random.Random(3)
    for _ in range(8):
        _d, mons, its = level_manager.LevelManager().generate(15)
        g = sum(i.amount for i in its if isinstance(i, GoldPile))
        c = sum(container_system.chest_gold(ch, 15, rng) for ch in its if isinstance(ch, Container))
        m = sum(sum((mo.treasure or {}).get('gold', [0, 0])) / 2 for mo in mons)
        totals.append(g + 0.7 * c + 1.2 * m)
    measured = sum(totals) / len(totals)
    assert 0.4 * economy.floor_income(15) < measured < 2.2 * economy.floor_income(15)


def test_nice_numbers():
    assert economy.nice(33) == 35 and economy.nice(437) == 440 and economy.nice(1234) == 1250
    assert economy.nice(0) == 0 and economy.nice(1) == 5


# ------------------------------------------------------------------ D1: gold by lore

def test_beasts_vermin_oozes_constructs_and_spirits_carry_no_coin():
    mons = _data('monsters.json')
    for mid, m in mons.items():
        tr = m.get('treasure') or {}
        tags = set(m.get('tags') or ())
        purse = tr.get('purse')
        assert purse, mid                                    # every creature was decided
        if purse == 'kept':
            continue                                         # named one-offs, bosses, specials
        if tags & {'beast', 'plant', 'construct', 'elemental'} and purse == 'none':
            assert tr['gold'] == [0, 0], mid
        if 'beast' in tags and not tags & {'humanoid', 'dragon', 'fey'}:
            assert tr['gold'] == [0, 0], mid
    assert mons['giant_rat']['treasure']['gold'] == [0, 0]
    assert mons['cave_bear']['treasure']['gold'] == [0, 0]
    assert mons['chimera']['treasure']['gold'] == [0, 0]


def test_people_thieves_and_dragons_do():
    mons = _data('monsters.json')
    for mid in ('goblin', 'bandit_thief', 'bandit_captain', 'adult_red_dragon', 'vampire', 'hill_giant'):
        lo, hi = mons[mid]['treasure']['gold']
        assert 0 < lo < hi, mid
    thief = sum(mons['bandit_thief']['treasure']['gold'])
    goblin = sum(mons['goblin']['treasure']['gold'])
    assert thief > goblin
    dragon = mons['adult_red_dragon']['treasure']
    assert dragon['purse'] == 'hoard' and dragon['gold'][1] > 10 * mons['orc_warlord']['treasure']['gold'][1] / 2
    counts = {}
    for m in mons.values():
        counts[m['treasure']['purse']] = counts.get(m['treasure']['purse'], 0) + 1
    assert counts['none'] > 200 and counts['purse'] > 40 and counts['hoard'] > 10


def test_gold_by_lore_is_baked_into_the_data_and_idempotent():
    """LORE NOT FLOOR: the tool writes real numbers into monsters.json;
    running it again changes nothing, and nothing at runtime scales gold by
    the floor (test_lore_not_floor guards game code)."""
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'balance'))
    import gold_by_lore
    mons = _data('monsters.json')
    for mid, m in mons.items():
        kind = gold_by_lore.purse_kind(mid, m)
        assert kind == m['treasure']['purse'], mid
        if kind != 'kept':
            assert gold_by_lore.gold_for(mid, m, kind) == m['treasure']['gold'], mid


def test_chests_pay_a_share_of_the_floor():
    import container_system
    from items import Container, get_chest_template
    tpls = _data('chest_templates.json')
    rng = random.Random(2)
    for tid, t in tpls.items():
        lo, hi = t['gold_share']
        assert 0 < lo < hi <= 2.0, tid
        c = Container({'id': tid, 'name': tid, 'symbol': '&', 'color': [1, 1, 1], 'template_id': tid, 'item_class': 'container'})
        for lvl in (5, 50, 95):
            g = container_system.chest_gold(c, lvl, rng)
            inc = economy.floor_income(lvl)
            assert lo * inc * 0.9 <= g <= hi * inc * 1.1, (tid, lvl, g)
    assert get_chest_template('dragon_hoard')['gold_share'][0] > get_chest_template('wooden_chest')['gold_share'][1]
    # a chest without a template keeps its written range
    old = Container({'id': 'box', 'name': 'box', 'symbol': '&', 'color': [1, 1, 1], 'gold': [10, 20], 'item_class': 'container'})
    assert 10 <= container_system.chest_gold(old, 50, rng) <= 20


def test_rooms_hold_coin_piles_and_lairs_hold_heaps_without_touching_the_floor_stream():
    from dungeon import generate_dungeon, spawn_items
    from items import GoldPile
    # 40 floors, not 12: how many rooms roll a pile depends on how much of
    # the shared stream earlier code drew, so a small sample was flaky
    # (4 piles in one suite order, 9 alone). About 34 is typical.
    found = 0
    for s in range(40):
        random.seed(500 + s)
        d = generate_dungeon(80, 50, 30)
        its = spawn_items(d.rooms, 30, d)
        piles = [i for i in its if isinstance(i, GoldPile)]
        found += len(piles)
        for p in piles:
            assert p.amount <= economy.floor_income(30) * 1.0
    assert found >= 12
    src = open(os.path.join(ROOT, 'src', 'dungeon.py'), encoding='utf-8').read()
    assert '_coin_rng = random.Random(hash((tuple(rng.getstate()' in src


def test_boss_hoards_are_shares_of_the_floor_not_written_sums():
    src = open(os.path.join(ROOT, 'src', 'boss_levels.py'), encoding='utf-8').read()
    assert '_random.randint(150, 350)' not in src and '_random.randint(250, 500)' not in src


# ------------------------------------------------------------------ prices

def test_trader_prices_are_a_share_of_the_floor():
    class It:
        def __init__(self, cls, tier=3, unique=False):
            self.item_class, self.quiz_tier, self.is_unique = cls, tier, unique
    for floor in (1, 20, 60, 95):
        income = economy.floor_income(floor)
        assert 0.08 * income <= economy.merchant_price(It('potion', 1), floor) <= 0.3 * income
        assert 1.2 * income < economy.merchant_price(It('accessory'), floor) < 2.5 * income
        assert economy.merchant_price(It('weapon', unique=True), floor) > 2.5 * income
    assert economy.merchant_price(It('potion', 1), 1) >= 25
    import mystery_system
    assert mystery_system._merchant_price is economy.merchant_price


def test_s4_a_named_ring_costs_what_named_gear_does():
    class It:
        def __init__(self, unique):
            self.item_class, self.quiz_tier, self.is_unique = 'accessory', 3, unique
    for floor in (25, 99):
        plain, named = economy.merchant_price(It(False), floor), economy.merchant_price(It(True), floor)
        assert named >= 1.9 * plain
        assert named > 2.5 * economy.floor_income(floor)


def test_worth_follows_the_item_not_the_class():
    from items import load_items
    pots = {p.id: p for p in load_items('potion')}
    lvl = 40
    price = {k: economy.merchant_price(pots[k], lvl) for k in
             ('potion_of_healing', 'potion_of_extra_healing', 'potion_of_full_healing',
              'potion_of_sickness', 'potion_of_blindness', 'potion_of_drain_strength')}
    assert price['potion_of_sickness'] == price['potion_of_blindness'] == price['potion_of_drain_strength']
    assert price['potion_of_sickness'] < price['potion_of_healing'] < price['potion_of_extra_healing'] \
        < price['potion_of_full_healing']
    food = {f.id: f for f in load_items('food')}
    assert economy.merchant_price(food['ambrosia'], lvl) > 10 * economy.merchant_price(food['bread_ration'], lvl)
    from items import make_item_by_id
    sphere = make_item_by_id('artifact', 'soul_sphere')
    assert economy.merchant_price(sphere, lvl) >= 1.5 * economy.floor_income(lvl)
    t = economy.worth_table()
    for cls, table in t['by_effect'].items():
        for eff, v in table.items():
            assert v == 'junk' or 0.1 <= float(v) <= 10, (cls, eff)


def test_an_unknown_price_never_depends_on_what_the_thing_is():
    from items import load_items
    pots = [p for p in load_items('potion')]
    prices = {economy.unknown_price(p, 30) for p in pots}
    assert len(prices) == 1


# ------------------------------------------------------------------ S1

def test_s1_a_purse_share_cost_has_a_floor_and_an_empty_purse_cannot_pay_it():
    from npc_encounters import can_pay_cost, gold_pct_label
    cost = {'type': 'gold_pct', 'amount': 15}
    least = economy.pct_cost(0, 15, 81)
    assert least == economy.nice(economy.floor_income(81) * 2 * 0.15) > 0
    ok, why = can_pay_cost(None, cost, 0, 81)
    assert not ok and f"{least:,}" in why
    assert can_pay_cost(None, cost, least, 81)[0]
    assert economy.pct_cost(10 ** 6, 15, 81) == 150000            # rich: the share
    assert gold_pct_label(cost, 0, 81) == f" ({least:,} Gold)"
    # a loss that lands later (no level) is still a plain share
    assert can_pay_cost(None, cost, 0)[0]


def test_s1_dropping_your_gold_first_no_longer_buys_the_golem_medic_for_free():
    import pygame as pg
    g = _game()
    g.dungeon_level = 81
    enc = economy.price_encounter(next(e for e in _encounters()
                                       if e.get('tag') == 'flv_practical_golem_medic'), 81)
    g._flavor_encounter_levels = {81: enc}
    g._maybe_spawn_flavor_npc(81)
    npc = next(m for m in g.monsters if getattr(m, '_flavor_encounter_tag', None) == enc['tag'])
    g.player_gold = 0
    g.player.hp = 1
    assert g._start_flavor_encounter(npc)
    g._npc_encounter_input(pg.K_RETURN)
    g._npc_encounter_input(pg.K_1)
    assert g.player.hp == 1 and enc['tag'] not in (g._encountered_flavor_npcs or set())
    g.player_gold = 10 ** 5
    g._npc_encounter_input(pg.K_1)
    assert g.player.hp == g.player.max_hp
    assert g.player_gold == 10 ** 5 - economy.pct_cost(10 ** 5, 15, 81)


def test_s1_the_option_shows_what_the_share_will_cost():
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert 'gold_pct_label(opt.get' in src


# ------------------------------------------------------------------ S2

def test_s2_a_gold_ring_never_doubles_the_gold_a_thief_gives_back():
    import theft
    from items import GoldPile, add_gold_to_tile, is_found_gold
    g = _game()
    m = types.SimpleNamespace(x=g.player.x, y=g.player.y, stolen_gold=500)
    m.__dict__['stolen_items'] = []
    found = add_gold_to_tile(g.ground_items, 100, m.x, m.y)
    theft.give_back(g, m)
    piles = [i for i in g.ground_items if isinstance(i, GoldPile) and (i.x, i.y) == (m.x, m.y)]
    assert sorted(p.amount for p in piles) == [100, 500]        # never merged
    own = next(p for p in piles if p.amount == 500)
    assert not is_found_gold(own) and is_found_gold(found)
    from items import make_item_by_id
    ring = make_item_by_id('accessory', 'ring_of_the_nibelung')
    assert ring.gold_multiplier == 2.0
    g.player.accessory_slots[0] = ring
    assert ring in g.player.equipped_accessories
    gold0, earned0 = g.player_gold, g.gold_earned
    g.ground_items = [i for i in g.ground_items if i is not found]
    g._pickup(own)
    assert g.player_gold == gold0 + 500 and g.gold_earned == earned0   # the hero's own coin: x1
    g.ground_items.append(found)
    g._pickup(found)
    assert g.player_gold == gold0 + 500 + 200 and g.gold_earned == earned0 + 200   # found: x2


# ------------------------------------------------------------------ S3 (test_traders: dressed stock)
# ------------------------------------------------------------------ S5

def test_s5_vendors_charge_the_traders_price_at_their_floor():
    encs = {e['tag']: e for e in _encounters()}
    herb = economy.price_encounter(encs['flv_wandering_herbalist'], 1)
    cost = herb['options'][1]['cost']
    assert cost['amount'] == economy.share_price('potion', 1, 0.75)
    assert cost['amount'] < 60                                   # was 270 on floor 1
    assert f"({cost['amount']:,} Gold)" in herb['options'][1]['label']
    ort = economy.price_encounter(encs['flv_final_merchant_ortolan'], 81)
    trader_potion = economy.share_price('potion', 81)
    assert ort['options'][0]['cost']['amount'] == economy.share_price('potion', 81, 1.5)
    assert ort['options'][0]['cost']['amount'] <= 1.6 * trader_potion
    shares = [o['cost'] for e in encs.values() for o in e.get('options') or []
              if isinstance(o.get('cost'), dict) and o['cost'].get('share')]
    assert len(shares) >= 20


def test_s5_a_share_cost_is_never_scaled_twice():
    enc = {'tag': 'v', 'min_level': 10, 'options': [
        {'label': 'Buy a potion', 'cost': {'type': 'gold', 'share': 'potion', 'markup': 1.0}}]}
    out = economy.price_encounter(enc, 10)
    assert out['options'][0]['cost']['amount'] == economy.share_price('potion', 10)
    assert economy.price_encounter(out, 10) is out


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
    assert enc['options'][0]['cost']['amount'] == 30
    o0, o1, o2 = out['options']
    assert o0['cost']['amount'] == 180
    assert o0['label'] == 'Buy a potion from him (180g)'
    assert o0['outcome'] == 'He takes your 180 gold.'
    assert o1['cost']['amount'] == 480 and '480 gold' in o1['label'] and '(+1)' in o1['label']
    assert o1['reward']['rewards'][0] == {'type': 'gold', 'min': 300, 'max': 480}
    assert o2['outcome'] == 'You leave on level 30.'
    assert economy.price_encounter(out) is out


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
    assert 0.05 < sorted(shares)[len(shares) // 2] < 0.6
    for enc in flavor_encounters.FLAVOR_ENCOUNTERS:
        assert not enc.get('_gold_priced')


# ------------------------------------------------------------------ S7

def test_s7_the_ending_shows_gold_earned_and_gold_carried():
    g = _game()
    g.player_gold = 0
    e0 = g.gold_earned
    g.player_gold += 300
    g.player_gold -= 100
    g._set_gold_quietly(g.player_gold + 50)      # the hero's own coin back
    assert g.gold_earned == e0 + 300 and g.player_gold == 250
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert 'Gold Collected' not in src and src.count('"Gold Earned"') == 2 and src.count('"Gold Carried"') == 2
    import save_system
    assert "'gold_earned'" in open(save_system.__file__, encoding='utf-8').read()


# ------------------------------------------------------------------ S8

def test_s8_no_stale_merchant_key_or_chance_text():
    for name in ('main.py', 'mystery_system.py', 'game_traders.py', 'dungeon.py'):
        src = open(os.path.join(ROOT, 'src', name), encoding='utf-8').read()
        assert 'player presses T' not in src and '(t key)' not in src, name
        assert '20% chance per floor to place a merchant' not in src, name


# ------------------------------------------------------------------ S9

def test_s9_the_bribe_is_priced_once_and_the_monster_stands_aside_not_still():
    import game_menus
    mon = types.SimpleNamespace(alive=True, is_boss=False, tags=['humanoid'], x=2, y=1,
                                name='Orc', kind='orc', status_effects={}, is_unique_named=False)
    mon.resists_control = lambda e: False
    pl = types.SimpleNamespace(x=1, y=1)
    msgs = []
    g = types.SimpleNamespace(player=pl, monsters=[mon], visible={(2, 1)}, dungeon_level=20,
                              player_gold=0, add_message=lambda t, k='info': msgs.append(t))
    random.seed(2)
    for _ in range(6):                           # pressing again never re-rolls the price
        game_menus.MenuMixin._activate_gold_offering(g)
    quoted = {m for m in msgs if 'You need' in m}
    assert len(quoted) == 1
    g.player_gold = 5000
    game_menus.MenuMixin._activate_gold_offering(g)
    lo, hi = economy.BRIBE_SHARE
    spent = 5000 - g.player_gold
    assert spent == mon.__dict__['_bribe_cost']
    assert 0.9 * lo * economy.floor_income(20) <= spent <= 1.1 * hi * economy.floor_income(20)
    assert mon.status_effects.get('charmed') == economy.BRIBE_TURNS
    assert 'paralyzed' not in mon.status_effects


def test_s9_striking_a_bribed_monster_ends_the_deal():
    from monster import Monster
    mons = _data('monsters.json')
    m = Monster({**mons['orc_warrior'], 'id': 'orc_warrior'}, 1, 1)
    m.status_effects['charmed'] = 3
    m.__dict__['_bribed'] = True
    m.take_damage(1)
    assert 'charmed' not in m.status_effects


# ------------------------------------------------------------------ S10

def test_s10_a_trader_whose_every_ware_is_a_claimed_unique_is_sold_out():
    import level_manager
    import items
    from mystery_system import MerchantNPC
    from items import load_items
    uniq = copy.copy(next(a for a in load_items('accessory') if a.is_unique and items.is_random_loot(a)))
    lm = level_manager.LevelManager()        # (a manager binds its own registry)
    items.bind_unique_registry({uniq.id})
    m = MerchantNPC(1, 1, [uniq], [100])
    kept = lm._once_per_run([m])
    assert kept == [m] and m.stock == [] and m.sold_out


# ------------------------------------------------------------------ D6 / D7 karma

def test_d6_late_temptations_offer_a_share_of_the_purse():
    assert economy.purse_scaled(1800, 200000, 25) == 50000
    assert economy.purse_scaled(1800, 1000, 25) == 1800
    deep = [(e['tag'], o) for e in _encounters() for o in e.get('options') or []
            if any(isinstance(p, dict) and p.get('purse_pct')
                   for p in ([o.get('reward') or {}] + list((o.get('reward') or {}).get('rewards') or [])))]
    assert len(deep) >= 12
    g = _game()
    # Coins weigh (2026-10-18): a strong hero, so the whole share fits.
    g.player.STR = 40
    g.player_gold = 20000
    g._apply_npc_reward({'type': 'gold', 'min': 300, 'max': 400, 'purse_pct': 25})
    assert g.player_gold == 25000


def test_d6_forgoing_pocket_change_is_no_sacrifice():
    """A forgo option scores karma only when the gold turned down was real
    against the purse at the time (economy.forgo_is_real)."""
    assert economy.forgo_is_real(500, 1000) and not economy.forgo_is_real(500, 100000)
    g = _game()
    enc = {'tag': 'fx_box', 'options': [
        {'label': 'Leave the box', 'karma': 1, 'karma_kind': 'forgo', 'outcome': 'You leave it.'},
        {'label': 'Empty the box', 'reward': {'type': 'gold', 'amount': 300}, 'outcome': 'Taken.'}]}
    g._npc_encounter_active = enc
    g._npc_selected_index = 0
    assert g._forgone_gold(enc) == 300
    g._npc_encounter_active['options'][1]['reward']['purse_pct'] = 25
    g.player_gold = 100000
    assert g._forgone_gold(enc) == 25000              # a purse-relative temptation is always real
    del g._npc_encounter_active['options'][1]['reward']['purse_pct']
    assert not economy.forgo_is_real(g._forgone_gold(enc), g.player_gold)
    enc['options'][1]['reward'] = {'type': 'multi', 'rewards': [
        {'type': 'gold', 'amount': 300}, {'type': 'random_accessory'}]}
    assert g._forgone_gold(enc) is None                # more than gold: always judged real


def test_gold_lives_on_the_game_not_on_the_player():
    for name in ('game_menus.py', 'main.py', 'game_divine.py', 'game_combat.py', 'game_traders.py'):
        src = open(os.path.join(ROOT, 'src', name), encoding='utf-8').read()
        code = '\n'.join(line.split('#')[0] for line in src.splitlines())
        assert 'pl.gold' not in code and 'player.gold ' not in code and 'player.gold+' not in code, name
    from player import Player
    assert not hasattr(Player(), 'gold')


def test_found_gold_follows_the_floor():
    rng = random.Random(1)
    shallow = [economy.roll_share(rng, 3, economy.GRAVE_RICH_SHARE) for _ in range(50)]
    deep = [economy.roll_share(rng, 80, economy.GRAVE_RICH_SHARE) for _ in range(50)]
    assert max(shallow) < min(deep)
    assert economy.written_gold(50) == 300 and economy.written_gold(0) == 0
    src = open(os.path.join(ROOT, 'src', 'game_divine.py'), encoding='utf-8').read()
    assert src.count('economy.roll_share(_rng, self.dungeon_level') == 3


def test_service_prices_are_shares_and_the_dearest_also_bite_the_purse():
    for sid in economy.SERVICE_SHARE:
        p = economy.service_price(sid, 50)
        assert 0.05 * economy.floor_income(50) <= p <= 1.0 * economy.floor_income(50), sid
    assert economy.service_price('restore', 50, purse=10 ** 6) == 100000
    assert economy.service_price('repair', 50, points=3) == economy.nice(economy.floor_income(50) * 0.45)
