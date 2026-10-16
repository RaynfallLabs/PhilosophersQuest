"""Equip / drop from the Kit (K) and the character sheet (@).

Behaviour tests on a real Game: both screens act on the selected item with
the same keys (E equip/unequip, D drop, I identify, X lore) through the map
commands' own paths, and bring the player back to the same screen, tab and
item afterwards -- including after the equip quiz, pass or fail.

Play-test still needed for the feel of it (Claude cannot drive Pygame).
"""

import copy
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame
import pytest

pygame.init()

from game_states import (STATE_KIT, STATE_CHARACTER_SHEET, STATE_QUIZ,
                         STATE_DROP_QTY_INPUT, STATE_LORE, STATE_PLAYER)


def _game(name='__test_item_actions__'):
    from main import Game
    g = Game(pygame.display.set_mode((1, 1)), player_name=name)
    # A quiet tile: nothing nearby can act on the turns these actions spend.
    g.monsters = []
    g.ground_items = [i for i in g.ground_items
                      if (i.x, i.y) != (g.player.x, g.player.y)]
    return g


def _item(cat, pred=lambda i: True):
    from items import load_items
    proto = next(i for i in load_items(cat) if pred(i))
    it = copy.copy(proto)
    it.cursed = False
    it.buc = 'uncursed'
    it.buc_known = True
    it.id_level = 5
    it.equip_chain_mode = ''
    if hasattr(it, 'count'):
        it.count = 1
    return it


def _body_armor():
    from chain_equip import is_chain_equip
    return _item('armor', lambda i: getattr(i, 'slot', '') == 'body'
                 and not is_chain_equip(i))


def _ring():
    from chain_equip import is_chain_equip
    return _item('accessory', lambda i: getattr(i, 'slot', '') == 'ring'
                 and not is_chain_equip(i))


def _finish_quiz(g, right=True):
    """Answer every question (right or wrong) until the quiz ends."""
    qe = g.quiz_engine
    for _ in range(40):
        if not qe.active:
            break
        q = qe.current_question
        ans = q['answer'] if right else next(c for c in q['choices'] if c != q['answer'])
        qe.answer(ans)
        qe._advance()
    assert not qe.active


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0,
                                      unicode=uni, scancode=0))


def _kit_select(g, tab_slug, item):
    tabs = [t[1] for t in g._KIT_TABS]
    g._open_kit_panel()
    g._kit_tab = tabs.index(tab_slug)
    rows = g._kit_rows_for_slug(tab_slug)
    g._kit_sel = next(i for i, (_s, it) in enumerate(rows) if it is item)


def _sheet_select_pack(g, item):
    g._open_character_sheet()
    g._charsheet_focus = 'pack'
    g._charsheet_action_source = 'pack'
    g._charsheet_pack_idx = next(i for i, e in enumerate(g._charsheet_pack_entries())
                                 if e['item'] is item)


def _sheet_select_worn(g, item):
    g._open_character_sheet()
    g._charsheet_focus = 'loadout'
    g._charsheet_action_source = 'loadout'
    g._charsheet_loadout_idx = next(i for i, e in enumerate(g._charsheet_loadout_entries())
                                    if e['item'] is item)


def _wear(g, item):
    g.player.inventory.append(item)
    g.player._apply_equip(item)
    g.player.remove_from_inventory(item)
    assert g._item_where(item) == 'equip'


# -- Equip from the Kit -------------------------------------------------------

def test_kit_equip_starts_the_normal_equip_quiz():
    ref = _game('__test_ia_ref__')
    armor_ref = _body_armor()
    ref.player.armor_slots = [None] * len(ref.player.armor_slots)
    ref.player.inventory.append(armor_ref)
    ref._equip_item(armor_ref)
    want = (ref.quiz_engine.subject, ref.quiz_engine.mode, ref.quiz_engine.tier,
            ref.quiz_engine.required, ref.quiz_title)

    g = _game()
    armor = _body_armor()
    g.player.armor_slots = [None] * len(g.player.armor_slots)
    g.player.inventory.append(armor)
    _kit_select(g, 'armor', armor)
    _press(g, pygame.K_e, 'e')
    assert g.state == STATE_QUIZ
    got = (g.quiz_engine.subject, g.quiz_engine.mode, g.quiz_engine.tier,
           g.quiz_engine.required, g.quiz_title)
    assert got == want
    assert g.quiz_engine.subject == 'geography'


