"""The cook menu (the kitchen rebuild, slice K2; COOKING_REBUILD_PLAN_2026_11_14
section 2.4).

Brandon: "open the cooking screen and be greeted with a clearly sorted menu
that helps me determine what I want to cook quickly, based on my current game
status; see what dishes I am building towards, but can't cook yet; see big
payoff meals that require dungeon scavenging and hunting to cook".

Pins: the five tabs and the keys that move between them; the tab it opens on
and why; the screen's rows are kitchen.menu_rows, in its three sections; a
dish being built toward names what is missing and Enter on it does no harm;
Enter on a ready dish cooks it through the one cooking question; the dish's
picture comes from the recipe's own ``art`` (gold frame for a feast, no
picture rather than a glyph); the words (cook_menu.py) and the list window.
Real keys drive a headless Game. How the menu reads to a kid is a play-test
question: Claude cannot drive Pygame.
"""
import copy
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

import cook_menu  # noqa: E402
import kitchen  # noqa: E402

pygame.init()

# One part of each nature and two rations: every tab has a dish ready and
# dishes being built toward (the same pack as the capture tool's).
EVERY_TAB = [('death_dog_prime', 1), ('giant_lizard_prime', 1), ('cave_bear_prime', 1),
             ('giant_beetle_prime', 1), ('green_slime_prime', 1), ('battle_mage_prime', 1),
             ('crystal_ooze_prime', 1), ('homunculus_prime', 1), ('bone_witch_prime', 1),
             ('goblin_prime', 2), ('cobra_prime', 1), ('fire_beetle_prime', 1),
             ('bread_ration', 2)]


def _game(size=(1280, 720)):
    import items
    from main import Game
    from game_states import STATE_PLAYER
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode(size), player_name='__test_cook_menu__')
    g.monsters = []
    g.state = STATE_PLAYER
    return g


def _pack(g, spec):
    from items import Food, Ingredient, load_items
    from food_system import load_ingredient_for
    p = g.player
    p.inventory = [i for i in p.inventory if not isinstance(i, (Food, Ingredient))]
    foods = {f.id: f for f in load_items('food')}
    for iid, n in spec:
        it = load_ingredient_for(iid) or copy.copy(foods[iid])
        it.count = n
        p.inventory.append(it)


def _press(g, key, uni=''):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=uni, mod=0, scancode=0))


def _held(g, iid):
    return kitchen.held_counts(g.player.inventory).get(iid, 0)


def _select(g, rid):
    ids = [r['id'] for r in g._cook_tab_rows()]
    for _ in range(ids.index(rid)):
        _press(g, pygame.K_DOWN)
    assert g._cook_tab_rows()[g._cook_sel]['id'] == rid


# ---------------------------------------------------------------------------
# Real keys
# ---------------------------------------------------------------------------

