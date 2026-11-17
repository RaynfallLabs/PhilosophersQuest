"""Hunting for a dish (Brandon, 2026-11-16): "for recipes in progress, you
should be able to toggle it to 'hunt' for the ingredients, meaning a monster
or ingredient you need is gold text in the right panel (instead of shades of
green or red); no limit to how many you can hunt at once".

H in the cook menu, on a dish still missing parts, hunts it (and H again
stops); the hunted dishes live on the Player (kitchen.hunted) and go into the
save; what they still need shows gold under In Sight
(hud_context.visible_context_rows): a creature whose harvest gives it, a part
lying in view. A part held stops being gold; a dish cooked leaves the hunt.
Real keys drive a headless Game. How it looks to a kid is a play-test
question: Claude cannot drive Pygame.
"""
import copy
import os
import pickle
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

import cook_menu  # noqa: E402
import kitchen  # noqa: E402

pygame.init()

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
    g = Game(pygame.display.set_mode(size), player_name='__test_cook_hunt__')
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


def _open_on(g, tab, rid):
    _press(g, pygame.K_c, 'c')
    while g._cook_tab_slug() != tab:
        _press(g, pygame.K_RIGHT)
    ids = [r['id'] for r in g._cook_tab_rows()]
    for _ in range(ids.index(rid)):
        _press(g, pygame.K_DOWN)
    return g._cook_tab_rows()[g._cook_sel]


def _monster_for(part):
    """A creature kind whose harvest gives ``part``."""
    for kind, iid in (kitchen.harvest_map().get('monsters') or {}).items():
        if kitchen.resolve(iid) == part:
            return kind
    return None


def _monster(kind, x, y):
    import json
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        defs = json.load(f)
    return Monster({**defs[kind], 'id': kind}, x, y)


def test_h_hunts_a_dish_being_built_toward_and_h_again_stops():
    g = _game()
    _pack(g, EVERY_TAB)
    row = _open_on(g, 'sp', 'dish_221')
    assert row['group'] == 'building' and not row['hunted']
    assert cook_menu.footer_hint(row) == cook_menu.HINT_HUNT
    _press(g, pygame.K_h, 'h')
    row = g._cook_tab_rows()[g._cook_sel]
    assert row['hunted'] and kitchen.is_hunted(g.player, 'dish_221')
    assert cook_menu.row_line(row, g._cook_counts) == \
        "Hunting: Locust Swarmlord Drumstick, Hard Cheese"
    assert cook_menu.footer_hint(row) == cook_menu.HINT_STOP
    texts = [str(e[0]) for e in g.msg_log.entries[-2:]]
    assert any('You are hunting for' in t for t in texts)
    g.render()                                   # the hunted row and its gold parts draw
    _press(g, pygame.K_h, 'h')
    assert not g._cook_tab_rows()[g._cook_sel]['hunted']
    assert not kitchen.is_hunted(g.player, 'dish_221')


def test_there_is_no_limit_and_a_ready_dish_has_nothing_to_hunt():
    g = _game()
    _pack(g, EVERY_TAB)
    building = [r for t in kitchen.MENU_TABS for r in kitchen.menu_rows(g.player, g.player.inventory, t)
                if not r['ready']]
    for r in building:
        kitchen.toggle_hunt(g.player, r['id'])
    assert len(kitchen.hunted(g.player)) == len(building) > 5
    # H on a ready dish hunts nothing.
    g.player.hunted_dishes = set()
    _press(g, pygame.K_c, 'c')
    ready = next(i for i, r in enumerate(g._cook_tab_rows()) if r['ready'])
    g._cook_sel = ready
    _press(g, pygame.K_h, 'h')
    assert not kitchen.hunted(g.player)
    assert cook_menu.footer_hint(g._cook_tab_rows()[ready]) == cook_menu.HINT_READY


def test_the_hunt_is_kept_in_the_save_and_an_old_save_has_none():
    from player import Player
    p = Player()
    kitchen.toggle_hunt(p, 'dish_221')
    kitchen.toggle_hunt(p, 'feast_01')
    q = pickle.loads(pickle.dumps(p))
    assert kitchen.hunted(q) == {'dish_221', 'feast_01'}
    old = Player()
    del old.__dict__['hunted_dishes']            # a save from before the hunt
    assert kitchen.hunted(old) == set() and old.hunted_dishes == set()


def test_a_hunted_part_shows_gold_in_sight_until_it_is_held():
    from hud_context import HUNT, visible_context_rows
    from fantasy_ui import FP
    from player import Player
    assert HUNT == FP.GOLD_BRIGHT
    p = Player()
    p.x, p.y = 5, 5
    rec = kitchen.recipe('dish_221')
    part = next(x for x in kitchen.parts(rec)
                if kitchen.part_kind(x) == 'monster' and _monster_for(x))
    kind = _monster_for(part)
    m = _monster(kind, 7, 5)
    other = _monster('goblin' if kind != 'goblin' else 'kobold', 8, 5)
    visible = {(7, 5), (8, 5), (6, 6)}
    rows, _items = visible_context_rows(p, [m, other], [], visible, 1)
    assert not any(r.hunted for r in rows)            # nothing hunted yet
    kitchen.toggle_hunt(p, 'dish_221')
    assert part in kitchen.hunted_parts(p)
    rows, _items = visible_context_rows(p, [m, other], [], visible, 1)
    gold = [r for r in rows if r.hunted]
    assert len(gold) == 1 and gold[0].color == HUNT
    assert all(r.color != HUNT for r in rows if not r.hunted)
    # A hunted part lying in view is gold in the Items list too.
    from food_system import load_ingredient_for
    lying = load_ingredient_for(part)
    lying.x, lying.y = 6, 6
    _rows, items = visible_context_rows(p, [], [lying], visible, 1)
    assert items and items[0].hunted and items[0].color == HUNT
    # Held in the number the dish needs: no longer hunted, no longer gold.
    held = load_ingredient_for(part)
    held.count = kitchen.needs(rec)[part]
    p.inventory.append(held)
    assert part not in kitchen.hunted_parts(p)
    rows, items = visible_context_rows(p, [m], [lying], visible, 1)
    assert not any(r.hunted for r in rows + items)


def test_a_dish_cooked_leaves_the_hunt():
    from player import Player
    p = Player()
    rec = kitchen.recipe('cook_cobra')
    kitchen.toggle_hunt(p, 'cook_cobra')
    kitchen.toggle_hunt(p, 'dish_221')
    kitchen.apply_dish(p, rec)
    assert kitchen.hunted(p) == {'dish_221'}


def test_the_help_page_says_how_to_hunt():
    import json
    with open(os.path.join(ROOT, 'data', 'ui', 'how_quizzes_work.json'), encoding='utf-8') as f:
        text = json.dumps(json.load(f))
    assert 'H hunts for it' in text and 'gold under In Sight' in text
