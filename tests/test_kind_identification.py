"""One identification knows every copy (Brandon, 2026-10-18).

    "once you've identified something, all further instances need to be
    fully identified, including BUC status. This is just too annoying right
    now."

Once the hero knows an item's KIND (by the identify question, a scroll, use,
a trader, or any other path) every copy of it is fully identified: its name,
its blessing or curse and its enchantment, in the pack, on the floor, in a
chest, in a trader's stock, and every copy that turns up later. The cursed
Scroll of Identify and the Book of Thoth's curse still make the hero forget
kinds, and forgetting un-knows every copy. Treasure keeps its own appraisal
rules, and an item looks the same whether or not it is known.

These drive a real headless Game.
"""
import copy
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

KIND = 'potion_of_sickness'
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(name='__test_kind_identification__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(11)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.state = STATE_PLAYER
    for s in ('known_item_ids', 'known_class_ids', 'known_forms', 'known_materials'):
        getattr(g.player, s).discard(KIND)
    return g


def _potion(buc='uncursed', pid=KIND):
    it = items.make_item_by_id('potion', pid)
    assert it is not None, pid
    it.id_level = 0
    it.buc = buc
    it.buc_known = False
    return it


def _identify_by_quiz(g, item):
    """Answer the real identify question right."""
    from game_states import STATE_QUIZ
    g._identify_item(item)
    assert g.state == STATE_QUIZ and g.quiz_engine.subject == 'philosophy'
    g.quiz_engine._end(success=True)


def _identify_menu_items(g):
    g._open_identify_menu()
    return [entry[0] for entry in (getattr(g, 'identify_menu_items', None) or [])]


# ------------------------------------------------------------------ the rule

def test_identifying_one_potion_fully_identifies_every_copy_blessing_included():
    from hud_context import hud_item_name
    g = _game()
    p = g.player
    first, second = _potion('uncursed'), _potion('blessed')
    p.inventory += [first, second]
    true_name = g._fix_name_case(first.name)
    assert g._display_name(second) == g._fix_name_case(second.unidentified_name)
    assert g._menu_buc_label(second) == 'Unknown'

    _identify_by_quiz(g, first)

    # The copy already in the pack: full name, its blessing, no "Unknown".
    assert g._display_name(second) == f"Blessed {true_name}"
    assert hud_item_name(p, second) == f"Blessed {true_name}"
    assert g._menu_buc_label(second) == 'Blessed'
    assert g._kit_visible_level(second) == 5
    assert g._lore_direct_id_level(second) == 5
    assert not any('Unknown' in str(x) for x in (g._display_name(second),))
    # Its own stored state is untouched: the kind decides, so forgetting can
    # take it back.
    assert second.id_level == 0 and second.buc_known is False


def test_a_copy_found_later_and_one_in_a_shop_are_known_too():
    from mystery_system import MerchantNPC, build_trader
    g = _game()
    p = g.player
    first = _potion()
    p.inventory.append(first)
    _identify_by_quiz(g, first)
    true_name = g._fix_name_case(first.name)

    # Spawned after the identification, cursed, lying on the floor.
    found = _potion('cursed')
    found.x, found.y = p.x, p.y
    g.ground_items.append(found)
    assert g._display_name(found) == f"Cursed {true_name}"
    assert g._menu_buc_label(found) == 'Cursed'
    # Picked up: still known, and it stays apart from the uncursed copy.
    g.ground_items.remove(found)
    assert p.add_to_inventory(found)
    assert found in p.inventory and g._display_name(found) == f"Cursed {true_name}"

    # In a trader's stock.
    g.ground_items = [i for i in g.ground_items if not isinstance(i, MerchantNPC)]
    m = build_trader('generalist', g.dungeon_level, random.Random(3))
    ware = _potion('uncursed')
    m.stock = [ware]
    m.prices = [economy.merchant_price(ware, g.dungeon_level, m.markup)]
    m.x, m.y = p.x + 1, p.y
    g.ground_items.append(m)
    g._open_shop()
    g._shop_tab = 0
    menu = g._trader_menu()
    assert [e['name'] for e in menu['entries']] == [true_name]
    details = ' '.join(str(d[0]) for d in menu['entries'][0]['details'] if isinstance(d, tuple))
    assert 'Unknown' not in details


def test_a_known_kind_is_never_offered_for_identifying_and_sells_as_identified():
    from game_states import STATE_PLAYER
    g = _game()
    p = g.player
    first, second = _potion(), _potion('blessed')
    p.inventory += [first, second]
    assert second in _identify_menu_items(g)
    g.state = STATE_PLAYER
    _identify_by_quiz(g, first)
    g.state = STATE_PLAYER
    assert not g._needs_identify(second)
    listed = _identify_menu_items(g)
    assert second not in listed and first not in listed
    g.state = STATE_PLAYER
    # The Kit / sheet's I action is gone, and the I key on its lore page says so.
    assert 'identify' not in [a['id'] for a in g._item_actions(second, 'pack')]
    # The Scroll of Identify picker skips it too.
    g._open_scroll_identify_picker()
    assert second not in [e[0] for e in (g.identify_menu_items or [])]
    g._scroll_identify_pending = False
    g.state = STATE_PLAYER
    # A trader pays the identified rate for it.
    from game_traders import TraderMixin  # noqa: F401  (Game mixes it in)
    from mystery_system import build_trader
    m = build_trader('generalist', g.dungeon_level, random.Random(3))
    m.x, m.y = p.x + 1, p.y
    g.ground_items.append(m)
    g._open_shop()
    offer, why = g._trader_offer(second)
    assert why is None
    assert offer == economy.sell_offer(second, g.dungeon_level, known=True, identified=True,
                                       markup=m.markup, purse=m.purse)


def test_same_blessing_copies_join_one_stack_once_the_kind_is_known():
    g = _game()
    p = g.player
    p.inventory = [i for i in p.inventory if getattr(i, 'id', '') != KIND]
    a, b, c = _potion('uncursed'), _potion('uncursed'), _potion('cursed')
    for it in (a, b, c):
        p.add_to_inventory(it)
    assert len([i for i in p.inventory if i.id == KIND]) == 3     # unknown: apart
    _identify_by_quiz(g, a)
    held = [i for i in p.inventory if i.id == KIND]
    assert len(held) == 2
    assert a in held and a.count == 2                    # the identified copy kept
    assert sorted(i.buc for i in held) == ['cursed', 'uncursed']


def test_use_identification_knows_every_copy():
    """Drinking one teaches the kind, as it always did: now that knows every
    copy, blessing included."""
    import pygame as _pg
    g = _game()
    p = g.player
    drink, spare = _potion(), _potion('blessed')
    p.inventory += [drink, spare]
    g._open_quaff_menu()
    g._quaff_sel = g.quaff_menu_items.index(drink)
    g._quaff_menu_input(_pg.K_RETURN)
    assert KIND in p.known_item_ids
    assert g._display_name(spare).startswith('Blessed ')
    assert not g._needs_identify(spare)


def test_save_and_load_keep_kind_knowledge():
    from save_system import delete_save, load_game, save_game
    from main import Game
    name = '__test_kind_id_roundtrip__'
    try:
        g = _game(name)
        p = g.player
        first, second = _potion(), _potion('blessed')
        p.inventory += [first, second]
        _identify_by_quiz(g, first)
        assert save_game(g)
        g2 = Game(_screen(), player_name=name)
        g2.load_state(load_game(name))
        copy2 = next(i for i in g2.player.inventory if i.id == KIND and i.buc == 'blessed')
        assert copy2.id_level == 0                      # nothing was stamped on it
        assert g2._display_name(copy2) == f"Blessed {g2._fix_name_case(copy2.name)}"
        assert not g2._needs_identify(copy2)
        later = _potion('cursed')
        assert g2._display_name(later).startswith('Cursed ')
    finally:
        delete_save(name)


def test_loading_rebuilds_kind_state_from_known_item_ids():
    """A save from before accessory families were recorded: the family of a
    known ring is rebuilt from known_item_ids, so its other copies are known."""
    g = _game()
    p = g.player
    ring = next(r for r in items.load_items('accessory')
                if getattr(r, 'slot', '') == 'ring' and not getattr(r, 'is_unique', False))
    ring = copy.copy(ring)
    ring.id_level = 0
    p.inventory.append(ring)
    p.known_item_ids.add(ring.id)
    p.known_class_ids.clear()
    state = {'ground_items': [], 'level_mgr': None}
    g._rebuild_kind_knowledge(state, rebuild_classes=True)
    assert items.type_class(ring) in p.known_class_ids
    assert items.is_fully_known(ring, p)


# ------------------------------------------------------------------ forgetting

def test_the_cursed_scroll_forgets_the_kind_and_every_copy(monkeypatch):
    g = _game()
    p = g.player
    first, second = _potion(), _potion('blessed')
    p.inventory = [i for i in p.inventory if getattr(i, 'id', '') == 'philosophers_shard']
    p.inventory += [first, second]
    _identify_by_quiz(g, first)
    floor_copy = _potion('cursed')
    floor_copy.x, floor_copy.y = p.x, p.y
    g.ground_items.append(floor_copy)
    assert first.id_level == 5 and not g._needs_identify(second)
    monkeypatch.setattr(random, 'choice', lambda seq: next(i for i in seq if i.id == KIND))
    g._scroll_identify_amnesia()
    assert KIND not in p.known_item_ids
    for it in (first, second, floor_copy):
        assert g._needs_identify(it)
        assert g._display_name(it) in (g._fix_name_case(it.unidentified_name),
                                       g._fix_name_case(it.unidentified_name) + ' x2')
        assert g._menu_buc_label(it) == 'Unknown'
    assert first.id_level == 0                       # the identified copy too
    # The Shard is never the one forgotten.
    shard = next(i for i in p.inventory if getattr(i, 'id', '') == 'philosophers_shard')
    assert not g._forgettable(shard)


def test_the_book_of_thoth_curse_forgets_kinds_too():
    g = _game()
    p = g.player
    p.inventory = [i for i in p.inventory if getattr(i, 'id', '') == 'philosophers_shard']
    first, second = _potion(), _potion('blessed')
    p.inventory += [first, second]
    _identify_by_quiz(g, first)
    g._book_of_thoth_curse()
    assert KIND not in p.known_item_ids
    assert g._needs_identify(second) and g._needs_identify(first)


# ------------------------------------------------------------------ must not break

def test_treasure_keeps_its_own_appraisal_rules():
    import treasure
    g = _game()
    p = g.player
    gem = next(t for t in items.load_items('treasure'))
    gem = copy.copy(gem)
    p.inventory.append(gem)
    assert not g._needs_identify(gem)                # known by sight
    assert not g._forgettable(gem)
    p.known_item_ids.add(gem.id)                     # a kind known says nothing of worth
    assert gem.id not in treasure.appraised(p)


def test_the_art_never_changes_with_identification():
    from renderer import _resolve_item_sprite_path
    g = _game()
    p = g.player
    first, second = _potion(), _potion('blessed')
    p.inventory += [first, second]
    before = _resolve_item_sprite_path(second.id)
    _identify_by_quiz(g, first)
    assert _resolve_item_sprite_path(second.id) == before
    assert before is not None


def test_a_unique_is_known_by_its_own_identify():
    """Identifying one unique identifies that item; it teaches nothing about
    any other unique."""
    uniques = [w for w in items.load_items('weapon') if getattr(w, 'is_unique', False)][:2]
    assert len(uniques) == 2
    g = _game()
    p = g.player
    a, b = (copy.copy(u) for u in uniques)
    for u in (a, b):
        u.id_level = 0
        for s in ('known_item_ids', 'known_class_ids'):
            getattr(p, s).discard(u.id)
    p.inventory += [a, b]
    g._full_identify(a)
    assert not g._needs_identify(a)
    assert g._needs_identify(b)


# ------------------------------------------------------------------ seams (wiring audit)

def test_forgetting_reaches_a_thiefs_loot_and_never_picks_bread():
    import json
    from monster import Monster
    g = _game()
    p = g.player
    first = _potion()
    p.inventory = [i for i in p.inventory if getattr(i, 'id', '') == 'philosophers_shard']
    p.inventory.append(first)
    _identify_by_quiz(g, first)
    stolen = _potion('blessed')
    stolen.id_level = 5                                  # identified, then snatched
    mons = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
    kind = next(k for k in ('goblin', 'kobold', 'giant_rat') if k in mons)
    thief = Monster({**mons[kind], 'id': kind}, p.x + 1, p.y)
    thief.__dict__['stolen_items'] = [stolen]
    g.monsters = [thief]
    g._forget_kind(first)
    assert stolen.id_level == 0 and g._needs_identify(stolen)
    bread = next(iter(items.load_items('food')))
    assert not g._forgettable(bread)


def test_a_merchants_strongbox_teaches_the_kinds_it_names():
    g = _game()
    loot = [_potion('cursed')]
    loot[0].id_level = 5
    loot[0].__dict__['_learn_kind'] = True
    g._learn_loot_kinds(loot)
    assert KIND in g.player.known_item_ids
    assert '_learn_kind' not in loot[0].__dict__
    assert not g._needs_identify(_potion())


def test_the_lore_page_identify_key_needs_the_shard():
    from game_states import STATE_LORE
    g = _game()
    p = g.player
    pot = _potion()
    p.inventory = [i for i in p.inventory if getattr(i, 'id', '') != 'philosophers_shard'] + [pot]
    g._lore_subject = pot
    g.state = STATE_LORE
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_i, unicode='i',
                                      mod=0, scancode=0))
    assert g.state == STATE_LORE
    assert any('Shard' in str(e[0]) for e in g.msg_log.entries[-2:])


def test_the_throw_prompt_names_an_unknown_potion_by_its_look():
    g = _game()
    pot = _potion()
    g.player.inventory.append(pot)
    g._open_throw_targeting(pot)
    said = ' '.join(str(e[0]) for e in g.msg_log.entries[-2:])
    assert g._fix_name_case(pot.name) not in said
    assert g._bare_name(pot) in said
