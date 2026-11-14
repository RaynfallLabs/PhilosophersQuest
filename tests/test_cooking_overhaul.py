"""Cooking data + behaviour tests, rewritten for the kitchen rebuild (2026-11-14).

What still holds from the 2026-06-07 overhaul and v2.6.5:

  * no Assorted Monster Parts, no family cuts, no basic stew;
  * every monster part is safe to eat raw (the emergency floor) and never
    poisons;

and the recipe book's shape since the rebuild (COOKING_REBUILD_PLAN_2026_11_14):

  * every ingredient cooks alone in exactly one dish, and is in at least two
    dishes of 2 to 5 ingredients;
  * the fourteen boss trophies each have a dish of their own;
  * every dish names real ingredients or rations;
  * a pack with nothing cookable says so and opens no menu.

Fuller kitchen tests live in tests/test_kitchen_rebuild.py.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

DATA = ROOT / "data" / "items"
RECIPES = json.loads((DATA / "recipes.json").read_text(encoding="utf-8"))
INGREDIENTS = json.loads((DATA / "ingredient.json").read_text(encoding="utf-8"))
FOOD = json.loads((DATA / "food.json").read_text(encoding="utf-8"))

ASSORTED = "assorted_monster_parts"


class _MockPlayer:
    """Minimal player for eat_raw: tracks SP + effects."""
    def __init__(self):
        self.sp = 0
        self.hp = 50
        self.effects = {}

    def restore_sp(self, amt):
        self.sp += amt

    def restore_hp(self, amt):
        self.hp += amt

    def add_effect(self, name, dur):
        self.effects[name] = dur
        return True

    def has_effect(self, name):
        return name in self.effects


# ---------------------------------------------------------------------------
# (A) The emergency floor: raw monster parts
# ---------------------------------------------------------------------------

def test_assorted_monster_parts_is_removed():
    assert ASSORTED not in INGREDIENTS


def test_family_cuts_are_removed():
    assert [k for k in INGREDIENTS if k.startswith("family_")] == []


def test_every_monster_part_is_edible_raw():
    for ing_id, ing in INGREDIENTS.items():
        if ing.get("tier_role") != "prime":
            continue
        assert ing.get("edible_safe") is True, f"{ing_id} not edible_safe"
        assert 5 <= int(ing.get("raw_sp", 0) or 0) <= 40, ing_id


def test_eat_raw_part_never_poisons():
    import food_system
    from food_system import load_ingredient_for
    for _ in range(300):
        pl = _MockPlayer()
        part = load_ingredient_for("giant_rat_prime")
        assert part is not None
        food_system.eat_raw(pl, part)
        assert "poisoned" not in pl.effects


# ---------------------------------------------------------------------------
# (B) Gone for good
# ---------------------------------------------------------------------------

def test_basic_stew_deleted():
    assert "basic_monster_stew" not in RECIPES


def test_assorted_parts_load_as_nothing():
    from food_system import load_ingredient_for
    assert load_ingredient_for(ASSORTED) is None


# ---------------------------------------------------------------------------
# (C) The book's shape
# ---------------------------------------------------------------------------

def test_one_single_dish_and_two_multi_dishes_per_ingredient():
    singles, multis = Counter(), Counter()
    for r in RECIPES.values():
        parts = set(r["ingredients"])
        for p in parts:
            (singles if len(parts) == 1 else multis)[p] += 1
    for ing_id in INGREDIENTS:
        assert singles[ing_id] == 1, ing_id
        assert multis[ing_id] >= 2, ing_id


def test_trophy_dishes_are_the_trophy_alone():
    troph = {rid: r for rid, r in RECIPES.items() if rid.startswith("trophy_")}
    assert len(troph) == 14
    for rid, r in troph.items():
        assert len(r["ingredients"]) == 1 and r["ingredients"][0].endswith("_trophy"), rid
        assert r.get("trophy") is True and r.get("permanent"), rid


def test_every_recipe_references_existing_ingredients():
    broken = {rid: [i for i in r["ingredients"] if i not in INGREDIENTS and i not in FOOD]
              for rid, r in RECIPES.items()}
    broken = {k: v for k, v in broken.items() if v}
    assert not broken, dict(list(broken.items())[:10])


def test_every_dish_names_one_main_benefit():
    import kitchen
    for rid, r in RECIPES.items():
        assert kitchen.dish_tab({'id': rid, **r}) in kitchen.MENU_TABS, rid


# ---------------------------------------------------------------------------
# (D) Cook menu with nothing cookable (play-reachable)
# ---------------------------------------------------------------------------

def _headless_game(name="cooktest"):
    import pygame as _pg
    _pg.init()
    from main import Game
    return Game(_pg.display.set_mode((1, 1)), player_name=name)


def test_cook_menu_with_nothing_cookable_says_so():
    from game_states import STATE_PLAYER
    g = _headless_game()
    g.player.inventory = []
    g.state = STATE_PLAYER
    g._open_cook_menu()
    assert g.cook_compound_recipes == []
    assert g.state == STATE_PLAYER
