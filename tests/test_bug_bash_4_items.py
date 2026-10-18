"""Bug bash 4 (2026-10-16), fix batch F2: items, identification and weight.

Each test names the finding it pins (items/I-xx, ui/UI-xx, saves/S-02,
world/E1 and E3 in _bugbash_2026_10_16). Behaviour tests on a real headless
Game wherever the bug lives in Game code. What these cannot prove (how the
"It feels wrong..." line reads in play, the Kit at a real window size) is a
play-test question: Claude cannot drive Pygame.
"""
import copy
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import items  # noqa: E402
from items import load_items  # noqa: E402

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(name='__test_bug_bash_4_items__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(3)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.ground_items = [i for i in g.ground_items
                      if (i.x, i.y) != (g.player.x, g.player.y)]
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _texts(g, n=6):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni,
                                      mod=0, scancode=0))


def _known(it):
    it.id_level = 5
    it.buc_known = True
    return it


def _unknown(it):
    it.id_level = 0
    it.buc_known = False
    return it


def _pass_quizzes(g):
    """Every quiz this Game starts passes at once (chain 5)."""
    g.quiz_engine.start_quiz = lambda **kw: kw['callback'](
        types.SimpleNamespace(success=True, score=5))


def _acc(aid):
    return copy.copy(next(a for a in load_items('accessory') if a.id == aid))


def _weapon(material='iron', wid='longsword'):
    w = items.instantiate_weapon(wid, material)
    w.cursed = False
    w.buc = 'uncursed'
    return w


# ---------------------------------------------------------------- I-01
def test_i01_a_new_belt_over_a_cursed_belt_is_refused_and_kept():
    """It passed the quiz, said "You slip on the Girdle", equipped nothing,
    and the new belt was gone."""
    g = _game()
    p = g.player
    _pass_quizzes(g)
    old = _known(_acc('ariadnes_thread'))
    old.buc = 'cursed'
    p._apply_equip(old)
    new = _known(_acc('amulet_of_hippolyta'))
    new.buc = 'uncursed'
    p.inventory.append(new)
    acts = {a['id']: a for a in g._item_actions(new)}
    assert acts['equip']['enabled'] is False          # the Kit sees it too
    g._equip_item(new)
    assert p.belt_slot is old
    assert any(i is new for i in p.inventory)
    assert any('welded' in t for t in _texts(g, 2))


def test_i01_a_refused_accessory_swap_after_the_quiz_never_destroys_the_item():
    """The quiz path itself: if _apply_equip refuses, the item stays."""
    g = _game()
    p = g.player
    _pass_quizzes(g)
    new = _known(_acc('amulet_of_hippolyta'))
    p.inventory.append(new)
    p._apply_equip = lambda item: None                # every swap refused
    g._equip_accessory(new)
    assert any(i is new for i in p.inventory)
    assert 'cannot put on' in _texts(g, 1)[0]


# ---------------------------------------------------------------- I-02
def test_i02_paralysed_hero_cannot_take_the_stairs_or_open_the_sheet():
    from game_states import STATE_PLAYER
    g = _game()
    calls = []
    g._descend_stairs = lambda: calls.append('>')
    g._ascend_stairs = lambda: calls.append('<')
    for effect in ('paralyzed', 'sleeping'):
        g.player.status_effects.clear()
        g.player.add_effect(effect, 20)
        for uni, key in (('>', pygame.K_PERIOD), ('<', pygame.K_COMMA), ('@', pygame.K_2)):
            g.state = STATE_PLAYER
            _press(g, key, uni)
            assert g.state == STATE_PLAYER, (effect, uni)
    assert calls == []
    g.player.status_effects.clear()
    _press(g, pygame.K_PERIOD, '>')
    assert calls == ['>']                             # awake: the stairs work


# ---------------------------------------------------------------- I-03
def test_i03_two_rings_of_one_kind_do_not_share_one_effects_dict():
    tpl = next(a for a in load_items('accessory') if a.id == 'ring_of_master_constitution')
    a, b = copy.copy(tpl), copy.copy(tpl)
    assert a.effects == b.effects == tpl.effects
    assert a.effects is not b.effects and a.effects is not tpl.effects
    a.effects['amount'] = 0
    assert b.effects['amount'] == tpl.effects['amount'] != 0


