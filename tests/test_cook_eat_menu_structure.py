"""Cook = ONE Recipes list; Eat = ONE combined list (2026-06-07).

After the cooking overhaul deleted basic_monster_stew, the obsolete "Single"
solo-cook tab (1) duplicated the Recipes tab and (2) let you cook a multi-
ingredient dish from a single anchor ingredient, bypassing its real cost. And
the survival jerky was stuck on a separate "Raw Ingredients" eat tab instead of
sitting with the rations. This guards both UX fixes.
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
    # one tab whose filter admits BOTH rations (Food) and ingredients (jerky),
    # so the survival food sits with the rations.
    assert len(Game._EAT_TABS) == 1
    admit = Game._EAT_TABS[0][1]
    assert admit(Food.__new__(Food)) is True          # bread ration, apple...
    assert admit(Ingredient.__new__(Ingredient)) is True   # Assorted Monster Jerky
