"""Cook = ONE Recipes list; Eat = ONE combined list (2026-06-07).

After the cooking overhaul deleted basic_monster_stew, the obsolete "Single"
solo-cook tab (1) duplicated the Recipes tab and (2) let you cook a multi-
ingredient dish from a single anchor ingredient, bypassing its real cost. And
raw ingredients were stuck on a separate "Raw Ingredients" eat tab instead of
sitting with the rations. This guards both UX fixes. (The kitchen rebuild of
2026-11-14 gives every ingredient one dish of its own on the Recipes list;
the tabbed cook menu by main benefit, slice K2, will replace this test's
first half.)
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from items import Food, Ingredient
from main import Game


def test_cook_menu_has_no_single_tab():
    # exactly one tab, and it is the compound/Recipes list -- no 'single' tab
    assert [t[1] for t in Game._COOK_TABS] == ['compound']


def test_eat_menu_is_one_combined_list():
    # one tab whose filter admits BOTH rations (Food) and raw ingredients,
    # so the emergency food sits with the rations.
    assert len(Game._EAT_TABS) == 1
    admit = Game._EAT_TABS[0][1]
    assert admit(Food.__new__(Food)) is True          # bread ration, apple...
    assert admit(Ingredient.__new__(Ingredient)) is True   # a raw monster part