def test_i03_cursed_enchant_ring_scrolls_leave_no_permanent_stat():
    g = _game()
    p = g.player
    tpl = next(a for a in load_items('accessory') if a.id == 'ring_of_master_constitution')
    a, b = _known(copy.copy(tpl)), _known(copy.copy(tpl))
    con0 = p.CON
    p._apply_equip(a)
    p._apply_equip(b)
    sc = copy.copy(next(s for s in load_items('scroll') if s.effect == 'enchant_accessory'))
    for _ in range(3):
        sc.buc = 'cursed'
        g._apply_scroll_effect(sc)
    g._unequip_slot('accessory_0', a)
    g._unequip_slot('accessory_1', b)
    assert p.CON == con0


# ---------------------------------------------------------------- I-04
def test_i04_esc_on_the_scroll_of_identify_picker_wastes_it():
    from game_states import STATE_PLAYER, STATE_IDENTIFY_MENU
    g = _game()
    p = g.player
    wand = _unknown(copy.copy(load_items('wand')[2]))
    p.inventory.append(wand)
    g._open_scroll_identify_picker()
    assert g.state == STATE_IDENTIFY_MENU and g._scroll_identify_pending
    _press(g, pygame.K_ESCAPE)
    assert g.state == STATE_PLAYER
    assert not g._scroll_identify_pending
    assert 'fades' in _texts(g, 1)[0]


# ---------------------------------------------------------------- I-05 (leak part)
def test_i05_a_scripted_identified_flag_does_not_open_the_dossier():
    """``item.identified = True`` writes id_level 4 without identifying; the
    dossier then showed the aura, the effect and the lore of an item still
    named by its appearance."""
    g = _game()
    p = g.player
    pot = copy.copy(next(x for x in load_items('potion') if x.effect == 'confusion'))
    p.known_item_ids.discard(pot.id)
    pot.identified = True
    assert pot.id_level == 4 and not p.knows_item_type(pot)
    p.inventory.append(pot)
    assert g._display_name(pot) == g._fix_name_case(pot.unidentified_name)
    assert g._kit_visible_level(pot) == 0
    ident = [str(line[0]) for line in g._lore_item_identity_lines(pot, pot.id_level)]
    assert 'Aura: Unknown' in ident
    mech = [str(line[0]) for line in g._lore_item_mechanic_lines(pot, g._kit_visible_level(pot))]
    assert mech[0] == 'Mechanics unrevealed'
    assert not any('Confusion' in m for m in mech)
    # The menus agree: no effect line for it in the quaff list.
    assert g._item_is_known(pot) is False
    # Once its type IS known, everything shows (unchanged).
    p.known_item_ids.add(pot.id)
    assert g._kit_visible_level(pot) == 4 and g._item_is_known(pot)


# ---------------------------------------------------------------- I-06
def test_i06_npc_rewards_go_through_the_pack_rules():
    """Appended directly: no weight limit, no stacking, no ring look."""
    g = _game()
    p = g.player
    heal = next(x for x in load_items('potion') if x.id == 'potion_of_healing')
    p.known_item_ids.add(heal.id)
    p.inventory = [i for i in p.inventory if i.id != heal.id]
    held = _known(copy.copy(heal))
    held.buc = 'uncursed'
    p.inventory.append(held)
    gift = _known(copy.copy(held))
    g._create_specific_npc_item = lambda *a, **k: gift
    g._apply_npc_reward({'type': 'specific_item', 'item_type': 'potion',
                         'item_id': 'potion_of_healing'})
    assert held.count == 2                                         # stacked
    assert gift not in p.inventory
    # Too heavy: it lands at the hero's feet, never past the limit.
    boulder = _known(_weapon())
    boulder.weight = 10 * p.get_carry_limit()
    g._create_specific_npc_item = lambda *a, **k: boulder
    g._apply_npc_reward({'type': 'specific_item', 'item_type': 'weapon', 'item_id': 'x'})
    assert boulder not in p.inventory and boulder in g.ground_items


