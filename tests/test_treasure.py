"""Coin weight, treasure and the rare draught (Brandon's decisions D2 and D8,
2026-10-18; src/treasure.py, src/game_purse.py).

D2: "a very real lesson about cash and metals; they have value but are hard
to move. Make sure player can DROP gold ... 1 gp is 1/10th an oz ... Gems or
TREASURE ... could add to the score."
D8: "No WIS purchase, possible rare shop appearance?"

Logic tests on a real headless Game. How heavy coin FEELS in a run, and
whether the shop reads well, is Brandon's play-test: Claude cannot drive
Pygame.
"""
import copy
import json
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import economy  # noqa: E402
import items  # noqa: E402
import traders  # noqa: E402
import treasure  # noqa: E402

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(name='__test_treasure__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(7)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.monsters = [m for m in g.monsters if not getattr(m, '_npc_encounter_tag', None)]
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    g.ground_items = [i for i in g.ground_items
                      if (getattr(i, 'x', -9), getattr(i, 'y', -9)) != (g.player.x, g.player.y)]
    return g


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def _texts(g, n=8):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _piles_here(g):
    from items import GoldPile
    return [i for i in g.ground_items if isinstance(i, GoldPile)
            and (i.x, i.y) == (g.player.x, g.player.y)]


def _trader(g, kind='generalist', level=None, stock=None):
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


# ===================================================================== coin

def test_a_gold_piece_weighs_a_tenth_of_an_ounce():
    assert treasure.COINS_PER_LB == 160
    assert treasure.coin_weight(160) == 1.0
    assert treasure.coin_weight(16000) == 100.0          # a full pack at Strength 10
    assert treasure.coins_in(2.5) == 400
    assert treasure.weight_text(1200) == '7.5 lb' and treasure.weight_text(3200) == '20 lb'


def test_the_purse_counts_toward_carry_weight():
    g = _game()
    g.player_gold = 0
    base = g.player.get_current_weight()
    g.player_gold = 1600
    assert g.player.purse_coins == 1600
    assert abs(g.player.get_current_weight() - (base + 10.0)) < 1e-6
    g.player_gold -= 800                                  # spending lightens the pack
    assert abs(g.player.get_current_weight() - (base + 5.0)) < 1e-6
    g._set_gold_quietly(0)
    assert g.player.purse_coins == 0


def test_enough_gold_makes_the_hero_burdened_and_blocks_pickups():
    g = _game()
    p = g.player
    g.player_gold = 0
    spare = p.burden_threshold() - p.get_current_weight()
    g.player_gold = treasure.coins_in(spare) + 160        # a pound past the line
    assert p.is_burdened() and p.update_burden() == 'on'
    g.player_gold = g.player_gold + p.coin_room() + 160   # past the limit itself
    assert p.is_overloaded()
    heavy = copy.copy(next(i for i in items.load_items('potion')))
    assert p.add_to_inventory(heavy) is False
    assert 'gold weighs' in p.too_heavy_message()


def test_the_sidebar_and_sheets_show_what_the_purse_weighs():
    src = open(os.path.join(ROOT, 'src', 'ui.py'), encoding='utf-8').read()
    assert 'def _purse(' in src and 'weight_text(gold)' in src
    rsrc = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert rsrc.count('_gwt(self.player_gold)') == 2          # Kit header and sheet header
    # (The rendered lines are checked at every window size by the UI gates:
    # tools/ui/capture.py, tests/test_ui_gates.py.)


def test_a_pile_is_picked_up_only_as_far_as_the_hero_can_carry():
    from items import add_gold_to_tile
    g = _game()
    g.player_gold = 0
    room = g.player.coin_room()
    assert room > 340
    g.player_gold = room - 340                     # room for exactly 340 more
    add_gold_to_tile(g.ground_items, 1200, g.player.x, g.player.y)
    turn = g.turn_count
    g._pickup()
    assert "You can only carry 340 of the 1,200 gold. The rest stays on the floor." in _texts(g)
    pile = _piles_here(g)[0]
    assert pile.amount == 860
    assert g.turn_count == turn + 1
    # Full: nothing taken and no turn spent.
    g._pickup()
    assert pile.amount == 860 and g.turn_count == turn + 1
    assert any('cannot carry any more gold' in t for t in _texts(g))


def test_dropping_gold_through_the_drop_menu_makes_the_heros_own_pile():
    from items import is_found_gold
    g = _game()
    g.player_gold = 1000
    _press(g, pygame.K_d, 'd')
    from game_states import STATE_DROP_MENU, STATE_DROP_GOLD_INPUT, STATE_PLAYER
    assert g.state == STATE_DROP_MENU
    assert type(g.drop_menu_items[0]).__name__ == '_GoldDropEntry'
    _press(g, pygame.K_RETURN)
    assert g.state == STATE_DROP_GOLD_INPUT
    for ch in '320':
        _press(g, getattr(pygame, f'K_{ch}'), ch)
    _press(g, pygame.K_RETURN)
    assert g.state == STATE_PLAYER and g.player_gold == 680
    pile = _piles_here(g)[0]
    assert pile.amount == 320 and not is_found_gold(pile)
    assert any('(2.0 lb lighter)' in t for t in _texts(g))
    # A second drop on the tile joins the hero's own pile.
    g._drop_gold(80)
    assert len(_piles_here(g)) == 1 and _piles_here(g)[0].amount == 400


def test_a_gold_ring_doubles_found_gold_once_and_never_the_heros_own(monkeypatch):
    from items import add_gold_to_tile
    g = _game()
    ring = types.SimpleNamespace(gold_multiplier=2.0)
    monkeypatch.setattr(type(g.player), 'equipped_accessories', property(lambda self: [ring]))
    g.player_gold = 0
    room = g.player.coin_room()
    g.player_gold = room - 100
    add_gold_to_tile(g.ground_items, 100, g.player.x, g.player.y)   # found: doubled to 200
    g._pickup()
    pile = _piles_here(g)[0]
    assert pile.amount == 100                                        # 100 taken, 100 left
    g._set_gold_quietly(0)                                           # make room
    g._pickup()
    assert g.player_gold == 100          # the rest: not doubled a second time
    g._set_gold_quietly(0)
    add_gold_to_tile(g.ground_items, 50, g.player.x, g.player.y, found=False)
    g._pickup()
    assert g.player_gold == 50           # the hero's own gold: never doubled


def test_gold_given_that_will_not_fit_stays_on_the_floor_or_comes_as_gems():
    g = _game()
    g.player_gold = 0
    room = g.player.coin_room()
    g.player_gold = room - 100
    earned = g.gold_earned
    got = g._gain_gold(5000)                       # a find: the rest at his feet
    assert got['taken'] == 100 and got['spilled'] == 4900
    pile = _piles_here(g)[0]
    assert pile.amount == 4900 and not items.is_found_gold(pile)   # no ring doubling later
    assert g.gold_earned == earned + 5000                         # booked once
    g.ground_items.remove(pile)
    g.dungeon_level = 50
    got = g._gain_gold(8000, paid=True)            # a person paying: the rest in gems
    gems = got['gems']
    assert gems and all(treasure.is_treasure(x) and x.kind == 'gem' for x in gems)
    assert sum(treasure.total_value(x) for x in gems) + got['spilled'] == 8000
    assert all(treasure.is_valued(g.player, x) for x in gems)


def test_old_saves_get_their_purse_weight_on_load(tmp_path):
    from save_system import delete_save, load_game, save_game
    name = '__test_treasure_save__'
    try:
        g = _game(name)
        g.player_gold = 3200
        ruby = treasure.make('treasure_burmese_ruby')
        g.player.inventory.append(ruby)
        treasure.appraise(g.player, ruby)
        assert save_game(g)
        state = load_game(name)
        # An old save: the player has no purse mirror, no seen or valued sets
        # (unpickled again through Player.__setstate__, as a load does).
        import pickle
        for k in ('purse_coins', 'appraised_treasure', 'seen_item_ids'):
            state['player'].__dict__.pop(k, None)
        state['player'] = pickle.loads(pickle.dumps(state['player']))
        g2 = _game(name)
        g2.load_state(state)
        assert g2.player.purse_coins == 3200 and abs(g2.player.purse_weight() - 20.0) < 1e-6
        assert hasattr(g2.player, 'appraised_treasure')
        assert any(i.id == 'treasure_burmese_ruby' for i in g2.player.inventory)
    finally:
        delete_save(name)


def test_a_thief_takes_coin_off_the_heros_back_and_likes_treasure():
    import theft
    g = _game()
    g.player_gold = 1600
    w = g.player.get_current_weight()
    m = types.SimpleNamespace(alive=True, name='Cutpurse', kind='bandit', x=g.player.x + 1,
                              y=g.player.y, after_theft='flee', _aware=False, _flee_timer=0,
                              is_unique_named=False, proper_noun=False)
    msg = theft.steal(g, m, 'gold', random.Random(1))
    assert 'cuts your purse' in msg
    assert g.player.get_current_weight() < w - 1.0      # lighter by what was cut
    assert 'Treasure' in theft.BRIGHT_KINDS
    ruby = treasure.make('treasure_burmese_ruby')
    g.player.inventory.append(ruby)
    assert ruby in theft.stealable(g.player)


def test_the_bribe_is_paid_in_coin_and_lightens_the_purse():
    src = open(os.path.join(ROOT, 'src', 'game_menus.py'), encoding='utf-8').read()
    block = src[src.index('def _activate_gold_offering'):]
    block = block[:block.index('\n    def ', 10)]
    assert 'self.player_gold = _purse - cost' in block      # the setter mirrors the weight


def test_brisingamen_tears_never_overload_the_hero():
    src = open(os.path.join(ROOT, 'src', 'main.py'), encoding='utf-8').read()
    block = src[src.index("tears_of_freya"):]
    block = block[:block.index('break  # only first')]
    assert 'coin_room()' in block and 'self._gain_gold(' in block
    # The amulet is the one with the tears in the data.
    brisingamen = items.make_item_by_id('accessory', 'brisingamen')
    assert brisingamen is not None and brisingamen.tears_of_freya


def test_all_three_gold_rings_double_found_gold_by_the_same_rule():
    """Draupnir, Andvaranaut and the Ring of the Nibelung carry
    gold_multiplier; game_purse._pickup_gold reads that field, once a pile."""
    rings = [items.make_item_by_id('accessory', i)
             for i in ('draupnir', 'andvaranaut', 'ring_of_the_nibelung')]
    assert all(r is not None and r.gold_multiplier == 2.0 for r in rings)
    src = open(os.path.join(ROOT, 'src', 'game_purse.py'), encoding='utf-8').read()
    assert "getattr(acc, 'gold_multiplier', 0)" in src and '_ring_doubled' in src


def test_treasure_in_the_kit_offers_drop_and_lore_only():
    g = _game()
    ruby = treasure.make('treasure_burmese_ruby')
    g.player.add_to_inventory(ruby)
    acts = {a['id'] for a in g._item_actions(ruby, 'pack')}
    assert acts == {'drop', 'lore'}
    g._do_drop_item(ruby)
    assert any(i is ruby for i in g.ground_items)
    from game_states import STATE_PLAYER
    g.state = STATE_PLAYER
    g.ground_items = [i for i in g.ground_items if i is ruby or (i.x, i.y) != (g.player.x, g.player.y)]
    ruby.x, ruby.y = g.player.x, g.player.y
    g._pickup()
    assert ruby in g.player.inventory
    assert any('Worth thousands of gold' in t for t in _texts(g))


def test_an_encounter_reward_too_heavy_to_carry_comes_partly_in_gems():
    g = _game()
    g.dungeon_level = 45
    g._npc_encounter_active = {'tag': 't', 'name': 'Lost Merchant', 'options': []}
    g.player_gold = 0
    g.player_gold = g.player.coin_room() - 50
    g._apply_npc_reward({'type': 'gold', 'amount': 6000})
    gems = [i for i in g.player.inventory if treasure.is_treasure(i)]
    assert gems and any('paid in gems' in t for t in _texts(g))


def test_an_altar_tribute_can_be_paid_in_treasure_and_gives_no_change():
    src = open(os.path.join(ROOT, 'src', 'game_divine.py'), encoding='utf-8').read()
    block = src[src.index("if m.get('gold_cost', 0) > 0:"):]
    block = block[:block.index('# Consume key item')]
    assert 'self._pay_gold(_cost, change_purse=0' in block
    assert 'self._purse_wealth()' in src


# ===================================================================== treasure data

def test_treasure_kinds_have_real_weights_values_and_lore():
    kinds = treasure.kinds()
    assert 12 <= len(kinds) <= 20
    for kid, d in kinds.items():
        assert kid.startswith('treasure_'), kid
        assert d['kind'] in ('gem', 'jewellery', 'coins', 'art'), kid
        w, v = float(d['weight']), int(d['value'])
        assert v > 0 and d['lore'] and d['name'][0].isupper(), kid
        if d['kind'] == 'gem':
            assert 0.01 <= w <= 0.05, kid
        elif d['kind'] in ('jewellery', 'coins'):
            assert 0.1 <= w <= 1.0, kid
        else:
            assert w >= 2.0, kid
        assert int(d['min_level']) >= 1 and int(d['peak_floor']) > 0 and float(d['peak_weight']) > 0
    by = {k: v for k, v in kinds.items()}
    assert by['treasure_gold_idol']['weight'] == 10.0
    assert by['treasure_silver_candelabra']['weight'] == 6.0
    assert by['treasure_arras_tapestry']['weight'] == 20.0
    # The lesson in the data: silver plate is worth less than its weight in gold coin.
    cand = by['treasure_silver_candelabra']
    assert cand['value'] < cand['weight'] * treasure.COINS_PER_LB
    # Gems carry far more wealth per pound than coin.
    ruby = by['treasure_burmese_ruby']
    assert ruby['value'] / ruby['weight'] > 100 * treasure.COINS_PER_LB


def test_every_treasure_and_the_draught_have_their_own_64px_art():
    import renderer
    with open(os.path.join(ROOT, 'tools', 'content', 'genart', 'installed_items.json'),
              encoding='utf-8') as f:
        installed = set(json.load(f)['items'])
    for kid in list(treasure.kinds()) + ['draught_of_mimir']:
        path = os.path.join(ROOT, 'assets', 'tiles', 'items', f'{kid}.png')
        assert os.path.exists(path), kid
        assert renderer._resolve_item_sprite_path(kid).endswith(f'{kid}.png')
        assert kid in installed, kid
        with open(path, 'rb') as f:
            head = f.read(24)
        assert (int.from_bytes(head[16:20], 'big'), int.from_bytes(head[20:24], 'big')) == (64, 64)
    import lore_art
    assert 'treasure' in lore_art.ITEM_CATEGORIES
    assert lore_art.encyclopedia_ref('treasure', {'_id': 'treasure_burmese_ruby'}) == \
        ('item', 'treasure_burmese_ruby')


def test_treasure_is_known_by_sight_and_never_cursed():
    ruby = treasure.make('treasure_burmese_ruby')
    assert ruby.id_level == 5 and ruby.buc_known and not ruby.cursed
    ruby.cursed = True
    assert not ruby.cursed and ruby.buc == 'uncursed'
    assert ruby.unidentified_name == ruby.name


def test_treasure_stacks_by_kind():
    g = _game()
    a, b = treasure.make('treasure_baltic_amber'), treasure.make('treasure_baltic_amber')
    assert g.player.add_to_inventory(a) and g.player.add_to_inventory(b)
    stacks = [i for i in g.player.inventory if i.id == 'treasure_baltic_amber']
    assert len(stacks) == 1 and stacks[0].count == 2
    assert 'Lump of Baltic Amber x2' == g._display_name(stacks[0])


def test_nothing_about_the_value_leaks_before_a_trader_values_it():
    g = _game()
    ruby = treasure.make('treasure_burmese_ruby')
    g.player.inventory.append(ruby)
    name_before = g._display_name(ruby)
    text = treasure.value_text(g.player, ruby)
    assert text == 'Worth thousands of gold (not yet valued)'
    assert '2,500' not in text and '2500' not in ' '.join(str(x[0]) for x in
                                                         g._menu_item_detail_lines(ruby))
    # What the hero can count on is the band's low end, never the true value.
    assert treasure.known_unit_value(g.player, ruby) == 1000
    _trader(g)                                       # a trader values it
    assert treasure.is_valued(g.player, ruby)
    assert treasure.value_text(g.player, ruby) == 'Valued at 2,500 gold'
    assert g._display_name(ruby) == name_before      # it looks the same either way
    import renderer
    assert renderer._resolve_item_sprite_path(ruby.id).endswith('treasure_burmese_ruby.png')


# ===================================================================== where it lies

def test_treasure_spawns_by_spawn_weight_never_by_a_floor_multiplier():
    rng = random.Random(3)
    shallow = [treasure.roll(3, rng) for _ in range(200)]
    deep = [treasure.roll(85, rng) for _ in range(200)]
    assert all(s is not None for s in shallow + deep)
    assert max(treasure.unit_value(s) for s in shallow) <= 700
    assert min(treasure.unit_value(s) for s in deep) >= 1800
    # A kind's value is the same on every floor.
    for s in shallow + deep:
        assert treasure.unit_value(s) == treasure.kinds()[s.id]['value']
    src = open(os.path.join(ROOT, 'src', 'treasure.py'), encoding='utf-8').read()
    assert 'dungeon_level' not in src


def test_chests_hold_treasure_where_lore_puts_it():
    import container_system
    with open(os.path.join(ROOT, 'data', 'chest_templates.json'), encoding='utf-8') as f:
        t = json.load(f)
    for k in ('jewelry_box', 'dragon_hoard', 'merchant_strongbox', 'crypt_chest', 'gilded_chest'):
        assert t[k]['loot_table'].get('treasure', 0) > 0, k
    assert 'treasure' not in t['apothecary_chest']['loot_table']
    box = types.SimpleNamespace(template_id='jewelry_box', tier=2, _gold_bonus_accum=0)
    random.seed(4)
    got = []
    for _ in range(40):
        got += container_system._generate_loot_from_template(box, 30)
    assert any(treasure.is_treasure(i) for i in got)
    assert treasure.coin_after_treasure(1000, 5000) == 250 and treasure.coin_after_treasure(1000, 100) == 900


def test_treasuries_vaults_and_lairs_hold_treasure():
    from level_manager import LevelManager
    found = []
    for lvl in (12, 30, 55, 75):
        for seed in range(12):
            random.seed(seed * 31 + lvl)
            items.bind_unique_registry(set())
            lm = LevelManager()
            _d, _m, ground = lm.generate(lvl)
            found += [i.id for i in ground if treasure.is_treasure(i)]
    assert len(found) >= 3 and len(set(found)) >= 2


def test_gate_boss_hoards_hold_treasure():
    import boss_levels
    for lvl, builder in ((60, boss_levels.generate_boss_level), ):
        random.seed(2)
        items.bind_unique_registry(set())
        out = builder(lvl)
        ground = out[2] if isinstance(out, tuple) else []
        assert sum(1 for i in ground if treasure.is_treasure(i)) == treasure.BOSS_HOARD_PIECES[60]


def test_creatures_carry_treasure_by_what_they_are():
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = json.load(f)
    by_purse = {}
    for mid, m in mons.items():
        if isinstance(m, dict):
            tr = m.get('treasure') or {}
            by_purse.setdefault(tr.get('purse'), []).append(float(tr.get('treasure_chance', 0) or 0))
    assert min(by_purse['hoard']) > 0                         # dragons sleep on it
    mean = {k: sum(v) / len(v) for k, v in by_purse.items()}
    assert mean['hoard'] > mean['noble_dead'] > mean['thief'] > 0
    assert max(by_purse['none']) == 0                         # beasts carry none
    assert max(by_purse['purse']) == 0                        # a working man's purse is coin
    assert max(by_purse['grave_goods']) == 0                  # grave goods are in the graves, dug
    g = _game()
    mon = types.SimpleNamespace(treasure={'gold': [0, 0], 'treasure_chance': 1.0,
                                          'treasure_kinds': ['gem']},
                                x=g.player.x, y=g.player.y, name='Young Red Dragon',
                                kind='young_red_dragon', is_unique_named=False, proper_noun=False)
    before = len(g.ground_items)
    g._drop_treasure(mon)
    dropped = [i for i in g.ground_items[before:] if treasure.is_treasure(i)]
    assert len(dropped) == 1 and dropped[0].kind == 'gem'


def test_rich_graves_hold_grave_goods_and_thrones_a_loose_stone():
    g = _game()
    from dungeon import GRAVE, THRONE
    px, py = g.player.x, g.player.y
    g.dungeon.tiles[py][px] = GRAVE
    g.dungeon_level = 20
    before = len(g.ground_items)
    random.seed(1)
    g._resolve_grave(3)
    goods = [i for i in g.ground_items[before:] if treasure.is_treasure(i)]
    assert goods and goods[0].kind in treasure.GRAVE_KINDS
    g.dungeon.tiles[py][px] = THRONE
    found = False
    for s in range(12):
        random.seed(s)
        before = len(g.ground_items)
        g._resolve_throne(1)
        found = found or any(treasure.is_treasure(i) for i in g.ground_items[before:])
    assert found


# ===================================================================== score

def test_treasure_carried_counts_toward_the_score_and_the_table(tmp_path, monkeypatch):
    import highscore_system as hs
    monkeypatch.setattr(hs, '_SCORE_FILE', str(tmp_path / 'highscores.json'))
    g = _game()
    base = g._calc_score()
    g.player_gold = 5000                              # coin does not score
    assert g._calc_score() == base
    g.player.inventory.append(treasure.make('treasure_gold_idol'))
    assert g._calc_score() == base + 5000
    assert g._end_treasure_text() == '5,000 gold (1 piece)'
    g._record_high_score(victory=False)
    row = hs.get_top(1)[0]
    assert row['treasure'] == 5000
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert src.count('("Treasure",') == 2              # the death and victory screens


def test_old_high_score_rows_read_with_no_treasure(tmp_path, monkeypatch):
    import highscore_system as hs
    f = tmp_path / 'highscores.json'
    f.write_text(json.dumps([{'name': 'Old', 'score': 10, 'level': 3, 'kills': 1, 'turns': 9}]),
                 encoding='utf-8')
    monkeypatch.setattr(hs, '_SCORE_FILE', str(f))
    assert hs.get_top(1)[0]['treasure'] == 0


# ===================================================================== traders

def test_traders_buy_treasure_near_full_value_whatever_they_deal_in():
    g = _game()
    g.dungeon_level = 50
    ruby = treasure.make('treasure_burmese_ruby')
    g.player.inventory.append(ruby)
    m = _trader(g, kind='apothecary', level=50)       # an apothecary still takes a ruby
    m.purse = 100000
    offer, why = g._trader_offer(ruby)
    assert why is None and offer == int(2500 * treasure.buy_rate())
    g.player_gold = 0
    g._shop_tab = 1
    g._trader_sell(ruby)
    assert ruby not in g.player.inventory and g.player_gold == offer


def test_a_sale_that_will_not_fit_in_the_purse_is_paid_in_gems():
    g = _game()
    g.dungeon_level = 60
    idol = treasure.make('treasure_gold_idol')
    g.player.inventory.append(idol)
    m = _trader(g, level=60)
    m.purse = 100000
    g.player_gold = 0
    g.player_gold = g.player.coin_room() - 200 + int(treasure.coin_weight(0))
    g._trader_sell(idol)
    gems = [i for i in g.player.inventory if treasure.is_treasure(i) and i.kind == 'gem']
    assert gems                                     # 4,500 offered, room for ~200 coin + the idol's 10 lb


def test_traders_sell_a_few_gems_at_a_small_markup_and_never_haggle_them():
    with open(os.path.join(ROOT, 'data', 'traders.json'), encoding='utf-8') as f:
        d = json.load(f)
    t = d['treasure']
    assert t['buy_rate'] < 1.0 < t['sell_markup'] and t['gem_stock']['generalist'] >= 1
    defn = {**traders.kind_def('generalist'), 'kind': 'generalist'}
    gems = [w for w in traders.build_stock(defn, 30, random.Random(2)) if treasure.is_treasure(w)]
    assert gems and all(w.kind == 'gem' for w in gems)
    g = _game()
    gem = treasure.make('treasure_badakhshan_lapis')
    m = _trader(g, stock=[gem])
    assert g._trader_price(0) == treasure.shop_price(gem) == 495
    g._shop_mult = 0.8                              # a friend's price: never below the exchange
    assert g._trader_price(0) == 495
    g._shop_mult = 1.25                             # a wronged guild: the rise applies
    assert g._trader_price(0) > 495
    g._shop_mult = 1.0
    _press(g, pygame.K_h, 'h')
    assert m.prices[0] == 495 and any('No haggling over gems' in t for t in _texts(g))


def test_no_buy_and_sell_loop_through_gems():
    gem = treasure.make('treasure_kashmir_sapphire')
    assert treasure.credit(gem) < treasure.shop_price(gem)
    gem._bought_for = treasure.shop_price(gem)
    assert economy.sell_offer(gem, 60, known=True, identified=True) < treasure.shop_price(gem)


def test_paying_with_treasure_when_coin_runs_short():
    g = _game()
    g.dungeon_level = 40
    sword = items.pick_random_weapon_for_floor(40, random.Random(3))
    m = _trader(g, level=40, stock=[sword])
    m.purse = 5000
    price = g._trader_price(0)
    ruby = treasure.make('treasure_burmese_ruby')        # credit 2,250
    brooch = treasure.make('treasure_saxon_brooch')      # credit 315
    g.player.inventory += [ruby, brooch]
    g.player_gold = max(0, price - 2250 + 100)           # coin and the ruby cover it
    plan = g._payment_plan(price)
    assert plan is not None and [it.id for it, _ in plan['take']] == ['treasure_burmese_ruby']
    coin_before = g.player_gold
    _press(g, pygame.K_RETURN)                           # buy
    assert sword in g.player.inventory or any(i is sword for i in g.ground_items)
    assert ruby not in g.player.inventory and brooch in g.player.inventory
    assert g.player_gold == coin_before - plan['coin'] + plan['change']
    assert m.purse == 5000 - plan['change']


def test_the_shop_says_what_a_ware_will_cost_in_treasure():
    g = _game()
    g.dungeon_level = 40
    sword = items.pick_random_weapon_for_floor(40, random.Random(3))
    _trader(g, level=40, stock=[sword])
    g.player.inventory.append(treasure.make('treasure_gold_idol'))
    g.player_gold = 10
    menu = g._trader_menu()
    texts = [str(d[0]) for d in menu['entries'][0]['details'] if isinstance(d, tuple)]
    # The idol alone covers it: the coin stays in the purse, change comes back.
    assert any(t.startswith('Pays with a Gold Idol;') and 'gold back' in t for t in texts), texts


def test_encounter_gold_costs_accept_treasure_with_change_in_coin():
    from npc_encounters import can_pay_cost
    g = _game()
    g.player_gold = 100
    g.player.inventory.append(treasure.make('treasure_celtic_torc'))   # credit 1,620
    treasure.appraise(g.player, g.player.inventory[-1])
    ok, _ = can_pay_cost(g.player, {'type': 'gold', 'amount': 1200}, g._purse_wealth(), 10)
    assert ok
    g._npc_pay_gold(1200)
    assert not any(i.id == 'treasure_celtic_torc' for i in g.player.inventory)
    assert g.player_gold == 100 + 1620 - 1200
    # An unvalued kind counts only at the low end of its band toward what he can afford.
    g2 = _game()
    g2.player_gold = 0
    g2.player.inventory.append(treasure.make('treasure_celtic_torc'))
    assert g2._purse_wealth() == int(1000 * treasure.buy_rate())


# ===================================================================== stock lean and spread

def test_trader_stock_leans_toward_kinds_the_hero_has_not_held():
    with open(os.path.join(ROOT, 'data', 'traders.json'), encoding='utf-8') as f:
        bias = json.load(f)['stock_bias']
    assert 0 < bias['seen_weight'] < 1
    import collections
    defn = {**traders.kind_def('generalist'), 'kind': 'generalist'}
    base = collections.Counter(w.id for s in range(300)
                               for w in traders.build_stock(defn, 25, random.Random(s))
                               if w.item_class == 'scroll')
    held = {i for i, _n in base.most_common(3)}       # three kinds the hero has held
    leaned = collections.Counter(w.id for s in range(300)
                                 for w in traders.build_stock(defn, 25, random.Random(s), seen=held)
                                 if w.item_class == 'scroll')
    before = sum(base[i] for i in held)
    after = sum(leaned[i] for i in held)
    assert after < before * 0.5                       # what he has held shows up far less
    assert sum(leaned.values()) >= sum(base.values()) * 0.9    # and the stall is as full


def test_every_trader_offers_a_real_choice_across_kinds():
    plan = traders.data()['traders']
    for kind, t in plan.items():
        assert t.get('spread'), kind
        defn = {**t, 'kind': kind}
        lo = {'abyssal': 61, 'bookseller': 15, 'armourer': 10}.get(kind, 5)
        for s in range(12):
            stock = traders.build_stock(defn, lo + s, random.Random(100 + s))
            classes = {w.item_class for w in stock}
            for group in t['spread']:
                assert classes & set(group), (kind, group, sorted(classes))
    g = plan['generalist']['spread']
    assert ['accessory'] in g and any('weapon' in grp for grp in g) and any('spellbook' in grp for grp in g)


def test_the_lean_never_names_an_unknown_ware():
    g = _game()
    g.player.seen_item_ids.update(i.id for i in items.load_items('potion')[:10])
    m = _trader(g, level=12)
    for it in m.stock:
        if getattr(it, 'item_class', '') in ('potion', 'scroll', 'wand', 'accessory') \
                and not g._item_is_known(it):
            assert g._display_name(it) != it.name or it.name == it.unidentified_name


# ===================================================================== the draught (D8)

def test_the_draught_is_a_rare_deep_ware_and_data_driven():
    rare = traders.data()['rare_stock']
    entry = next(e for e in rare if e['id'] == 'draught_of_mimir')
    assert entry['min_floor'] >= 40 and 0.02 <= entry['chance'] <= 0.05 and entry['share'] >= 3
    defn = {**traders.kind_def('generalist'), 'kind': 'generalist'}
    shallow = sum(any(w.id == 'draught_of_mimir' for w in traders.build_stock(defn, 30, random.Random(s)))
                  for s in range(300))
    deep = sum(any(w.id == 'draught_of_mimir' for w in traders.build_stock(defn, 60, random.Random(s)))
               for s in range(600))
    assert shallow == 0 and 5 <= deep <= 45                 # about 1 in 30
    d = items.make_item_by_id('potion', 'draught_of_mimir')
    d._trade_share = entry['share']
    assert economy.merchant_price(d, 60) >= 3 * economy.floor_income(60)
    assert d.id_level == 5 and d.min_level >= 9999          # never random loot


def _drink_draught(g, success):
    from game_states import STATE_PLAYER, STATE_QUAFF_MENU
    d = items.make_item_by_id('potion', 'draught_of_mimir')
    g.player.inventory.append(d)
    g._open_quaff_menu()
    assert g.state == STATE_QUAFF_MENU
    g._quaff_sel = g.quaff_menu_items.index(d)
    seen = {}

    def fake_start(**kw):
        seen.update(kw)
        kw['callback'](types.SimpleNamespace(success=success, score=1 if success else 0,
                                             correct=1 if success else 0, asked=1))
    g.quiz_engine.start_quiz = fake_start
    _press(g, pygame.K_RETURN)
    assert g.state == STATE_PLAYER
    return d, seen


def test_the_draught_asks_a_question_and_a_right_answer_gives_wisdom_for_good():
    g = _game()
    wis = g.player.WIS
    d, seen = _drink_draught(g, True)
    assert seen['subject'] in ('philosophy', 'theology') and seen['tier'] == 4
    assert seen['threshold'] == 1 and seen['mode'] == 'threshold'
    assert g.player.WIS == wis + 1 and d not in g.player.inventory


def test_a_wrong_answer_wastes_the_draught():
    g = _game()
    wis = g.player.WIS
    d, _seen = _drink_draught(g, False)
    assert g.player.WIS == wis and d not in g.player.inventory
    assert any('wasted' in t for t in _texts(g))


# ===================================================================== encyclopedia

def test_the_encyclopedia_has_treasure_pages_and_every_category_fits():
    from main import Game
    assert ('k', 'treasure', 'Treasure') in Game._ENCYCLOPEDIA_CATS
    g = _game()
    g.player.seen_item_ids.add('treasure_burmese_ruby')
    g._encyclopedia_load_entries('treasure')
    assert [e['_id'] for e in g.encyclopedia_entries] == ['treasure_burmese_ruby']
    assert g._encyclopedia_treasure_value(g.encyclopedia_entries[0]) == 'Worth thousands of gold'
    g.player.appraised_treasure.add('treasure_burmese_ruby')
    assert g._encyclopedia_treasure_value(g.encyclopedia_entries[0]) == 'Valued at 2,500 gold'
    src = open(os.path.join(ROOT, 'src', 'game_render.py'), encoding='utf-8').read()
    assert 'cat_body.h // max(1, len(cats))' in src          # the rows close up to fit eleven
    assert 'a-j' not in src


# ===================================================================== bones, QA

def test_bones_keep_a_little_treasure_never_cursed(tmp_path, monkeypatch):
    import bones
    monkeypatch.setattr(bones, '_bones_dir', lambda: str(tmp_path))
    g = _game()
    g.player.inventory += [treasure.make('treasure_bohemian_garnets'),
                           treasure.make('treasure_golconda_diamond')]
    bones.save_bones('Ghosty', 20, 'died', g.player, 0)
    data = json.loads((tmp_path / 'bones_L20.json').read_text(encoding='utf-8'))
    ids = [e['id'] for e in data['gear'] if e['item_class'] == 'treasure']
    assert ids == ['treasure_bohemian_garnets']            # the diamond is worth more than a floor
    room = types.SimpleNamespace(inner_tiles=lambda: [(x, y) for x in range(2, 9) for y in range(2, 9)])
    dungeon = types.SimpleNamespace(is_walkable=lambda x, y: True)
    ground = []
    bones._place_cursed_gear(data['gear'], 0, room, dungeon, ground)
    t = [i for i in ground if treasure.is_treasure(i)]
    assert t and t[0].buc == 'uncursed'


def test_the_qa_sampler_lays_out_gold_treasure_and_a_trader():
    from mystery_system import MerchantNPC
    g = _game()
    g.player.qa_tools = True
    g._qa_treasure_sampler()
    assert any(isinstance(i, items.GoldPile) and i.amount == 20000 for i in g.ground_items)
    laid = {i.id for i in g.ground_items if treasure.is_treasure(i)}
    assert len(laid) >= 10
    m = next(i for i in g.ground_items if isinstance(i, MerchantNPC))
    assert any(w.id == 'draught_of_mimir' for w in m.stock)