def test_kit_equip_pass_wears_it_and_returns_to_the_kit_same_tab():
    g = _game()
    armor = _body_armor()
    g.player.armor_slots = [None] * len(g.player.armor_slots)
    g.player.inventory.append(armor)
    _kit_select(g, 'armor', armor)
    tab = g._kit_tab
    turn = g.turn_count
    _press(g, pygame.K_e, 'e')
    _finish_quiz(g, right=True)
    assert g._item_where(armor) == 'equip'
    assert g.state == STATE_KIT, "the quiz must hand the player back to the Kit"
    assert g._kit_tab == tab
    assert g._kit_selected()[1] is armor, "the same item stays selected"
    assert g.turn_count == turn + 1, "one turn, as on the map"
    said = " ".join(t for t, _k in g._item_feedback_lines())
    assert "You equip the" in said, "the quiz result is shown on the Kit"


def test_kit_equip_fail_returns_to_the_kit_with_the_message():
    g = _game()
    ring = _ring()
    g.player.accessory_slots = [None] * len(g.player.accessory_slots)
    g.player.inventory.append(ring)
    _kit_select(g, 'accessories', ring)
    _press(g, pygame.K_e, 'e')
    assert g.state == STATE_QUIZ and g.quiz_engine.subject == 'history'
    _finish_quiz(g, right=False)
    assert g._item_where(ring) == 'pack'
    assert g.state == STATE_KIT
    assert g._kit_selected()[1] is ring
    assert any("fumble" in t for t, _k in g._item_feedback_lines())


def test_quit_quiz_with_escape_still_returns_to_the_kit():
    g = _game()
    armor = _body_armor()
    g.player.armor_slots = [None] * len(g.player.armor_slots)
    g.player.inventory.append(armor)
    _kit_select(g, 'armor', armor)
    _press(g, pygame.K_e, 'e')
    assert g.state == STATE_QUIZ
    _press(g, pygame.K_ESCAPE)
    assert g.state == STATE_KIT
    assert g._item_where(armor) == 'pack'


# -- Equip / unequip toggle on both screens -----------------------------------

def test_unequip_toggle_from_the_kit():
    g = _game()
    armor = _body_armor()
    g.player.armor_slots = [None] * len(g.player.armor_slots)
    _wear(g, armor)
    _kit_select(g, 'armor', armor)
    acts = {a['id']: a for a in g._kit_actions()}
    assert acts['equip']['label'] == 'Unequip'
    _press(g, pygame.K_e, 'e')
    assert g._item_where(armor) == 'pack'
    assert g.state == STATE_KIT
    assert g._kit_selected()[1] is armor


def test_unequip_toggle_from_the_character_sheet():
    g = _game()
    armor = _body_armor()
    g.player.armor_slots = [None] * len(g.player.armor_slots)
    _wear(g, armor)
    _sheet_select_worn(g, armor)
    _press(g, pygame.K_e, 'e')
    assert g._item_where(armor) == 'pack'
    assert g.state == STATE_CHARACTER_SHEET
    _src, _e, sel = g._charsheet_selection()
    assert sel is armor, "the item stays selected, now in the pack"


def test_equip_from_the_character_sheet_returns_after_the_quiz():
    g = _game()
    armor = _body_armor()
    g.player.armor_slots = [None] * len(g.player.armor_slots)
    g.player.inventory.append(armor)
    _sheet_select_pack(g, armor)
    _press(g, pygame.K_e, 'e')
    assert g.state == STATE_QUIZ
    _finish_quiz(g, right=True)
    assert g.state == STATE_CHARACTER_SHEET
    assert g._item_where(armor) == 'equip'
    _src, _e, sel = g._charsheet_selection()
    assert sel is armor


def test_weapon_equip_toggle_has_no_quiz_and_stays_on_the_sheet():
    g = _game()
    sword = _item('weapon', lambda i: not getattr(i, 'two_handed', False)
                  and getattr(i, 'requires_ammo', None) is None)
    g.player.weapon = None
    g.player.inventory.append(sword)
    _sheet_select_pack(g, sword)
    _press(g, pygame.K_e, 'e')
    assert g.player.weapon is sword
    assert g.state == STATE_CHARACTER_SHEET


# -- Drop on both screens -------------------------------------------------------

def test_drop_pack_item_from_the_kit():
    g = _game()
    sword = _item('weapon')
    g.player.inventory.append(sword)
    _kit_select(g, 'weapons', sword)
    turn = g.turn_count
    _press(g, pygame.K_d, 'd')
    assert sword in g.ground_items and sword not in g.player.inventory
    assert g.turn_count == turn + 1
    assert g.state == STATE_KIT
    src, sel = g._kit_selected()
    assert sel is sword and src == 'floor', "it is still selected, now on the floor"