# ---------------------------------------------------------------- I-07 / I-15
def test_i07_wearing_a_cursed_item_makes_the_curse_known():
    g = _game()
    p = g.player
    w = _unknown(_weapon())
    w.buc = 'cursed'
    p.inventory.append(w)
    g._equip_item(w)
    assert p.weapon is w and w.buc_known
    assert g._display_name(w).startswith('Cursed ')
    acts = {a['id']: a for a in g._item_actions(w)}
    assert not acts['equip']['enabled'] and not acts['drop']['enabled']


def test_i07_a_refused_removal_marks_the_curse_known():
    g = _game()
    p = g.player
    w = _unknown(_weapon())
    w.buc = 'cursed'
    p._apply_equip(w)
    assert not w.buc_known
    ok, _msg = p.try_unequip_slot(w)
    assert not ok and w.buc_known


def test_i15_cursed_prefix_goes_before_the_appearance_without_its_article():
    g = _game()
    p = g.player
    arm = items.instantiate_armor('chain_shirt', 'chain_steel')
    arm.unidentified_name = 'a rough amber pelt'
    _unknown(arm)
    p.known_item_ids.discard(arm.id)
    arm.buc = 'cursed'
    arm.buc_known = True
    if p.knows_item_type(arm):
        pytest.skip('type known by the starting kit')
    assert g._display_name(arm) == 'Cursed Rough Amber Pelt'
    _pass_quizzes(g)
    p.inventory.append(arm)
    g._equip_item(arm)
    assert not any('(cursed)' in t for t in _texts(g, 3))
    assert not any('Cursed A ' in t for t in _texts(g, 3))


# ---------------------------------------------------------------- I-08 / E3
def test_i08_e3_messages_name_an_unidentified_item_by_its_appearance():
    g = _game()
    p = g.player
    w = _unknown(_weapon())
    w.buc = 'cursed'
    p._apply_equip(w)
    shown = g._bare_name(w)
    assert w.name not in shown
    ok, msg = p.try_unequip_slot(w)
    assert w.name not in msg and shown in msg          # E3: "welded" line
    # The enchant scroll neither names it nor tells its number.
    w.buc = 'uncursed'
    sc = copy.copy(next(s for s in load_items('scroll') if s.effect == 'enchant_weapon'))
    sc.buc = 'uncursed'
    g._apply_scroll_effect(sc)
    line = _texts(g, 1)[0]
    assert w.name not in line and 'enchant +' not in line
    # Ranged weapon lines.
    bow = _unknown(copy.copy(next(x for x in load_items('weapon')
                                  if getattr(x, 'requires_ammo', None))))
    p.ranged_weapon = bow
    p.known_item_ids.discard(bow.id)
    bow.infinite_ammo = False
    p.inventory = [i for i in p.inventory if getattr(i, 'ammo_type', None) is None]
    g._open_targeting()
    line = _texts(g, 1)[0]
    assert 'Cannot fire' in line and bow.name not in line
    assert g._bare_name(bow) in line


def test_i08_shop_purchase_names_the_item_as_the_shop_showed_it():
    from mystery_system import spawn_merchant
    from game_states import STATE_SHOP
    g = _game()
    m = None
    for s in range(30):
        m = spawn_merchant(10, g.dungeon.rooms, g.dungeon, [], random.Random(s))
        if m and any(i.name not in g._display_name(i) for i in m.stock):
            break
    idx = next(i for i, it in enumerate(m.stock) if it.name not in g._display_name(it))
    item = m.stock[idx]
    shown = g._display_name(item)
    g.player_gold = 10 ** 6
    g._shop_merchant = m
    g._shop_selection = idx
    g.state = STATE_SHOP
    _press(g, pygame.K_RETURN)
    bought = next(t for t in _texts(g, 3) if t.startswith('You buy'))   # then the trader's line
    assert shown in bought and item.name not in bought


