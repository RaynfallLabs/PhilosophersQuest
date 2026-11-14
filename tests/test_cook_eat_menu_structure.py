"""Cook = a tab per main benefit; Eat = ONE combined list.

2026-06-07: the obsolete "Single" solo-cook tab let you cook a multi-
ingredient dish from a single anchor ingredient, bypassing its real cost, and
raw ingredients were stuck on a separate "Raw Ingredients" eat tab instead of
sitting with the rations. The kitchen rebuild (2026-11-14) gives every
ingredient one dish of its own, and its cook menu (slice K2) has a tab per
main benefit (HP / SP / MP / Stat / Special) in place of the one Recipes
list; tests/test_cook_menu.py pins that menu.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from items import Food, Ingredient
from main import Game


def test_cook_menu_tabs_are_the_five_main_benefits():
    # The kitchen rebuild (K2): one tab per main benefit, every dish (single
    # ones included) in the tab of what it is for; the old one-list
    # 'Recipes' tab is gone.
    import kitchen
    assert kitchen.MENU_TABS == ('hp', 'sp', 'mp', 'stat', 'special')
    assert not hasattr(Game, '_COOK_TABS')


def test_eat_menu_is_one_combined_list():
    # one tab whose filter admits BOTH rations (Food) and raw ingredients,
    # so the emergency food sits with the rations.
    assert len(Game._EAT_TABS) == 1
    admit = Game._EAT_TABS[0][1]
    assert admit(Food.__new__(Food)) is True          # bread ration, apple...
    assert admit(Ingredient.__new__(Ingredient)) is True   # a raw monster part
