"""The lead's five wiring-audit decisions (2026-10-18), on a real headless Game:

4. The Kit (K) has a Valuables tab listing treasure, with weight and worth as
   the shop gives them, honouring appraisal.
5. An altar tribute paid with treasure worth more than the tribute gives
   change in coin, subject to coin weight; the altar card says so.
6. An encounter outcome that takes "a potion" with no picker never takes the
   Draught of Mimir's Well or any other rare potion: it takes the cheapest
   ordinary one.
7. The Draught cannot be thrown. Thieves may still steal it, and give it
   back when they die.
8. The six Soul Spheres and the Draught have Encyclopedia pages (Wonders),
   with lore and art.
"""
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import items  # noqa: E402
import treasure  # noqa: E402

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(name='__test_altar_draught__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(7)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def _texts(g, n=8):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _potion(pid):
    it = items.make_item_by_id('potion', pid)
    assert it is not None, pid
    it.id_level, it.buc_known = 5, True
    return it


# ------------------------------------------------------------------ 4. Valuables

def test_the_kit_has_a_valuables_tab_listing_treasure_with_weight_and_worth():
    from game_states import STATE_KIT
    g = _game()
    p = g.player
    ruby = treasure.make('treasure_burmese_ruby')
    ruby.count = 3
    brooch = treasure.make('treasure_saxon_brooch')
    idol = treasure.make('treasure_gold_idol')
    idol.x, idol.y = p.x, p.y
    p.inventory += [ruby, brooch]
    g.ground_items.append(idol)
    p.appraised_treasure.add(brooch.id)
    _press(g, pygame.K_k, 'k')
    assert g.state == STATE_KIT
    slugs = [s for _l, s in g._KIT_TABS]
    assert 'valuables' in slugs and [l for l, _s in g._KIT_TABS][slugs.index('valuables')] == 'Valuables'
    while g._KIT_TABS[g._kit_tab][1] != 'valuables':
        _press(g, pygame.K_RIGHT)
    rows = g._kit_rows_for_slug('valuables')
    listed = [it for _src, it in rows]
    assert set(map(id, listed)) == {id(ruby), id(brooch), id(idol)}
    assert all(treasure.is_treasure(it) for it in listed)
    # Nothing that is not treasure.
    assert not any(it is p.weapon for it in listed)
    # The shop's weight and worth: exact once valued, else only its band.
    cells = dict(zip([c.label for c in g._kit_column_defs('valuables')],
                     g._kit_cells_for_item('valuables', 'pack', brooch)))
    assert cells['Wt'] == f"{brooch.weight:g}"
    assert cells['Worth'] == f"{treasure.unit_value(brooch):,} gold"
    rcells = dict(zip([c.label for c in g._kit_column_defs('valuables')],
                      g._kit_cells_for_item('valuables', 'pack', ruby)))
    assert rcells['Count'] == '3' and rcells['Wt'] == '0.01'
    assert str(treasure.unit_value(ruby)) not in rcells['Worth'].replace(',', '')
    assert 'unvalued' in rcells['Worth']
    detail = [str(t[0]) for t in g._kit_detail_lines_for_item('valuables', 'pack', ruby)]
    assert treasure.value_text(p, ruby) in detail
    assert any('0.03 for all 3' in d for d in detail)
    # It draws, and the selected piece can be dropped from the Kit.
    g.render()
    g._kit_sel = next(i for i, (_s, it) in enumerate(rows) if it is brooch)
    assert 'drop' in [a['id'] for a in g._kit_actions()]
    assert 'identify' not in [a['id'] for a in g._kit_actions()]
    _press(g, pygame.K_d, 'd')
    assert brooch not in p.inventory and brooch in g.ground_items


# ------------------------------------------------------------------ 5. altar change

def _oracle(g):
    import economy
    from mystery_system import MYSTERIES, MysteryAltar
    p = g.player
    altar = MysteryAltar('oracle', p.x, p.y)
    g.ground_items.append(altar)
    return altar, economy.written_gold(MYSTERIES['oracle']['gold_cost'])


def test_an_altar_paid_in_treasure_gives_change_in_coin():
    from game_states import STATE_MYSTERY_APPROACH
    g = _game()
    p = g.player
    altar, cost = _oracle(g)
    g.player_gold = 20
    ruby = treasure.make('treasure_burmese_ruby')
    p.inventory.append(ruby)
    plan = g._payment_plan(cost)
    assert plan['take'] and plan['change'] > 0
    g._start_mystery(altar)
    assert g.state == STATE_MYSTERY_APPROACH
    g._begin_mystery_challenge()
    assert ruby not in p.inventory
    assert g.player_gold == 20 + plan['change']
    assert any(f"gives back {plan['change']:,} gold in change" in t for t in _texts(g))


def test_change_too_heavy_to_carry_is_left_at_his_feet():
    from items import GoldPile
    g = _game()
    p = g.player
    altar, cost = _oracle(g)
    g.player_gold = 0
    p.inventory.append(treasure.make('treasure_burmese_ruby'))
    plan = g._payment_plan(cost)
    room = 10
    p.coin_room = lambda: room                     # nearly a full pack
    g._start_mystery(altar)
    g._begin_mystery_challenge()
    assert g.player_gold == room
    piles = [i for i in g.ground_items if isinstance(i, GoldPile) and (i.x, i.y) == (p.x, p.y)]
    assert sum(pl.amount for pl in piles) == plan['change'] - room
    assert any('stays on the floor at your feet' in t for t in _texts(g))


def test_the_altar_card_says_change_comes_back_and_names_it_only_when_valued():
    g = _game()
    p = g.player
    _altar, cost = _oracle(g)
    g.player_gold = 20
    ruby = treasure.make('treasure_burmese_ruby')
    p.inventory.append(ruby)
    line = g._tribute_plan_line(cost)
    assert 'gives back the rest in coin' in line and 'no change' not in line
    assert 'left at your feet' in line
    p.appraised_treasure.add(ruby.id)
    change = g._payment_plan(cost)['change']
    assert f"gives back {change:,} gold in change" in g._tribute_plan_line(cost)


# ------------------------------------------------------------------ 6. auto-taken potions

def _only_potions(g, *pots):
    g.player.inventory = [i for i in g.player.inventory
                          if not isinstance(i, items.Potion)] + list(pots)


def test_an_outcome_taking_a_potion_takes_the_cheapest_ordinary_one():
    import economy
    g = _game()
    draught = _potion('draught_of_mimir')
    soma = _potion('soma')
    cheap = _potion('potion_of_healing')
    dear = _potion('potion_of_full_healing')
    assert economy.merchant_price(cheap, 1) < economy.merchant_price(dear, 1)
    _only_potions(g, draught, soma, dear, cheap)
    g._npc_pay_cost({'type': 'potion'}, None)
    left = [i.id for i in g.player.inventory if isinstance(i, items.Potion)]
    assert 'potion_of_healing' not in left
    assert {'draught_of_mimir', 'soma', 'potion_of_full_healing'} <= set(left)
    # "Give back two potions": the two cheapest ordinary ones.
    g._npc_pay_cost({'type': 'potion', 'count': 2}, None)
    left = [i.id for i in g.player.inventory if isinstance(i, items.Potion)]
    assert set(left) == {'draught_of_mimir', 'soma'}


def test_an_outcome_never_takes_the_draught_even_when_it_is_the_only_potion():
    g = _game()
    draught = _potion('draught_of_mimir')
    _only_potions(g, draught)
    g._npc_pay_cost({'type': 'potion'}, None)
    g._npc_pay_cost({'type': 'random_item', 'category': 'potion'}, None)
    assert draught in g.player.inventory
    from npc_encounters import can_pay_cost
    ok, _why = can_pay_cost(g.player, {'type': 'potion', 'count': 2}, 0)
    assert not ok


def test_a_healing_cost_with_no_picker_spares_soma():
    g = _game()
    soma = _potion('soma')
    heal = _potion('potion_of_healing')
    _only_potions(g, soma, heal)
    g._npc_pay_cost({'type': 'healing_potion'}, None)
    assert soma in g.player.inventory and heal not in g.player.inventory


def test_with_a_picker_the_hero_may_still_give_the_draught():
    g = _game()
    draught = _potion('draught_of_mimir')
    _only_potions(g, draught)
    g._npc_pay_cost({'type': 'potion'}, draught)
    assert draught not in g.player.inventory


def test_rare_potions_come_from_the_data():
    import json
    d = json.load(open(os.path.join(ROOT, 'data', 'items', 'potion.json'), encoding='utf-8'))
    rare = {k for k, v in d.items() if v.get('rare')}
    assert {'draught_of_mimir', 'fafnirs_blood', 'soma', 'water_of_lethe',
            'elixir_of_gilgamesh'} <= rare
    for pid in rare:
        assert items.is_rare_potion(_potion(pid))
    assert not items.is_rare_potion(_potion('potion_of_healing'))


# ------------------------------------------------------------------ 7. the Draught can't be thrown

def test_the_draught_is_not_offered_to_throw_and_a_throw_is_refused():
    from game_states import STATE_PLAYER
    g = _game()
    draught = _potion('draught_of_mimir')
    heal = _potion('potion_of_healing')
    _only_potions(g, draught, heal)
    g._open_throw_menu()
    assert draught not in g.throw_menu_items and heal in g.throw_menu_items
    g.state = STATE_PLAYER
    g._open_throw_targeting(draught)
    assert g.state == STATE_PLAYER and not g._throw_targeting
    assert draught in g.player.inventory
    assert any('not throw' in t for t in _texts(g, 3))
    # Only the Draught: nothing to throw.
    _only_potions(g, draught)
    g.player.inventory = [i for i in g.player.inventory
                          if isinstance(i, items.Potion)
                          or getattr(i, 'id', '') == 'philosophers_shard']
    g._open_throw_menu()
    assert g.state == STATE_PLAYER
    assert not items.can_be_thrown(draught) and items.can_be_thrown(heal)


def test_a_thief_may_steal_the_draught_and_gives_it_back_on_death():
    import theft
    from monster import Monster
    import json
    g = _game()
    p = g.player
    draught = _potion('draught_of_mimir')
    p.inventory = [draught]
    assert draught in theft.stealable(p)
    mons = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    kind = next(k for k in ('goblin', 'kobold', 'giant_rat') if k in mons)
    m = Monster({**mons[kind], 'id': kind}, p.x + 1, p.y)
    g.monsters = [m]
    msg = theft.steal(g, m, 'item', random.Random(1))
    assert msg and draught not in p.inventory
    theft.give_back(g, m)
    assert any(getattr(i, 'id', '') == 'draught_of_mimir' for i in g.ground_items)


# ------------------------------------------------------------------ 8. Encyclopedia pages

def test_the_spheres_and_the_draught_have_wonders_pages_with_art_and_lore():
    import lore_art
    from game_states import STATE_ENCYCLOPEDIA
    from pet_system import spheres
    g = _game()
    p = g.player
    sids = list(spheres())
    assert len(sids) == 6
    p.known_item_ids.update(sids)
    p.seen_item_ids.add('draught_of_mimir')
    _press(g, pygame.K_b, 'b')
    _press(g, pygame.K_l, 'l')
    assert g.state == STATE_ENCYCLOPEDIA and g.encyclopedia_category == 'wonders'
    ids = [e['_id'] for e in g.encyclopedia_entries]
    assert set(ids) == set(sids) | {'draught_of_mimir'}
    for e in g.encyclopedia_entries:
        lines = [str(t[0]) for t in g._encyclopedia_article_lines('wonders', e)]
        assert e.get('lore') and e['lore'] in lines
        ref = lore_art.encyclopedia_ref('wonders', e)
        assert ref == ('item', e['_id']) and lore_art.art_path(*ref)
        assert g._encyclopedia_entry_brief('wonders', e)
    draught = next(e for e in g.encyclopedia_entries if e['_id'] == 'draught_of_mimir')
    text = ' '.join(str(t[0]) for t in g._encyclopedia_article_lines('wonders', draught))
    assert '+1 WIS' in text and 'not for throwing' in text
    _press(g, pygame.K_RETURN)
    g.render()


def test_an_unknown_sphere_has_no_page_yet():
    g = _game()
    p = g.player
    p.known_item_ids.discard('greater_soul_sphere')
    p.seen_item_ids.add('greater_soul_sphere')     # held, but not known: no spoiler
    g._encyclopedia_load_entries('wonders')
    assert 'greater_soul_sphere' not in [e['_id'] for e in g.encyclopedia_entries]