def test_drop_worn_item_unequips_then_drops_from_the_sheet():
    g = _game()
    armor = _body_armor()
    g.player.armor_slots = [None] * len(g.player.armor_slots)
    _wear(g, armor)
    _sheet_select_worn(g, armor)
    turn = g.turn_count
    _press(g, pygame.K_d, 'd')
    assert armor in g.ground_items
    assert g._item_where(armor) == 'floor'
    assert g.turn_count == turn + 2, "unequip and drop each take their turn"
    assert g.state == STATE_CHARACTER_SHEET
    said = " ".join(t for t, _k in g._item_feedback_lines())
    assert "You remove the" in said and "You drop the" in said


def test_drop_worn_item_from_the_kit():
    g = _game()
    armor = _body_armor()
    g.player.armor_slots = [None] * len(g.player.armor_slots)
    _wear(g, armor)
    _kit_select(g, 'armor', armor)
    _press(g, pygame.K_d, 'd')
    assert armor in g.ground_items
    assert g.state == STATE_KIT


def _stack(n=5):
    from items import load_items
    it = copy.copy(next(iter(load_items('potion'))))
    it.count = n
    it.id_level = 5
    it.buc_known = True
    return it


def test_drop_stack_asks_how_many_then_returns_to_the_kit():
    g = _game()
    pot = _stack(5)
    g.player.inventory.append(pot)
    _kit_select(g, 'consumables', pot)
    _press(g, pygame.K_d, 'd')
    assert g.state == STATE_DROP_QTY_INPUT
    _press(g, pygame.K_2, '2')
    _press(g, pygame.K_RETURN)
    assert pot.count == 3
    assert g.state == STATE_KIT
    assert g._kit_selected()[1] is pot


def test_drop_stack_from_the_sheet_and_cancel_the_prompt():
    g = _game()
    pot = _stack(4)
    g.player.inventory.append(pot)
    _sheet_select_pack(g, pot)
    _press(g, pygame.K_d, 'd')
    assert g.state == STATE_DROP_QTY_INPUT
    _press(g, pygame.K_ESCAPE)
    assert pot.count == 4
    assert g.state == STATE_CHARACTER_SHEET


# -- Curses ------------------------------------------------------------------------

@pytest.mark.parametrize('known', [True, False])
def test_cursed_worn_item_cannot_be_unequipped_or_dropped(known):
    for screen in ('kit', 'sheet'):
        g = _game()
        armor = _body_armor()
        armor.cursed = True
        armor.buc = 'cursed'
        armor.buc_known = known
        g.player.armor_slots = [None] * len(g.player.armor_slots)
        _wear(g, armor)
        turn = g.turn_count
        for key, uni in ((pygame.K_e, 'e'), (pygame.K_d, 'd')):
            if screen == 'kit':
                _kit_select(g, 'armor', armor)
            else:
                _sheet_select_worn(g, armor)
            _press(g, key, uni)
            assert g._item_where(armor) == 'equip', f"{screen} {uni}: it came off"
            assert armor not in g.ground_items
            assert g.state in (STATE_KIT, STATE_CHARACTER_SHEET)
            said = " ".join(t for t, _k in g._item_feedback_lines()).lower()
            assert "welded" in said or "cursed" in said, said
        assert g.turn_count == turn, "a refused removal costs no turn"
        if known:
            acts = {a['id']: a for a in g._item_actions(armor)}
            assert not acts['equip']['enabled'] and not acts['drop']['enabled']
            assert 'Cursed' in acts['equip']['why']


# -- Floor items on the Kit -----------------------------------------------------------

def test_kit_floor_weapon_is_picked_up_and_equipped():
    g = _game()
    sword = _item('weapon', lambda i: not getattr(i, 'two_handed', False)
                  and getattr(i, 'requires_ammo', None) is None)
    sword.x, sword.y = g.player.x, g.player.y
    g.ground_items.append(sword)
    g.player.weapon = None
    _kit_select(g, 'weapons', sword)
    acts = {a['id']: a for a in g._kit_actions()}
    assert acts['equip']['enabled'] and 'drop' not in acts
    turn = g.turn_count
    _press(g, pygame.K_e, 'e')
    assert g.player.weapon is sword
    assert sword not in g.ground_items
    assert g.turn_count == turn + 2, "pick up and equip each take their turn"
    assert g.state == STATE_KIT
    assert g._kit_selected() == ('equip', sword)


def test_kit_floor_armor_goes_through_pickup_then_the_quiz():
    g = _game()
    armor = _body_armor()
    armor.x, armor.y = g.player.x, g.player.y
    g.ground_items.append(armor)
    g.player.armor_slots = [None] * len(g.player.armor_slots)
    _kit_select(g, 'armor', armor)
    _press(g, pygame.K_e, 'e')
    assert armor in g.player.inventory
    assert g.state == STATE_QUIZ
    _finish_quiz(g, right=True)
    assert g._item_where(armor) == 'equip'
    assert g.state == STATE_KIT


