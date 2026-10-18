"""Long item menus reach every item (Brandon, 2026-10-18: "if you have too
many food items, you can only see and select the first 8").

The pet feed and heal pickers are now the Kit / shop's scrolling list with a
detail pane (a scroll bar and "9-16 of 20" when the list is long). The quick
two-column pickers (wand, spell, eat, quaff, throw, powers, pet specials)
turn a whole page instead of shuffling every row across the columns.

These drive a real headless Game through the real keys.
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

_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(name='__test_long_menus__'):
    from main import Game
    from game_states import STATE_PLAYER
    from pet_system import Pet
    random.seed(11)
    items.bind_unique_registry(set())
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.state = STATE_PLAYER
    pet = Pet('electric', g.player.x + 1, g.player.y)
    pet.nickname = 'Sparky'
    pet.hp = 1
    g.pets = [pet]
    return g, pet


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def _twenty_foods(g):
    from items import Food, Ingredient
    defs = list(items.load_items('food')) + list(items.load_items('ingredient'))
    foods = []
    for d in defs:
        if len(foods) == 20:
            break
        import copy
        f = copy.copy(d)
        f.count = 1
        foods.append(f)
    assert len(foods) == 20
    g.player.inventory = [i for i in g.player.inventory
                          if not isinstance(i, (Food, Ingredient))] + foods
    return foods


def _spy_menu(g, monkeypatch):
    seen = {}

    def spy(**kw):
        seen.update(kw)
    monkeypatch.setattr(g, '_draw_decision_menu', spy)
    return seen


def test_twenty_foods_are_all_selectable_with_the_arrows(monkeypatch):
    from game_states import STATE_PET_FEED, STATE_PET_MENU
    for target in range(20):
        g, pet = _game()
        _twenty_foods(g)
        g._open_pet_menu()
        g._pet_open_feed(pet)
        assert g.state == STATE_PET_FEED
        assert len(g.pet_feed_items) == 20
        for _ in range(target):
            _press(g, pygame.K_DOWN)
        assert g._pet_feed_sel == target
        chosen = g.pet_feed_items[target]
        # The list on screen has every food and the cursor on this one.
        seen = _spy_menu(g, monkeypatch)
        g._draw_pet_feed_submenu()
        assert len(seen['entries']) == 20 and seen['selected'] == target
        assert seen['entries'][target]['name'] == g._display_name(chosen)
        monkeypatch.undo()
        _press(g, pygame.K_RETURN)
        assert g.state == STATE_PET_MENU
        assert chosen not in g.player.inventory, target


def test_page_keys_home_end_and_letters_reach_the_far_end():
    g, pet = _game()
    foods = _twenty_foods(g)
    g._open_pet_menu()
    g._pet_open_feed(pet)
    _press(g, pygame.K_END)
    assert g._pet_feed_sel == 19
    _press(g, pygame.K_HOME)
    assert g._pet_feed_sel == 0
    _press(g, pygame.K_PAGEDOWN)
    _press(g, pygame.K_PAGEDOWN)
    _press(g, pygame.K_PAGEDOWN)
    assert g._pet_feed_sel == 15
    _press(g, pygame.K_PAGEUP)
    assert g._pet_feed_sel == 10
    # The 20th food by its letter (t).
    last = g.pet_feed_items[19]
    _press(g, pygame.K_t, 't')
    assert last not in g.player.inventory and foods[19] is last


def test_the_feed_list_draws_its_scroll_bar_and_position(monkeypatch):
    """The real kit draw: the window around the cursor, the "x-y of 20" tag
    and a scroll bar."""
    g, pet = _game()
    _twenty_foods(g)
    g._open_pet_menu()
    g._pet_open_feed(pet)
    for _ in range(15):
        _press(g, pygame.K_DOWN)
    drawn, bars = [], []
    from fantasy_ui import kit_on
    if kit_on():
        real_row = g._menu_row_kit

        def row_spy(rect, entry, **kw):
            drawn.append(entry['name'])
            return real_row(rect, entry, **kw)
        monkeypatch.setattr(g, '_menu_row_kit', row_spy)
    else:
        real_line = g._menu_draw_line

        def line_spy(text, font, color, rect):
            drawn.append(text)
            return real_line(text, font, color, rect)
        monkeypatch.setattr(g, '_menu_draw_line', line_spy)
    monkeypatch.setattr(g, '_ui_scrollbar', lambda *a, **k: bars.append(a))
    g._draw_pet_feed_submenu()
    want = g._display_name(g.pet_feed_items[15])
    names = {g._display_name(f) for f in g.pet_feed_items}
    shown = [d for d in drawn if d in names]
    assert want in shown and len(shown) < 20
    assert bars and bars[0][2] == 20                 # total rows the bar measures


def test_the_heal_picker_scrolls_the_same_way(monkeypatch):
    from game_states import STATE_PET_HEAL
    g, pet = _game()
    heal = next(p for p in items.load_items('potion') if p.effect == 'heal')
    import copy
    pots = []
    for i in range(12):
        p = copy.copy(heal)
        p.buc = ('blessed', 'uncursed', 'cursed')[i % 3]
        p.id_level, p.buc_known, p.count = 5, True, 1
        pots.append(p)
    g.player.inventory += pots
    g._open_pet_menu()
    g._pet_open_heal(pet)
    assert g.state == STATE_PET_HEAL
    n = len(g.pet_heal_items)
    assert n >= 3
    _press(g, pygame.K_END)
    assert g._pet_heal_sel == n - 1
    seen = _spy_menu(g, monkeypatch)
    g._draw_pet_heal_submenu()
    assert len(seen['entries']) == n and seen['selected'] == n - 1


def test_two_column_pickers_turn_a_page_and_show_every_item():
    from game_render import _picker_scroll
    total, visible = 20, 8
    for sel in range(total):
        top = _picker_scroll(sel, total, visible, cols=2)
        assert top <= sel < top + visible                 # always on screen
        assert top % visible == 0                         # whole pages only
    assert _picker_scroll(7, total, visible, 2) == 0
    assert _picker_scroll(8, total, visible, 2) == 8      # Down past the 8th: page 2
    assert _picker_scroll(19, total, visible, 2) == 16
    # One column still scrolls a row at a time.
    assert _picker_scroll(6, 20, 6, 1) == 1
    assert _picker_scroll(3, 5, 8, 2) == 0


def test_the_eat_menu_reaches_its_ninth_food(monkeypatch):
    """A quick two-column picker: the ninth food shows on the second page and
    is eaten when picked."""
    from game_states import STATE_PLAYER
    g, _pet = _game()
    foods = _twenty_foods(g)
    g._open_eat_menu()
    tab_items = g._get_eat_tab_items()
    assert len(tab_items) >= 9
    for _ in range(8):
        _press(g, pygame.K_DOWN)
    ninth = tab_items[8]
    seen = {}
    monkeypatch.setattr(g, '_draw_fast_picker', lambda **kw: seen.update(kw))
    g._draw_eat_menu()
    assert seen['selected'] == 8
    monkeypatch.undo()
    _press(g, pygame.K_RETURN)
    assert ninth not in g.player.inventory and g.state != 'eat_menu'
    assert foods and g.state in (STATE_PLAYER, 'quiz')