# ---------------------------------------------------------------- I-09
def test_i09_floor_comparison_hides_enchants_and_unknown_worn_items():
    g = _game()
    p = g.player
    worn = _weapon()
    worn.id_level = 0
    worn.enchant_bonus = -2
    p._apply_equip(worn)
    floor = _known(_weapon())
    floor.enchant_bonus = 0
    p.known_item_ids.add(floor.id)
    n = len(g.msg_log.entries)
    g._show_item_comparison(floor)
    new = [str(e[0]) for e in g.msg_log.entries[n:]]
    # Same base sword, worn copy's -2 unknown: nothing to tell.
    assert new == []
    # A worn item whose TYPE is unknown is never compared or named.
    axe = _weapon('steel', 'battleaxe')
    axe.id_level = 0
    p.known_item_ids.discard(axe.id)
    if p.knows_item_type(axe):
        pytest.skip('battleaxe type known')
    p.weapon = axe
    g._show_item_comparison(floor)
    assert [str(e[0]) for e in g.msg_log.entries[n:]] == []


# ---------------------------------------------------------------- I-10
def test_i10_the_character_sheet_lists_every_pack_item():
    g = _game()
    p = g.player
    for _ in range(40 - len(p.inventory)):
        p.inventory.append(_known(copy.copy(load_items('scroll')[0])))
    rows = g._charsheet_pack_entries(filtered=False)
    assert len(rows) == len(p.inventory) == 40
    assert rows[26]['letter'] == 'A'


# ---------------------------------------------------------------- I-11 / I-12
def test_i11_intercession_never_gives_a_unique_twice():
    from items import claim_unique, unique_available
    g = _game()
    got = []
    for s in range(12):
        random.seed(s)
        g.ground_items = []
        g._spawn_intercession_artifact(g.player.x, g.player.y)
        got += [i.id for i in g.ground_items]
    assert len(got) == len(set(got))
    for it in load_items('artifact'):
        if it.id in got:
            assert not unique_available(it)          # claimed
    pal = next(a for a in load_items('artifact') if a.id == 'palladium')
    items.bind_unique_registry(set())
    claim_unique(pal)
    g.ground_items = []
    for s in range(10):
        random.seed(s)
        g._spawn_intercession_artifact(g.player.x, g.player.y)
    assert 'palladium' not in [i.id for i in g.ground_items]


def test_i12_mini_boss_unique_drop_is_once_a_run():
    from items import unique_available
    g = _game()
    spear = next(w for w in load_items('weapon') if w.id == 'meleager_spear')
    g.ground_items = []
    g._spawn_unique_item(g.player.x, g.player.y, 'meleager_spear')
    assert [i.id for i in g.ground_items] == ['meleager_spear']
    assert not unique_available(spear)
    g._spawn_unique_item(g.player.x, g.player.y, 'meleager_spear')
    assert [i.id for i in g.ground_items] == ['meleager_spear']


# ---------------------------------------------------------------- I-14
def test_i14_a_blessed_potions_saved_dose_survives_being_over_the_limit():
    from game_states import STATE_QUAFF_MENU
    kept = lost = 0
    for s in range(25):
        g = _game()
        p = g.player
        proto = next(i for i in load_items('potion') if getattr(i, 'effect', '') == 'cure_poison')
        pot = _known(copy.copy(proto))
        pot.buc = 'blessed'
        pot.count = 1
        junk = _known(items.instantiate_armor('full_plate', 'chain_steel'))
        p.inventory += [pot, junk]
        junk.weight = p.get_carry_limit() - p.get_current_weight() + junk.weight + 5
        random.seed(s)
        g.quaff_menu_items = [pot]
        g.state = STATE_QUAFF_MENU
        g._quaff_menu_input(pygame.K_a)
        if any('remains' in t for t in _texts(g, 4)):
            if pot in p.inventory:
                kept += 1
            else:
                lost += 1
    assert lost == 0 and kept > 0


# ---------------------------------------------------------------- I-16
def test_i16_u_on_a_pack_item_does_nothing():
    g = _game()
    p = g.player
    sw = next(i for i in p.inventory if items.Weapon is not None and isinstance(i, items.Weapon))
    _known(sw)
    sw.buc = 'uncursed'
    was = p.weapon
    t0 = g.turn_count
    ctx = {}
    assert g._item_action_run('unequip', sw, ctx) is False
    assert p.weapon is was and g.turn_count == t0


