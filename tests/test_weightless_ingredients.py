"""Ingredients weigh nothing, and the eat menu (U) lists the dungeon's food
first, then the raw ingredients (Brandon, 2026-11-16)."""
import os
import pickle
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from items import Food, Ingredient, make_item_by_id  # noqa: E402
from player import Player  # noqa: E402


def _part():
    item = make_item_by_id('ingredient', 'aboleth_lesser_prime')
    assert isinstance(item, Ingredient)
    return item


def test_an_ingredient_weighs_nothing_in_any_number():
    part = _part()
    part.count = 12
    assert part.weight == 0.0
    assert Player._item_weight(part) == 0.0


def test_carrying_ingredients_adds_nothing_to_the_load():
    p = Player()
    before = p.get_current_weight()
    for _ in range(30):
        p.inventory.append(_part())
    assert p.get_current_weight() == before


def test_an_old_saves_pickled_weight_is_ignored():
    part = _part()
    part.__dict__['weight'] = 0.25          # what an old save carried
    back = pickle.loads(pickle.dumps(part))
    assert back.weight == 0.0


def test_food_still_has_its_weight():
    food = make_item_by_id('food', 'magic_dungeon_carrot')
    assert isinstance(food, Food) and food.weight > 0


def test_the_eat_menu_lists_food_first_then_raw_ingredients():
    import game_menus
    part_a, part_b = _part(), _part()
    food = make_item_by_id('food', 'magic_dungeon_carrot')
    fake = types.SimpleNamespace(
        player=types.SimpleNamespace(inventory=[part_a, food, part_b]),
        _EAT_TABS=[('Food', lambda i: isinstance(i, (Food, Ingredient)))],
        add_message=lambda *a, **k: None,
        state=None)
    game_menus.MenuMixin._open_eat_menu(fake)
    assert fake.eat_menu_items == [food, part_a, part_b]