def test_kit_floor_item_too_heavy_says_why_and_does_nothing():
    g = _game()
    armor = _body_armor()
    armor.weight = 10_000
    armor.x, armor.y = g.player.x, g.player.y
    g.ground_items.append(armor)
    _kit_select(g, 'armor', armor)
    acts = {a['id']: a for a in g._kit_actions()}
    assert not acts['equip']['enabled'] and acts['equip']['why'] == (
        f"Too heavy for your limit of {g.player.get_carry_limit()}")
    turn = g.turn_count
    _press(g, pygame.K_e, 'e')
    assert armor in g.ground_items
    assert g.turn_count == turn
    assert g.state == STATE_KIT
    assert any("too heavy" in t.lower() for t, _k in g._item_feedback_lines())


# -- Only possible actions are offered --------------------------------------------------

def test_impossible_actions_are_not_offered():
    from items import Potion
    g = _game()
    pot = _stack(1)
    g.player.inventory.append(pot)
    ids = [a['id'] for a in g._item_actions(pot)]
    assert 'equip' not in ids, "a potion cannot be equipped"
    assert ids[:1] == ['drop'] and 'lore' in ids
    assert isinstance(pot, Potion)

    # Identified: no Identify.
    ring = _ring()
    g.player.inventory.append(ring)
    assert 'identify' not in [a['id'] for a in g._item_actions(ring)]
    # Not identified and no Shard: offered greyed, like the I menu refuses.
    ring.id_level = 0
    g.player.inventory = [i for i in g.player.inventory
                          if getattr(i, 'id', '') != 'philosophers_shard']
    act = next(a for a in g._item_actions(ring) if a['id'] == 'identify')
    assert not act['enabled'] and 'Shard' in act['why']

    # All ring slots full: Equip greyed with the reason.
    g.player.accessory_slots = [_ring() for _ in g.player.accessory_slots]
    act = next(a for a in g._item_actions(ring) if a['id'] == 'equip')
    assert not act['enabled'] and act['why'] == "All ring slots are full"

    # A floor item cannot be dropped; a worn one offers Unequip, not Equip.
    sword = _item('weapon')
    sword.x, sword.y = g.player.x, g.player.y
    g.ground_items.append(sword)
    assert 'drop' not in [a['id'] for a in g._item_actions(sword)]
    # The footer lists only enabled actions.
    hints = g._item_action_hints(g._item_actions(ring))
    assert ('E', 'Equip') not in hints and ('I', 'Identify') not in hints


def test_disabled_action_costs_no_turn():
    g = _game()
    ring = _ring()
    g.player.inventory.append(ring)
    g.player.accessory_slots = [_ring() for _ in g.player.accessory_slots]
    _kit_select(g, 'accessories', ring)
    turn = g.turn_count
    _press(g, pygame.K_e, 'e')
    assert g.state == STATE_KIT and g.turn_count == turn
    assert any("ring slots" in t for t, _k in g._item_feedback_lines())


# -- Identify and lore return too ---------------------------------------------------------

def test_lore_from_the_kit_returns_to_the_kit():
    g = _game()
    sword = _item('weapon')
    g.player.inventory.append(sword)
    _kit_select(g, 'weapons', sword)
    _press(g, pygame.K_x, 'x')
    assert g.state == STATE_LORE
    _press(g, pygame.K_ESCAPE)
    assert g.state == STATE_KIT
    assert g._kit_selected()[1] is sword


def test_identify_from_the_sheet_needs_the_shard_and_returns():
    g = _game()
    pot = _stack(1)
    pot.id_level = 0
    g.player.inventory.append(pot)
    assert g._item_can_identify_now(), "a new hero carries the Shard"
    _sheet_select_pack(g, pot)
    _press(g, pygame.K_i, 'i')
    assert g.state == STATE_QUIZ and g.quiz_engine.subject == 'philosophy'
    _finish_quiz(g, right=False)
    assert g.state == STATE_CHARACTER_SHEET


def test_the_return_does_not_survive_leaving_for_another_state():
    g = _game()
    armor = _body_armor()
    g.player.armor_slots = [None] * len(g.player.armor_slots)
    g.player.inventory.append(armor)
    _kit_select(g, 'armor', armor)
    _press(g, pygame.K_e, 'e')
    assert g.state == STATE_QUIZ
    g.state = 'dead'                       # the turn killed the hero
    g._item_screen_resume()
    assert g._item_screen_return is None
    g.state = STATE_PLAYER
    g._item_screen_resume()
    assert g.state == STATE_PLAYER
