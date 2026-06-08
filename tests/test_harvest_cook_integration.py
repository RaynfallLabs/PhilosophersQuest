"""Integration tests for the 2026-05-31 harvest+cook redesign.

Simulates the full lifecycle using a mock quiz engine:
  1. Make a corpse for a monster
  2. Call harvest_corpse with a mock quiz that "scores" tier N
  3. Verify the right ingredients land in the player's inventory
  4. Cook one of those ingredients via cook_ingredient
  5. Verify SP/HP/stat outcomes
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


class MockQuizEngine:
    """Fakes QuizEngine.start_quiz — fires the callback immediately with
    a pre-set tier score so we can drive the harvest+cook flow without
    a real game loop."""

    def __init__(self, scripted_tier: int):
        self.tier = scripted_tier
        self.last_quiz_kwargs: dict | None = None

    def start_quiz(self, **kwargs):
        self.last_quiz_kwargs = kwargs
        callback = kwargs['callback']

        class _Result:
            success = True
            score = self.tier
            correct = self.tier
            asked = 5
        callback(_Result())


class MockCorpse:
    """Minimal corpse shape for harvest_corpse."""
    def __init__(self, monster_id: str, name: str = None):
        self.monster_id = monster_id
        self.name = name or monster_id.replace('_', ' ').title()
        self.harvest_tier = 1
        self.x = 0
        self.y = 0


# ---------------------------------------------------------------------------
# Harvest path
# ---------------------------------------------------------------------------

def test_harvest_tier_0_returns_no_ingredients():
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    corpse = MockCorpse('giant_rat')
    quiz = MockQuizEngine(scripted_tier=0)
    out = {}
    def on_complete(ings, msg):
        out['ingredients'] = ings
        out['message'] = msg
    harvest_corpse(p, corpse, quiz, on_complete)
    assert out['ingredients'] == []
    assert 'ruined' in out['message'].lower() or 'botch' in out['message'].lower()


def test_harvest_tier_3_returns_2_assorted_plus_family():
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    corpse = MockCorpse('giant_rat')  # beast family
    quiz = MockQuizEngine(scripted_tier=3)
    out = {}
    def on_complete(ings, msg):
        out['ingredients'] = ings
        out['message'] = msg
    harvest_corpse(p, corpse, quiz, on_complete)
    names = [i.name for i in out['ingredients']]
    # Renamed to "Assorted Monster Jerky" in the 2026-06-07 cooking overhaul.
    assert names.count('Assorted Monster Jerky') == 2
    assert names.count('Beast Meat') == 1


def test_harvest_tier_5_includes_prime_cut():
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    corpse = MockCorpse('giant_rat')
    quiz = MockQuizEngine(scripted_tier=5)
    out = {}
    def on_complete(ings, msg):
        out['ingredients'] = ings
        out['message'] = msg
    harvest_corpse(p, corpse, quiz, on_complete)
    ids = [i.id for i in out['ingredients']]
    assert 'giant_rat_prime' in ids


def test_harvest_tier_5_boss_includes_trophy():
    """Boss harvest at T5 yields the trophy ingredient (not regular prime)."""
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    corpse = MockCorpse('abaddon_destroyer')
    quiz = MockQuizEngine(scripted_tier=5)
    out = {}
    def on_complete(ings, msg):
        out['ingredients'] = ings
        out['message'] = msg
    harvest_corpse(p, corpse, quiz, on_complete)
    ids = [i.id for i in out['ingredients']]
    assert 'abaddon_destroyer_trophy' in ids


def test_harvest_quiz_uses_escalator_chain_mode():
    """Verify the quiz mode swapped from threshold → escalator_chain."""
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    corpse = MockCorpse('giant_rat')
    quiz = MockQuizEngine(scripted_tier=1)
    harvest_corpse(p, corpse, quiz, lambda i, m: None)
    assert quiz.last_quiz_kwargs['mode'] == 'escalator_chain'
    assert quiz.last_quiz_kwargs['subject'] == 'animal'
    assert quiz.last_quiz_kwargs['max_chain'] == 5


def test_harvest_always_starts_at_tier_1():
    """Bug fix 2026-05-31: legacy `harvest_tier` field on monsters used to
    leak through as the starting tier, making escalator_chain skip T1-T3
    and put the player into T4/T5 questions from the first answer. Every
    harvest must now START at T1 regardless of the monster's old tier."""
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    # MockCorpse defaults to harvest_tier=1, but force a legacy high value
    corpse = MockCorpse('giant_rat')
    corpse.harvest_tier = 5  # simulate a stale monster JSON
    quiz = MockQuizEngine(scripted_tier=2)
    harvest_corpse(p, corpse, quiz, lambda i, m: None)
    assert quiz.last_quiz_kwargs['tier'] == 1, \
        f"harvest must start at T1; got {quiz.last_quiz_kwargs['tier']}"


# ---------------------------------------------------------------------------
# Cook path
# ---------------------------------------------------------------------------

