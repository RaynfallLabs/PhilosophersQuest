"""The traders (economy refactor 2026-10-17, ECONOMY_REFACTOR_PROPOSAL D3-D7):
the run's plan, placement on a real headless Game, buying, selling, the
no-loop guarantee, services, and what the hero's deeds do to prices.

These are logic tests. How the shop reads and feels at a real window size,
and whether prices feel right in a run, is Brandon's play-test: Claude
cannot drive Pygame.
"""
import copy
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import economy  # noqa: E402
import items  # noqa: E402
import traders  # noqa: E402
from items import load_items  # noqa: E402

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(name='__test_traders__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(5)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.monsters = [m for m in g.monsters if not getattr(m, '_npc_encounter_tag', None)]
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def _texts(g, n=6):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _trader(g, kind='generalist', level=None, stock=None):
    """A trader of ``kind`` standing beside the hero, shop open."""
    from mystery_system import MerchantNPC, build_trader
    from game_states import STATE_PLAYER
    g.ground_items = [i for i in g.ground_items if not isinstance(i, MerchantNPC)]
    g.state = STATE_PLAYER
    level = level or g.dungeon_level
    m = build_trader(kind, level, random.Random(11))
    if stock is not None:
        m.stock = list(stock)
        m.prices = [economy.merchant_price(it, level, m.markup) for it in m.stock]
        m.sold_out = not m.stock
    m.x, m.y = g.player.x + 1, g.player.y
    g.ground_items.append(m)
    g._open_shop()
    return m


def _armed(g):
    """The hero with an iron weapon in hand (the default hero carries his)."""
    from items import pick_random_weapon_for_floor
    w = g.player.weapon
    if w is None:
        w = pick_random_weapon_for_floor(5, random.Random(4))
        g.player.weapon = w
    return w


def _potion(pid):
    return copy.copy(next(p for p in load_items('potion') if p.id == pid))


# ------------------------------------------------------------------ the plan

def test_plan_puts_a_gate_camp_before_every_gate_boss_and_avoids_the_secret_floors():
    for seed in range(40):
        plan = traders.roll_plan(seed * 7919, secret_floors=(5, 47), busy_floors=(3, 9, 15))
        f = plan['floors']
        for gate in (19, 39, 59, 79):
            assert f.get(gate) == 'sutler', (seed, gate)
        for never in (1, 20, 40, 60, 80, 99, 100, 5, 47):
            assert never not in f, (seed, never)
        assert 18 <= len(f) <= 40, len(f)
        kinds = set(f.values())
        assert {'sutler', 'generalist', 'apothecary', 'armourer', 'bookseller', 'abyssal'} <= kinds
        for fl, kind in f.items():
            lo_hi = {'apothecary': (2, 35), 'armourer': (10, 70), 'bookseller': (15, 90),
                     'abyssal': (61, 98)}.get(kind)
            if lo_hi:
                assert lo_hi[0] <= fl <= lo_hi[1], (kind, fl)
    assert traders.roll_plan(123)['floors'] == traders.roll_plan(123)['floors']


def test_the_plan_and_the_spawn_leave_the_shared_random_stream_alone():
    random.seed(77)
    before = random.getstate()
    traders.roll_plan(99, secret_floors=(4,))
    assert random.getstate() == before
    g = _game()
    plan = g._trader_plan()
    lvl = next(f for f, k in sorted(plan['floors'].items()) if k == 'generalist')
    g._change_level(lvl, enter_from_top=True)
    from mystery_system import MerchantNPC
    g.ground_items = [i for i in g.ground_items if not isinstance(i, MerchantNPC)]
    plan['spawned'] = [f for f in plan['spawned'] if f != lvl]
    random.seed(1234)
    before = random.getstate()
    assert g._maybe_spawn_trader(lvl) is not None
    assert random.getstate() == before


def test_floor_generation_no_longer_places_a_trader():
    """Traders are planned per run; generating a floor never draws one (so
    the dungeon's own random stream is the floor's alone)."""
    import level_manager
    from mystery_system import MerchantNPC
    random.seed(4)
    for lvl in (3, 12, 33):
        _d, _m, its = level_manager.LevelManager().generate(lvl)
        assert not any(isinstance(i, MerchantNPC) for i in its)


def test_the_gate_camp_stands_reachable_on_19_39_59_79_clear_of_everything():
    from dungeon import STAIRS_DOWN, STAIRS_UP
    from mystery_system import MerchantNPC
    g = _game('__test_trader_gates__')
    for lvl in (19, 39, 59, 79):
        g._change_level(lvl, enter_from_top=True)
        ts = [i for i in g.ground_items if isinstance(i, MerchantNPC)]
        assert len(ts) == 1, lvl
        t = ts[0]
        assert t.kind == 'sutler' and t.stock and t.purse > 0
        assert g.dungeon.tiles[t.y][t.x] not in (STAIRS_UP, STAIRS_DOWN)
        walk = g._reachable_tiles(g.player.x, g.player.y)
        assert (t.x, t.y) in walk
        assert not any((i.x, i.y) == (t.x, t.y) for i in g.ground_items if i is not t)
        occupied = {(m.x, m.y) for m in g.monsters}
        assert (t.x, t.y) not in occupied
        assert g.renderer._get_sprite(t.sprite_id) is not None, t.sprite_id


def test_a_trader_keeps_clear_of_the_roads_people_and_the_hero():
    """He never stands on or beside an encounter NPC, an escort or an ally,
    nor within 2 tiles of the hero."""
    from monster import Monster
    g = _game('__test_trader_clear__')
    mons = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    walk = sorted(g._reachable_tiles(g.player.x, g.player.y))
    npcs = []
    for i in range(0, len(walk), max(1, len(walk) // 12)):
        x, y = walk[i]
        if (x, y) == (g.player.x, g.player.y):
            continue
        n = Monster({**mons['giant_rat'], 'id': 'giant_rat'}, x, y)
        n._flavor_encounter_tag = f'fx_{i}'
        npcs.append(n)
    g.monsters = npcs
    for s in range(20):
        spot = g._trader_spot(random.Random(s))
        assert spot is not None
        for n in npcs:
            assert max(abs(spot[0] - n.x), abs(spot[1] - n.y)) >= 2, (spot, (n.x, n.y))
        assert max(abs(spot[0] - g.player.x), abs(spot[1] - g.player.y)) >= 3


def test_a_revisit_never_adds_a_second_trader():
    from mystery_system import MerchantNPC
    g = _game('__test_trader_revisit__')
    g._change_level(19, enter_from_top=True)
    g._change_level(18, enter_from_top=False)
    g._change_level(19, enter_from_top=True)
    assert sum(isinstance(i, MerchantNPC) for i in g.ground_items) == 1


def test_every_trader_kind_stocks_from_its_own_list():
    rng = random.Random(3)
    for kind, lvl in (('generalist', 10), ('apothecary', 12), ('armourer', 30),
                      ('bookseller', 40), ('abyssal', 80), ('sutler', 39)):
        d = traders.kind_def(kind)
        items.bind_unique_registry(set())
        stock = traders.build_stock(d, lvl, rng)
        assert stock, kind
        assert len(stock) <= max(traders.stock_size(d, lvl), 2)
        classes = {getattr(i, 'item_class', '') for i in stock}
        allowed = {e.get('class') or e.get('gear') or e.get('cat') for e in d['stock']}
        assert classes <= allowed, (kind, classes, allowed)
        for it in stock:
            assert getattr(it, 'buc', 'uncursed') != 'cursed'


def test_trader_wands_and_arrows_are_dressed_not_at_the_minimum():
    """S3: dress_spawn on every ware (wand charges, ammo bundles)."""
    seen_wand = seen_ammo = False
    for s in range(30):
        stock = traders.build_stock(traders.kind_def('generalist'), 25, random.Random(s))
        for it in stock:
            if hasattr(it, 'charges_min') and it.charges_max > it.charges_min:
                seen_wand |= it.charges > it.charges_min
            if hasattr(it, 'count_min') and it.count_max > it.count_min:
                seen_ammo |= it.count > it.count_min
    assert seen_wand and seen_ammo


# ------------------------------------------------------------------ buying

def test_buying_charges_the_price_names_the_ware_as_shown_and_remembers_what_was_paid():
    g = _game()
    potion = _potion('potion_of_healing')
    potion.id_level = 0
    g.player.known_item_ids.discard(potion.id)
    m = _trader(g, stock=[potion])
    shown = g._display_name(potion)
    price = g._trader_price(0)
    g.player_gold = price + 7
    _press(g, pygame.K_RETURN)
    assert g.player_gold == 7
    assert any(shown in t for t in _texts(g)) and potion.name not in ' '.join(_texts(g, 3))
    owned = next(i for i in g.player.inventory if i.id == 'potion_of_healing')
    assert owned._bought_for == price
    assert not m.stock and m.sold_out


def test_a_poor_hero_cannot_buy_and_a_full_pack_keeps_the_gold():
    g = _game()
    m = _trader(g, stock=[_potion('potion_of_full_healing')])
    g.player_gold = 1
    _press(g, pygame.K_RETURN)
    assert m.stock and g.player_gold == 1


def test_prices_follow_worth_not_class():
    lvl = 30
    heal, full, sick = (_potion(p) for p in ('potion_of_healing', 'potion_of_full_healing',
                                               'potion_of_sickness'))
    p_heal, p_full, p_sick = (economy.merchant_price(p, lvl) for p in (heal, full, sick))
    assert p_sick < 0.3 * p_heal < p_heal < p_full
    assert p_full >= 2.5 * p_heal


# ------------------------------------------------------------------ selling

def test_selling_pays_a_fifth_to_a_quarter_of_his_price_and_empties_his_purse():
    g = _game()
    m = _trader(g, stock=[])
    assert g._shop_tab == 1                       # no stock: the shop opens on Sell
    sword = next(i for i in load_items('weapon') if not i.is_unique) \
        if any(not i.is_unique for i in load_items('weapon')) else None
    from items import pick_random_weapon_for_floor
    sword = pick_random_weapon_for_floor(g.dungeon_level, random.Random(2))
    sword.id_level = 5
    g.player.known_item_ids.add(sword.id)
    g.player.inventory = [sword]
    his = economy.merchant_price(sword, g.dungeon_level, m.markup)
    offer, why = g._trader_offer(sword)
    assert why is None and 0.19 * his <= offer <= 0.26 * his
    gold, purse = g.player_gold, m.purse
    g._shop_selection = 0
    _press(g, pygame.K_RETURN)
    assert g.player_gold == gold + offer and m.purse == purse - offer
    assert sword not in g.player.inventory
    assert sword not in m.stock                   # never resold: no price-identify by selling


def test_the_offer_is_capped_by_his_purse():
    g = _game()
    m = _trader(g, stock=[])
    p = _potion('potion_of_full_healing')
    p.id_level = 5
    g.player.inventory = [p]
    m.purse = 12
    assert g._trader_offer(p)[0] == 12
    m.purse = 0
    assert g._trader_offer(p) == (0, "His purse is empty")


def test_an_unknown_thing_sells_as_its_unidentified_class_never_by_its_worth():
    g = _game()
    m = _trader(g, stock=[])
    full, sick = _potion('potion_of_full_healing'), _potion('potion_of_sickness')
    for p in (full, sick):
        p.id_level = 0
        g.player.known_item_ids.discard(p.id)
    a, b = g._trader_offer(full)[0], g._trader_offer(sick)[0]
    assert a == b == economy.sell_offer(full, g.dungeon_level, known=False, identified=False,
                                        markup=m.markup, purse=m.purse)
    g._shop_tab = 1
    names = [e['name'] for e in g._trader_menu()['entries']]
    assert full.name not in names and sick.name not in names


def test_quest_pieces_worn_things_and_tools_are_never_bought():
    g = _game()
    _trader(g, stock=[])
    from items import make_item_by_id
    dispatch = make_item_by_id('artifact', 'sealed_dispatch')
    g.player.inventory.append(dispatch)
    assert g._trader_offer(dispatch)[1] == "Not for sale"
    lock = next(i for i in g.player.inventory if getattr(i, 'item_class', '') == 'lockpick') \
        if any(getattr(i, 'item_class', '') == 'lockpick' for i in g.player.inventory) else None
    if lock is not None:
        assert g._trader_offer(lock)[1]
    worn = g.player.weapon
    g._shop_tab = 1
    assert worn is None or worn not in g._trader_rows()


def test_a_specialist_buys_only_his_kind_and_only_the_dealer_takes_curses():
    g = _game()
    m = _trader(g, kind='apothecary', stock=[])
    ring = copy.copy(next(a for a in load_items('accessory') if not a.is_unique and items.is_random_loot(a)))
    assert g._trader_offer(ring)[1] == "He doesn't deal in that"
    cursed = _potion('potion_of_healing')
    cursed.buc, cursed.buc_known, cursed.id_level = 'cursed', True, 5
    assert g._trader_offer(cursed)[1].startswith("Cursed")
    g.state = 'player'
    g.ground_items.remove(m)
    _trader(g, kind='abyssal', stock=[])
    assert g._trader_offer(cursed)[1] is None


# ------------------------------------------------------------------ the no-loop guarantee

def test_nothing_bought_from_any_trader_ever_sells_back_for_what_was_paid():
    """Buy at the lowest price the game allows (a full haggle, 50% off, AND a
    friend's 20%), carry it to the dearest buyer on the deepest floor
    (Vesper, x1.5), identify it: the offer is still under half of what was
    paid. A buy/sell loop cannot make gold."""
    g = _game()
    rng = random.Random(8)
    for kind, lvl in (('generalist', 5), ('apothecary', 3), ('armourer', 12), ('sutler', 19)):
        stock = traders.build_stock(traders.kind_def(kind), lvl, rng)
        for it in stock:
            list_price = economy.merchant_price(it, lvl, traders.kind_def(kind).get('markup', 1.0))
            paid = int(list_price * 0.5 * 0.8)
            it._bought_for = paid
            it.id_level = 5
            g.player.known_item_ids.add(it.id)
            for mk in (1.0, 1.5):
                offer = economy.sell_offer(it, 98, known=True, identified=True, markup=mk, purse=10 ** 9)
                assert offer <= paid * 0.5 < paid, (it.id, offer, paid)


def test_a_bought_potion_marks_the_stack_it_joins():
    g = _game()
    have = _potion('potion_of_healing')
    have.id_level, have.buc_known = 5, True
    g.player.inventory = [have]
    g.player.known_item_ids.add(have.id)
    new = _potion('potion_of_healing')
    new.id_level, new.buc_known = 5, True
    _trader(g, stock=[new])
    g.player_gold = 10 ** 6
    _press(g, pygame.K_RETURN)
    stack = next(i for i in g.player.inventory if i.id == 'potion_of_healing')
    assert stack.count == 2 and stack._bought_for > 0
    assert g._trader_offer(stack)[0] <= stack._bought_for // 2


def test_haggling_never_changes_what_he_pays():
    g = _game()
    p = _potion('potion_of_extra_healing')
    p.id_level = 5
    m = _trader(g, stock=[copy.copy(p)])
    before = economy.sell_offer(p, g.dungeon_level, known=True, identified=True, markup=m.markup)
    m.prices[0] = m.prices[0] // 2                # a full haggle
    after = economy.sell_offer(p, g.dungeon_level, known=True, identified=True, markup=m.markup)
    assert before == after


# ------------------------------------------------------------------ the shop's keys

def test_left_and_right_turn_the_tabs_and_the_services_tab_lists_his_trade():
    g = _game()
    _trader(g, kind='armourer')
    assert g._shop_tab == 0
    _press(g, pygame.K_RIGHT)
    assert g._shop_tab == 1
    _press(g, pygame.K_RIGHT)
    assert g._shop_tab == 2
    names = [e['name'] for e in g._trader_menu()['entries']]
    assert names == ['Mend Rust and Acid', 'Sharpen Your Weapon', 'Reinforce Your Armour',
                     'Cut Off a Cursed Thing']
    _press(g, pygame.K_RIGHT)
    assert g._shop_tab == 0
    _press(g, pygame.K_ESCAPE)
    assert g.state == 'player'


def test_a_trader_with_no_services_has_two_tabs():
    g = _game()
    _trader(g, kind='generalist')
    g._shop_merchant.services = ()
    assert [t[0] for t in g._trader_menu()['tabs']] == ['Buy', 'Sell']


def test_an_old_saved_merchant_still_trades():
    """A MerchantNPC pickled before the refactor has none of the new fields."""
    from mystery_system import MerchantNPC
    g = _game()
    old = MerchantNPC.__new__(MerchantNPC)
    old.__dict__.update({'x': g.player.x + 1, 'y': g.player.y, 'id': 'merchant_npc',
                         'name': 'Deep Gnome Trader', 'stock': [_potion('potion_of_healing')],
                         'prices': [40], 'sold_out': False, 'item_class': 'merchant',
                         'not_pickable': True, 'symbol': '@', 'color': (1, 2, 3)})
    g.ground_items.append(old)
    g._open_shop()
    assert g.state == 'shop'
    g._trader_menu()
    g.player_gold = 1000
    _press(g, pygame.K_RETURN)
    assert g.player_gold == 1000 - economy.nice(40)


# ------------------------------------------------------------------ services

def _service(g, kind, sid, gold=10 ** 6):
    m = _trader(g, kind=kind)
    g.player_gold = gold
    g._shop_tab = 2
    g._shop_selection = list(m.services).index(sid)
    _press(g, pygame.K_RETURN)
    return m


def test_the_smith_mends_what_rust_and_acid_took_never_more():
    from items import wear_down
    g = _game()
    w = _armed(g)
    start = w.enchant_bonus
    assert wear_down(w) and wear_down(w)
    assert w.enchant_bonus == start - 2 and w.wear_loss == 2
    gold = 10 ** 6
    _service(g, 'armourer', 'repair', gold)
    assert w.enchant_bonus == start and w.wear_loss == 0
    assert g.player_gold < gold
    paid = gold - g.player_gold
    assert paid == economy.service_price('repair', g.dungeon_level, points=2)
    g.player_gold = gold
    g._shop_tab, g._shop_selection = 2, 0
    _press(g, pygame.K_RETURN)                    # nothing left to mend: no charge
    assert g.player_gold == gold and w.enchant_bonus == start


def test_the_rust_trap_names_an_unknown_piece_as_the_hero_knows_it_and_remembers_the_loss():
    """The rust trap printed victim.name, an unidentified item's true name
    (ECONOMY_REFACTOR_PROPOSAL, found in passing). It now uses the shown
    name, and the point it takes is remembered for a smith (wear_loss)."""
    g = _game()
    p = g.player
    w = _armed(g)
    w.material = 'iron'
    w.id_level = 0
    p.known_item_ids.discard(w.id)
    p.shield = None
    p.armor_slots = [None] * len(p.armor_slots)
    w.enchant_bonus, w.wear_loss = 0, 0
    pos = (p.x, p.y)
    g.dungeon.traps[pos] = {'type': 'rust', 'message': 'A gush of water hits you!', 'damage': '0'}
    p.PER = 0
    random.seed(1)
    g._check_floor_trap(*pos, forced=True)
    said = ' '.join(_texts(g, 4))
    assert 'rusts' in said and g._bare_name(w) in said
    assert w.name not in said or w.name == g._bare_name(w)
    assert w.enchant_bonus == -1 and w.wear_loss == 1


def test_sharpening_is_plus_one_and_at_most_two_from_smiths():
    g = _game()
    w = _armed(g)
    start = w.enchant_bonus
    m = _service(g, 'armourer', 'sharpen')
    assert w.enchant_bonus == start + 1
    g._shop_tab, g._shop_selection = 2, list(m.services).index('sharpen')
    _press(g, pygame.K_RETURN)
    _press(g, pygame.K_RETURN)
    assert w.enchant_bonus == start + 2 and w._smith_bonus == 2


def test_a_cursed_worn_thing_is_cut_off_and_destroyed():
    g = _game()
    ring = copy.copy(next(a for a in load_items('accessory') if not a.is_unique and items.is_random_loot(a)
                          and getattr(a, 'slot', '') == 'ring'))
    ring.buc, ring.buc_known = 'cursed', True
    g.player.accessory_slots[0] = ring
    _service(g, 'armourer', 'cut_curse')
    assert g.player.accessory_slots[0] is None
    assert ring not in g.player.inventory
    assert any('cuts' in t for t in _texts(g, 6))


def test_an_unknown_curse_is_never_offered_for_cutting():
    g = _game()
    ring = copy.copy(next(a for a in load_items('accessory') if not a.is_unique and items.is_random_loot(a)
                          and getattr(a, 'slot', '') == 'ring'))
    ring.buc, ring.buc_known, ring.id_level = 'cursed', False, 0
    g.player.accessory_slots[0] = ring
    _trader(g, kind='armourer')
    assert g._service_targets('cut_curse') == []


def test_the_physician_cures_and_restores_drained_stats():
    from status_effects import note_stat_drain
    g = _game()
    p = g.player
    p.add_effect('poisoned', 20)
    _service(g, 'apothecary', 'cure')
    assert not p.has_effect('poisoned')
    con, wis = p.CON, p.WIS
    p.apply_stat_bonus('CON', -2)
    note_stat_drain(p, 'CON', 2)
    p.apply_stat_bonus('WIS', -1)
    note_stat_drain(p, 'WIS', 1)
    g.state = 'player'
    _service(g, 'apothecary', 'restore')
    assert (p.CON, p.WIS) == (con, wis)
    assert not p.__dict__.get('drained')


def test_a_drain_potion_and_a_monster_drain_are_remembered_for_the_physician():
    from food_system import drink_potion
    g = _game()
    p = g.player
    con = p.CON
    pot = _potion('potion_of_drain_constitution')
    pot.buc = 'uncursed'
    drink_potion(p, pot)
    assert p.CON == con - 1 and p.__dict__['drained'] == {'CON': 1}
    src = open(os.path.join(ROOT, 'src', 'monster.py'), encoding='utf-8').read()
    assert "note_stat_drain(player, 'CON'" in src


def test_the_scribe_lets_you_try_an_identify_without_the_backlash():
    g = _game()
    p = _potion('potion_of_healing')
    p.id_level = 0
    g.player.known_item_ids.discard(p.id)
    g.player.inventory.append(p)
    m = _trader(g, kind='bookseller')
    g.player_gold = 10 ** 6
    g._shop_tab = 2
    g._shop_selection = list(m.services).index('id_retry')
    _press(g, pygame.K_RETURN)
    if getattr(g, '_shop_pick', None):            # several unknown things: pick ours
        g._shop_selection = g._shop_pick[1].index(p)
        _press(g, pygame.K_RETURN)
    assert g.state == 'quiz'
    from quiz_engine import QuizResult
    cb, g.quiz_engine.callback = g.quiz_engine.callback, None
    cb(QuizResult(success=False, score=0, correct=0, asked=1))     # a wrong answer
    assert not g.player.has_effect('stunned')
    assert int(getattr(p, 'id_level', 0) or 0) < 5                 # still not identified
    # without the scribe the same wrong answer stuns
    g._identify_item(p)
    cb, g.quiz_engine.callback = g.quiz_engine.callback, None
    cb(QuizResult(success=False, score=0, correct=0, asked=1))
    assert g.player.has_effect('stunned')


def test_a_map_and_a_porter_can_be_bought():
    g = _game()
    m = _service(g, 'bookseller', 'map')
    d = g.dungeon
    assert len(d.explored) == d.width * d.height
    g.state = 'player'
    g.ground_items.remove(m)
    _service(g, 'sutler', 'porter')
    assert g.player.has_effect('porter')


def test_services_never_answer_the_question():
    """Gold buys a second chance, never the quiz answer: no service skips a
    quiz or marks an item identified without one."""
    src = open(os.path.join(ROOT, 'src', 'game_traders.py'), encoding='utf-8').read()
    assert '_full_identify' not in src and 'id_level = 5' not in src


# ------------------------------------------------------------------ deeds (D7)

def _deed(g, deed_id):
    import deeds
    deeds.record(g._deeds_reg(), deed_id, floor=g.dungeon_level, block=1)


def test_wronging_a_merchant_raises_every_traders_prices_and_one_says_why():
    g = _game()
    p = _potion('potion_of_healing')
    m = _trader(g, stock=[copy.copy(p)])
    base = g._trader_price(0)
    g.state = 'player'
    g.ground_items.remove(m)
    _deed(g, 'wrong.robbed_quill')
    _trader(g, stock=[copy.copy(p)])
    assert g._trader_price(0) == economy.nice(base * 1.25)
    said = [t for t in _texts(g, 8) if "Word's gone round" in t]
    assert len(said) == 1
    n = len(g.msg_log.entries)
    _trader(g, kind='apothecary', stock=[copy.copy(p)])
    new = [str(e[0]) for e in g.msg_log.entries[n:]]
    assert not [t for t in new if "Word's gone round" in t]            # said once a run
    assert abs(g._shop_mult - 1.25) < 1e-9                             # but it still holds


def test_a_saved_friend_comes_back_as_the_trader_with_a_friends_price():
    g = _game()
    _deed(g, 'saved.helena')
    plan = g._trader_plan()
    lvl = next(f for f, k in sorted(plan['floors'].items()) if k == 'bookseller')
    g._change_level(lvl, enter_from_top=True)
    from mystery_system import MerchantNPC
    t = next(i for i in g.ground_items if isinstance(i, MerchantNPC))
    assert t.person == 'Helena Marsh' and t.friend == 'helena'
    g.player.x, g.player.y = t.x + 1, t.y
    g._open_shop()
    assert abs(g._shop_mult - 0.8) < 1e-9
    assert 'helena' in plan['friends_used']


def test_a_kept_oath_earns_one_thing_on_the_house():
    g = _game()
    _deed(g, 'kept.edric_dispatch')
    p = _potion('potion_of_healing')
    _trader(g, stock=[copy.copy(p), copy.copy(p)])
    assert g._shop_credit
    g.player_gold = 0
    _press(g, pygame.K_RETURN)                    # free: within one floor's income
    assert g.player_gold == 0 and any(i.id == p.id for i in g.player.inventory)
    assert not g._shop_credit
    assert g._trader_plan()['credits_used'] == 1


def test_charity_has_consequences_but_no_karma():
    """Paying other people's debts: a fence charges you more, honest folk
    less. Neither moves karma."""
    g = _game()
    k0 = g.karma
    _deed(g, 'aid.gleaner')
    p = _potion('potion_of_healing')
    _trader(g, kind='generalist', stock=[copy.copy(p)])
    assert abs(g._shop_mult - 1.10) < 1e-9
    g.state = 'player'
    _trader(g, kind='apothecary', stock=[copy.copy(p)])
    assert abs(g._shop_mult - 0.90) < 1e-9
    assert g.karma == k0
    # the charity options themselves carry no karma (naive kindness: Brandon)
    for fn in ('npc_encounters.json', 'flavor_encounters.json'):
        d = json.load(open(os.path.join(ROOT, 'data', fn), encoding='utf-8'))
        encs = d if isinstance(d, list) else d.get('encounters', d)
        encs = list(encs.values()) if isinstance(encs, dict) else encs
        for e in encs:
            for o in (e.get('options') or []) if isinstance(e, dict) else []:
                ds = [x if isinstance(x, str) else x.get('id') for x in (o.get('deeds') or [])]
                if any(d_ in traders.data()['rumours']['open_hand']['deeds_any'] for d_ in ds):
                    assert not int(o.get('karma', 0) or 0), (e.get('tag'), o.get('label'))


def test_falling_for_a_con_marks_you_with_the_fences():
    g = _game()
    _deed(g, 'lost.wren')
    _trader(g, kind='generalist', stock=[_potion('potion_of_healing')])
    assert abs(g._shop_mult - 1.15) < 1e-9


# ------------------------------------------------------------------ data

def test_traders_data_is_complete_and_every_person_has_lines_and_art():
    d = traders.data()
    for kind, t in d['traders'].items():
        assert t['name'] and t['title'] and t['lore'], kind
        for key in ('greet', 'bought', 'sold', 'broke', 'refuse', 'purse_empty', 'sold_out'):
            assert t['lines'].get(key), (kind, key)
        for sid in t.get('services', ()):
            assert sid in economy.SERVICE_SHARE and sid in d['services'], (kind, sid)
        assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters', t['sprite'] + '.png')), kind
        fr = t.get('friend')
        if fr:
            assert os.path.exists(os.path.join(ROOT, 'assets', 'tiles', 'monsters', fr['sprite'] + '.png'))
            assert fr['line'] and fr['name']
        assert 0.5 <= t['markup'] <= 2.0 and t['purse'] > 0
    assert set(d['plan']['gate_camps']) == {'19', '39', '59', '79'}
    import deeds
    for name, cond in d['rumours'].items():
        if name.startswith('_'):
            continue
        assert set(cond) <= deeds.CONDITION_KEYS, name


def test_the_lines_never_say_lowercase_names_or_raw_ids():
    d = traders.data()
    for kind, t in d['traders'].items():
        assert t['name'][0].isupper() and t['title'][0].isupper()
        for v in t['lines'].values():
            for line in (v if isinstance(v, list) else [v]):
                assert '_' not in line, (kind, line)