# ---------------------------------------------------------------- I-17
def test_i17_pack_order_follows_the_shown_names():
    g = _game()
    p = g.player
    p.inventory = []
    pots = [_unknown(copy.copy(x)) for x in load_items('potion')[:6]]
    for x in pots:
        p.known_item_ids.discard(x.id)
        p.add_to_inventory(x)
    shown = [g._display_name(i).lower() for i in p.inventory]
    assert shown == sorted(shown)


# ---------------------------------------------------------------- I-18 / CQ-12
@pytest.mark.parametrize('wt, lim, state', [
    (75.4, 100, 'Burdened'), (74.6, 100, ''), (75.0, 100, ''),
    (100.3, 100, 'Over Limit'), (99.6, 100, 'Burdened'), (43.2, 100, ''),
    (3.4000000000000004, 100, ''),
])
def test_i18_the_weight_readout_never_contradicts_the_state(wt, lim, state):
    from hud_context import load_number
    shown = float(load_number(wt, lim, 0.75))
    assert (shown > lim * 0.75) == (state != '')
    assert (shown > lim) == (state == 'Over Limit')
    assert abs(shown - wt) <= 0.5


def test_i18_every_readout_uses_the_shared_number():
    from ui import carry_numbers
    from player import Player
    p = Player()
    it = _known(_weapon())
    it.weight = 75.4
    p.inventory.append(it)
    assert p.is_burdened()
    assert carry_numbers(p) == '75.4 / 100'
    assert p.carry_line() == 'Carrying 75.4 / 100'


# ---------------------------------------------------------------- UI-02 / UI-17
def _equip_menu_entries(g):
    seen = {}
    g._draw_decision_menu = lambda **kw: seen.update(kw)
    g._open_equip_menu()
    g._menu_tab = 0
    g._draw_equip_menu()
    return seen.get('entries', [])


def test_ui02_ui17_equip_menu_hides_unknown_stats_and_capitalises():
    g = _game()
    p = g.player
    p.inventory = []
    w = _unknown(_weapon())
    w.base_damage = 77
    p.known_item_ids.discard(w.id)
    if p.knows_item_type(w):
        pytest.skip('type known')
    p.inventory.append(w)
    entries = _equip_menu_entries(g)
    row = next(e for e in entries if e['icon'] is w)
    assert '77' not in row['detail'] and 'Iron' not in row['detail']
    assert 'Unidentified' in row['detail']
    # Known armour: slot capitalised, no raw lowercase label.
    a = _known(items.instantiate_armor('chain_shirt', 'chain_steel'))
    p.inventory = [a]
    g._menu_tab = 1
    seen = {}
    g._draw_decision_menu = lambda **kw: seen.update(kw)
    g._open_equip_menu()
    for tab in range(len(g._EQUIP_TABS)):
        g._menu_tab = tab
        g._draw_equip_menu()
        for e in seen.get('entries', []):
            if e['icon'] is a:
                assert e['detail'].split()[0][0].isupper()


def test_ui17_in_sight_and_powers_spell_their_units():
    from hud_context import _distance_label, _cooldown_row
    assert _distance_label(0) == 'Here'
    assert _distance_label(1) == '1 Tile' and _distance_label(4) == '4 Tiles'
    assert _cooldown_row('Prayer', 0).status == 'Ready'
    assert _cooldown_row('Prayer', 12).status == '12 Turns'
    assert _cooldown_row('Prayer', 12).state == 'cooldown'


# ---------------------------------------------------------------- UI-03 / UI-04 / UI-05 / CQ-08
def test_ui03_ui04_kit_hides_unknown_material_and_shows_real_weight():
    g = _game()
    p = g.player
    w = _unknown(_weapon())
    p.known_item_ids.discard(w.id)
    if p.knows_item_type(w):
        pytest.skip('type known')
    p.inventory.append(w)
    cells = g._kit_cells_for_item('weapons', 'pack', w)
    assert 'iron' not in [str(c).lower() for c in cells]
    stats, _extra = g._kit_row_labelled('weapons', 'pack', w)
    assert not any('iron' in s.lower() for s in stats)
    food = next(i for i in p.inventory if getattr(i, 'item_class', '') == 'food')
    fcells = g._kit_cells_for_item('consumables', 'pack', food)
    assert fcells[4] == f"{food.weight:.1f}" and fcells[4] != '0'
    lines = [str(line[0]) for line in g._kit_detail_lines_for_item('weapons', 'pack', w)]
    assert 'identification level' not in ' '.join(lines)
    assert any('until you identify it' in t for t in lines)