def test_cook_family_recipe_restores_sp():
    """Cook a family roast (2 family + 4 assorted): should restore SP and
    consume exactly the recipe's ingredients.

    2026-06-07: basic_monster_stew was DELETED (assorted parts are now eaten as
    Assorted Monster Jerky, not cooked). The family recipe is the new cheapest
    compound cook, so this exercises the same cook_compound_recipe path.
    """
    from food_system import load_ingredient_for, cook_compound_recipe, _raw_recipes
    from player import Player

    p = Player()
    p.sp = 100  # plenty of headroom

    recipe = {'id': 'family_beast_recipe', **_raw_recipes()['family_beast_recipe']}
    # Build EXACTLY the recipe's ingredients (2x family_beast + 4x assorted).
    for ing_id in recipe['ingredients']:
        p.add_to_inventory(load_ingredient_for(ing_id))

    quiz = MockQuizEngine(scripted_tier=2)
    out = {}
    def on_complete(messages):
        out['messages'] = messages
    cook_compound_recipe(p, recipe, p.inventory, quiz, on_complete)

    # SP should have increased by the T2 amount.
    assert p.sp > 100
    # Every listed ingredient consumed (one pop per list entry).
    from items import Ingredient
    remaining = [i for i in p.inventory if isinstance(i, Ingredient)]
    assert len(remaining) == 0


def test_cook_prime_recipe_at_t5_applies_temp_power():
    """T5 cook of a prime recipe should apply the lore-themed temp power."""
    from food_system import load_ingredient_for, cook_compound_recipe, _raw_recipes
    from player import Player

    p = Player()

    # Pick the first existing beast prime recipe so we don't depend on a
    # specific monster being named in this exact form.
    rid = next((k for k in _raw_recipes().keys()
                if k.startswith('prime_giant_rat')), None)
    assert rid is not None, "no prime_giant_rat recipe found"
    recipe_def = _raw_recipes()[rid]
    # Build the required ingredients from the recipe definition
    for ing_id in recipe_def['ingredients']:
        ing = load_ingredient_for(ing_id)
        if ing is not None:
            p.add_to_inventory(ing)

    recipe = {'id': rid, **recipe_def}
    quiz = MockQuizEngine(scripted_tier=5)
    out = {}
    cook_compound_recipe(p, recipe, p.inventory, quiz, lambda msgs: out.update(messages=msgs))

    # Temp power should be applied as a canonical status effect
    # (the redesign-friendly name gets remapped via _resolve_temp_power)
    from food_system import _resolve_temp_power
    raw = recipe.get('temp_power', 'night_vision')
    canonical = _resolve_temp_power(raw)
    assert p.has_effect(canonical), \
        f"expected {canonical} (remapped from {raw}) status active, got {p.status_effects}"


def test_cook_consumes_inventory_even_on_ruin():
    """Even at T0 (ruined), the ingredients are still consumed — design intent.

    2026-06-07: uses the family recipe now that basic_monster_stew is gone.
    """
    from food_system import load_ingredient_for, cook_compound_recipe, _raw_recipes
    from player import Player

    p = Player()
    recipe = {'id': 'family_beast_recipe', **_raw_recipes()['family_beast_recipe']}
    for ing_id in recipe['ingredients']:
        p.add_to_inventory(load_ingredient_for(ing_id))

    quiz = MockQuizEngine(scripted_tier=0)
    out = {}
    cook_compound_recipe(p, recipe, p.inventory, quiz, lambda msgs: out.update(messages=msgs))

    from items import Ingredient
    remaining = [i for i in p.inventory if isinstance(i, Ingredient)]
    assert len(remaining) == 0, "T0 ruined must still consume the ingredients"


def test_full_lifecycle_harvest_then_cook():
    """End-to-end: harvest a corpse → automatically cook the ingredients gained."""
    from food_system import harvest_corpse, cook_compound_recipe, _raw_recipes
    from player import Player

    p = Player()
    p.sp = 100
    p.hp = 20

    # Harvest a giant_rat at T5 → get 2 Assorted + 2 Beast + 1 Rat Prime
    corpse = MockCorpse('giant_rat')
    quiz_h = MockQuizEngine(scripted_tier=5)
    out_h = {}
    def on_harvest(ings, msg):
        out_h['ingredients'] = ings
        out_h['msg'] = msg
        # Add them to inventory manually (mimicking main.py call site)
        for ing in ings:
            p.add_to_inventory(ing)
    harvest_corpse(p, corpse, quiz_h, on_harvest)
    assert len(out_h['ingredients']) == 5

    # Now cook the prime recipe — needs 1 rat_prime + 1 beast + 2 assorted
    rid = 'prime_giant_rat_recipe'
    recipe = {'id': rid, **_raw_recipes()[rid]}
    quiz_c = MockQuizEngine(scripted_tier=5)
    out_c = {}
    cook_compound_recipe(p, recipe, p.inventory, quiz_c,
                         lambda msgs: out_c.update(messages=msgs))

    # SP should be much higher
    assert p.sp >= 100 + 60  # at least T5 SP amount
    # Stat grant should have applied (against floor cap)
    assert p._cook_stat_gain_this_floor > 0