def test_hurt_it_opens_on_hp_and_says_why_then_right_reaches_mp():
    from game_states import STATE_COOK_MENU
    g = _game()
    _pack(g, EVERY_TAB)
    g.player.hp = max(1, g.player.max_hp // 4)
    _press(g, pygame.K_c, 'c')
    assert g.state == STATE_COOK_MENU
    assert g._cook_tab_slug() == 'hp'
    assert g._cook_open == ('hp', 'hurt')
    line = cook_menu.reason_line(*g._cook_open, g.player)
    assert line == f"Opened on HP: you are hurt, {g.player.hp} of {g.player.max_hp} HP"
    _press(g, pygame.K_RIGHT)
    assert g._cook_tab_slug() == 'sp'
    _press(g, pygame.K_RIGHT)
    assert g._cook_tab_slug() == 'mp'
    ids = [r['id'] for r in g._cook_tab_rows()]
    assert ids == [r['id'] for r in kitchen.menu_rows(g.player, g.player.inventory, 'mp')]
    g.render()                                   # draws, and says why it opened on HP


def test_every_tab_is_reachable_left_right_and_tab_wrap_round():
    g = _game()
    _pack(g, EVERY_TAB)
    _press(g, pygame.K_c, 'c')
    assert g._cook_open == ('stat', 'lesson')   # full health: the floor's lesson is open
    seen = []
    for _ in range(5):
        seen.append(g._cook_tab_slug())
        _press(g, pygame.K_RIGHT)
    assert sorted(seen) == sorted(kitchen.MENU_TABS)
    assert g._cook_tab_slug() == 'stat'          # five Rights: round to the start
    _press(g, pygame.K_LEFT)
    assert g._cook_tab_slug() == 'mp'
    _press(g, pygame.K_TAB)
    assert g._cook_tab_slug() == 'stat'
    _press(g, pygame.K_DOWN)
    _press(g, pygame.K_RIGHT)
    assert g._cook_sel == 0                       # a new tab starts at its top row


def test_low_mana_opens_on_mp():
    g = _game()
    _pack(g, EVERY_TAB)
    g.player.known_spells = g.player.known_spells or {'magic_missile': 1}
    g.player.mp = 0
    _press(g, pygame.K_c, 'c')
    assert g._cook_open == ('mp', 'mana')
    assert g._cook_tab_slug() == 'mp'


def test_a_building_row_names_what_is_missing_and_enter_does_no_harm():
    from game_states import STATE_COOK_MENU
    g = _game()
    _pack(g, EVERY_TAB)
    _press(g, pygame.K_c, 'c')
    while g._cook_tab_slug() != 'sp':
        _press(g, pygame.K_RIGHT)
    _select(g, 'dish_221')
    row = g._cook_tab_rows()[g._cook_sel]
    assert row['group'] == 'building' and row['progress'] == '2 of 4'
    assert cook_menu.row_line(row, g._cook_counts) == \
        "Needs: Locust Swarmlord Drumstick, Hard Cheese"
    before = kitchen.held_counts(g.player.inventory)
    _press(g, pygame.K_RETURN)
    assert g.state == STATE_COOK_MENU
    assert kitchen.held_counts(g.player.inventory) == before
    assert g._cook_notice == 'dish_221'
    texts = [str(e[0]) for e in g.msg_log.entries[-3:]]
    assert any('you still need Locust Swarmlord Drumstick and Hard Cheese' in t for t in texts)
    g.render()
    _press(g, pygame.K_UP)
    assert g._cook_notice is None


def test_enter_on_a_ready_dish_cooks_it_uses_its_ingredients_and_heals():
    from game_states import STATE_PLAYER
    g = _game()
    _pack(g, EVERY_TAB)
    g.player.hp = max(1, g.player.max_hp // 4)
    asked = {}

    def one_question(**kw):
        asked.update(kw)
        kw['callback'](types.SimpleNamespace(success=True, score=1))
    g.quiz_engine.start_quiz = one_question
    _press(g, pygame.K_c, 'c')
    _select(g, 'cook_cave_bear')
    hp = g.player.hp
    assert _held(g, 'cave_bear_prime') == 1
    _press(g, pygame.K_RETURN)
    assert asked['subject'] == 'cooking' and asked['total_qs'] == 1
    assert g.state == STATE_PLAYER
    assert _held(g, 'cave_bear_prime') == 0
    assert g.player.hp > hp
    texts = [str(e[0]) for e in g.msg_log.entries[-8:]]
    assert any('You prepare Cave Bear Steak.' in t for t in texts), texts


def test_the_screens_rows_are_menu_rows_in_three_sections():
    g = _game()
    _pack(g, EVERY_TAB + [('asterion_minotaur_trophy', 1), ('seal_demon_wrath_prime', 1),
                          ('death_knight_prime', 1), ('wild_mushroom', 1)])
    _press(g, pygame.K_c, 'c')
    groups_seen = set()
    for tab in kitchen.MENU_TABS:
        want = [r['id'] for r in kitchen.menu_rows(g.player, g.player.inventory, tab)]
        rows = g._cook_tab_rows(tab)
        assert [r['id'] for r in rows] == want, tab
        lay = g._cook_list_layout(rows, tab, '', 420, 10_000)
        drawn = [rows[it['index']]['id'] for it in lay['items'] if it['kind'] == 'row']
        assert drawn == want, tab
        heads = [it['group'] for it in lay['items'] if it['kind'] == 'head']
        assert heads == [gr for gr in kitchen.GROUPS if any(r['group'] == gr for r in rows)]
        groups_seen.update(heads)
        # Each header is followed by exactly its own rows.
        cur = None
        for it in lay['items']:
            if it['kind'] == 'head':
                cur = it['group']
            elif it['kind'] == 'row':
                assert rows[it['index']]['group'] == cur
    assert groups_seen == set(kitchen.GROUPS)


def test_every_tab_draws_at_the_smallest_and_largest_windows():
    for size in ((1093, 614), (1280, 720), (3440, 1440)):
        g = _game(size)
        _pack(g, EVERY_TAB + [('asterion_minotaur_trophy', 1)])
        _press(g, pygame.K_c, 'c')
        for _ in kitchen.MENU_TABS:
            for _k in range(3):
                g.render()
                _press(g, pygame.K_DOWN)
            _press(g, pygame.K_END)
            g.render()
            _press(g, pygame.K_RIGHT)


def test_nothing_to_cook_keeps_the_menu_shut():
    from game_states import STATE_PLAYER
    g = _game()
    _pack(g, [('bread_ration', 3)])        # a ration alone is no dish and builds nothing
    _press(g, pygame.K_c, 'c')
    assert g.state == STATE_PLAYER


# ---------------------------------------------------------------------------
# The dish's picture
# ---------------------------------------------------------------------------

def _row_for(g, rid):
    rec = kitchen.recipe(rid)
    return kitchen._row(g.player, rec, kitchen.held_counts(g.player.inventory))


def test_the_detail_pane_shows_the_recipes_own_art_large_gold_for_a_feast():
    import lore_art
    from fantasy_ui import KT
    g = _game()
    rect = pygame.Rect(0, 0, 400, 600)
    feast = _row_for(g, 'feast_01')
    plan = g._cook_detail_plan(rect, feast)
    assert plan['plate'] is not None and plan['plate'].get_width() >= 128
    assert plan['frame'] == KT.GOLD_HI
    assert lore_art.cached('item', feast['recipe']['art'])
    plain = _row_for(g, 'cook_goblin')
    assert g._cook_detail_plan(rect, plain)['frame'] is None
    # The art id is read from the recipe: new pictures need no code change.
    from renderer import _resolve_item_sprite_path
    art = next(r['art'] for r in kitchen.book()
               if r.get('art') and r['art'] != plain['recipe'].get('art')
               and _resolve_item_sprite_path(r['art']))
    lore_art.clear_cache()
    other = dict(plain, id='__x__', recipe=dict(plain['recipe'], id='__x__', art=art))
    assert g._cook_detail_plan(rect, other)['plate'] is not None
    assert lore_art.cached('item', art)


def test_no_art_means_no_picture_never_a_glyph():
    g = _game()
    plain = _row_for(g, 'cook_goblin')
    none = dict(plain, id='__none__', recipe=dict(plain['recipe'], id='__none__',
                                                   art='__no_such_art__'))
    assert g._cook_detail_plan(pygame.Rect(0, 0, 400, 600), none)['plate'] is None
    # The row's small icon falls back to the first ingredient's own art...
    icon = g._cook_dish_icon(none['recipe'])
    assert icon is not None
    # ...and with none anywhere it is left empty.
    bare = dict(none['recipe'], id='__bare__', ingredients=['__nothing__'])
    assert g._cook_dish_icon(bare) is None


# ---------------------------------------------------------------------------
# The words (cook_menu.py, pure)
# ---------------------------------------------------------------------------

def test_window_keeps_the_focus_in_view():
    hs = [10] * 10
    assert cook_menu.window(hs, 0, 200) == (0, 10)
    assert cook_menu.window(hs, 0, 35) == (0, 3)
    assert cook_menu.window(hs, 5, 35) == (3, 6)
    assert cook_menu.window(hs, 9, 35) == (7, 10)
    assert cook_menu.window([], 0, 35) == (0, 0)
    # A header (item 3) never waits alone at the foot, its rows below.
    assert cook_menu.window(hs, 0, 40, heads={3}) == (0, 3)
    assert cook_menu.window(hs, 0, 40, heads={2}) == (0, 4)


def test_fit_list_counts_what_does_not_fit_rather_than_cutting_it():
    names = ['Wyvern Tail', 'Hard Cheese', 'River Salt']
    assert cook_menu.fit_list('Needs: ', names, lambda t: True) == \
        'Needs: Wyvern Tail, Hard Cheese, River Salt'
    assert cook_menu.fit_list('Needs: ', names, lambda t: len(t) <= 36) == \
        'Needs: Wyvern Tail and 2 more'
    assert '...' not in cook_menu.fit_list('Needs: ', names, lambda t: False)


def test_chip_says_what_a_ready_dish_does_or_how_close_one_is():
    from player import Player
    p = Player()
    counts = kitchen.held_counts([])
    hp = kitchen._row(p, kitchen.recipe('cook_cave_bear'), counts)
    assert cook_menu.chip_text(hp) == hp['progress'] == '0 of 1'
    for rid, want in (('cook_cave_bear', '+'), ('cook_fire_beetle', 'Dark Vision')):
        row = dict(kitchen._row(p, kitchen.recipe(rid), counts), ready=True)
        assert cook_menu.chip_text(row).startswith(want), rid
    half = dict(kitchen._row(p, kitchen.recipe('cook_cobra'), counts), ready=True)
    assert cook_menu.chip_text(half) == 'Teaches DEX'
    full = dict(half, effects=['Teaches DEX (a full point)'])
    assert cook_menu.chip_text(full) == 'DEX +1'
    used = dict(half, effects=['DEX lesson used this floor'])
    assert cook_menu.chip_text(used) == 'No DEX Lesson'


def test_part_words_say_what_to_do_about_a_missing_part():
    held = {'id': 'goblin_prime', 'name': 'Goblin Gristle', 'need': 1}
    assert cook_menu.part_words(held, 2) == ('Goblin Gristle', 'Have 2')
    assert cook_menu.part_words(held, 0) == ('Hunt Goblin Gristle', '0 of 1')
    assert cook_menu.part_words({'id': 'hard_cheese', 'name': 'Hard Cheese', 'need': 2}, 1) == \
        ('Find or buy Hard Cheese', '1 of 2')
    assert cook_menu.part_words({'id': 'river_salt', 'name': 'River Salt', 'need': 1}, 0) == \
        ('Forage or buy River Salt', '0 of 1')
    trophy = next(i for i, d in kitchen.ingredients().items() if d.get('tier_role') == 'trophy')
    assert cook_menu.part_words({'id': trophy, 'name': 'X', 'need': 1}, 0)[0] == 'Boss trophy: X'


def test_keep_together_binds_numbers_to_what_they_count():
    nb = ' '
    assert cook_menu.keep_together('Sustained, 525 turns') == f'Sustained, 525{nb}turns'
    assert cook_menu.keep_together('+2 Max HP') == f'+2{nb}Max{nb}HP'
    assert cook_menu.keep_together('Building Toward: 1 of 4') == f'Building Toward: 1{nb}of{nb}4'


def test_an_empty_tab_says_so_and_names_the_tab_that_has_something():
    ready = {'hp': 0, 'sp': 3, 'mp': 0, 'stat': 1, 'special': 0}
    rows = {'hp': 0, 'sp': 5, 'mp': 0, 'stat': 2, 'special': 4}
    line = cook_menu.empty_line('mp', ready, rows)
    assert line == 'No dish in the MP tab uses what you carry yet. Try SP: 3 dishes ready.'
    assert cook_menu.empty_line('mp', dict.fromkeys(ready, 0), dict.fromkeys(rows, 0)) == \
        'No dish in the MP tab uses what you carry yet.'
    assert cook_menu.nothing_ready_note('special', ready) == \
        'Nothing ready in Special yet. Try SP: 3 dishes ready.'
    assert cook_menu.nothing_ready_note('sp', ready) == ''


def test_reasons_read_plainly():
    p = types.SimpleNamespace(hp=7, max_hp=30, sp=100, max_sp=1000, mp=2, max_mp=20)
    assert cook_menu.reason_line('hp', 'hurt', p) == 'Opened on HP: you are hurt, 7 of 30 HP'
    assert cook_menu.reason_line('sp', 'hungry', p) == 'Opened on SP: you are hungry, 100 of 1000 SP'
    assert cook_menu.reason_line('mp', 'mana', p) == 'Opened on MP: your mana is low, 2 of 20 MP'
    assert cook_menu.reason_line('stat', 'lesson', p) == \
        "Opened on Stat: this floor's stat lesson is open"
    assert cook_menu.urgent('hurt') and not cook_menu.urgent('lesson')


# ---------------------------------------------------------------------------
# kitchen.py additions K2 reads
# ---------------------------------------------------------------------------

def test_opening_choice_gives_the_tab_and_why():
    g = _game()
    _pack(g, EVERY_TAB)
    p, inv = g.player, g.player.inventory
    assert kitchen.opening_choice(p, inv) == ('stat', 'lesson')
    assert kitchen.opening_tab(p, inv) == 'stat'
    p.hp = 1
    assert kitchen.opening_choice(p, inv) == ('hp', 'hurt')
    p.hp = p.max_hp
    p.sp = 1
    assert kitchen.opening_choice(p, inv) == ('sp', 'hungry')
    assert kitchen.opening_choice(p, []) == ('hp', 'nothing')
    assert set(kitchen.OPEN_REASONS) >= {'hurt', 'hungry', 'mana', 'lesson', 'most_ready',
                                         'most_rows', 'nothing'}


def test_dish_lasting_is_the_for_good_part_of_dish_effects():
    from player import Player
    p = Player()
    for rid in ('feast_01', 'trophy_fafnir_dragon_recipe', 'feast_05'):
        rec = kitchen.recipe(rid)
        lasting = kitchen.dish_lasting(p, rec)
        effects = kitchen.dish_effects(p, rec)
        assert lasting and all(line in effects for line in lasting), rid
    assert kitchen.dish_lasting(p, kitchen.recipe('cook_goblin')) == []


# ---------------------------------------------------------------------------
# The Kit, the Eat menu and the help say where a part's dishes are
# ---------------------------------------------------------------------------

def test_the_kit_and_eat_menu_point_a_part_at_its_tab():
    from food_system import load_ingredient_for
    from items import load_items
    g = _game()
    part = load_ingredient_for('cobra_prime')
    assert g._kit_consumable_effect(part) == kitchen.nature_line('cobra_prime')
    assert 'Stat dishes' in g._kit_consumable_effect(part)
    bread = next(f for f in load_items('food') if f.id == 'bread_ration')
    n = len(kitchen.dishes_with('bread_ration'))
    assert n > 0 and f"in {n} dishes" in g._kit_consumable_effect(bread)


def test_the_help_page_describes_the_tabbed_menu():
    import json
    with open(os.path.join(ROOT, 'data', 'ui', 'how_quizzes_work.json'), encoding='utf-8') as f:
        text = json.dumps(json.load(f))
    assert 'The cook menu (C) has a tab for each' in text
    assert 'building toward' in text and 'legendary feasts' in text.lower()