# ---------------------------------------------------------------- UI-16
def test_ui16_kit_special_shows_real_on_hit_effects_capitalised():
    g = _game()
    w = _known(_weapon())
    w.damage_types = ['pierce', 'slash']
    w.stun_chance = 0.3
    sp = g._kit_weapon_special(w, 5)
    assert 'Pierce / Slash' in sp and 'Stun 30%' in sp
    assert 'pierce+slash' not in sp


# ---------------------------------------------------------------- S-02
def test_s02_journey_restored_names_the_weapon_as_known():
    g = _game()
    p = g.player
    w = _unknown(_weapon())
    p.known_item_ids.discard(w.id)
    p.weapon = w
    g._show_load_summary_popup()
    line = g.popup_data['lines'][0]
    assert w.name not in line or g._display_name(w) == w.name
    assert g._display_name(w) in line
    p.weapon = None
    g._show_load_summary_popup()
    assert 'Unarmed' in g.popup_data['lines'][0]


# ---------------------------------------------------------------- E1
def test_e1_npcs_never_silently_take_a_quest_scroll():
    from npc_encounters import get_inventory_filter, can_pay_cost
    from items import make_scroll_lake_of_fire
    g = _game()
    p = g.player
    p.inventory = []
    fire = make_scroll_lake_of_fire(0, 0)
    p.inventory.append(fire)
    cost = {'type': 'random_item', 'category': 'scroll'}
    # The player picks the scroll (a picker), and the quest scroll is never
    # among the choices; with only it in the pack the cost cannot be paid.
    assert get_inventory_filter(cost) == 'scroll'
    assert g._get_filtered_inventory('scroll') == []
    assert can_pay_cost(p, cost, 0)[0] is False
    cure = _known(copy.copy(next(s for s in load_items('scroll'))))
    p.inventory.append(cure)
    assert g._get_filtered_inventory('scroll') == [cure]
    g._npc_encounter_active = {'tag': 'x', 'options': []}
    g._apply_npc_choice({'cost': cost, 'outcome': ''}, selected_item=None)
    assert fire in p.inventory and cure not in p.inventory


# ---------------------------------------------------------------- MK-04
def test_mk04_nothing_is_dropped_into_solid_rock():
    """Phasing through a wall, a dropped item (Chrysaor, in the monkey run)
    or gold pile was left inside the rock, out of reach."""
    from dungeon import WALL
    from game_states import STATE_DROP_GOLD_INPUT
    g = _game()
    p = g.player
    wx, wy = next((x, y) for y in range(g.dungeon.height) for x in range(g.dungeon.width)
                  if g.dungeon.tiles[y][x] == WALL)
    p.add_effect('phasing', 15)
    p.x, p.y = wx, wy
    sw = _known(_weapon())
    p.inventory.append(sw)
    n = len(g.ground_items)
    g._do_drop_item(sw)
    assert sw in p.inventory and len(g.ground_items) == n
    assert 'solid rock' in _texts(g, 1)[0]
    g.player_gold = 50
    g.drop_gold_input = '20'
    g.state = STATE_DROP_GOLD_INPUT
    _press(g, pygame.K_RETURN)
    assert g.player_gold == 50 and len(g.ground_items) == n


# ---------------------------------------------------------------- MK-11
def test_mk11_geralt_starts_with_one_potion_of_healing_row():
    from main import Game
    from welcome_screen import SECRET_BUILDS
    random.seed(3)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name='__test_bug_bash_4_geralt__',
             secret_build=SECRET_BUILDS['geralt of rivia'])
    rows = [i for i in g.player.inventory if i.id == 'potion_of_healing']
    assert len(rows) == 1 and rows[0].count >= 2
