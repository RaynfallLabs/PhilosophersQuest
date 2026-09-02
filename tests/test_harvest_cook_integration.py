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
    a pre-set outcome so we can drive the harvest+cook flow without
    a real game loop.

    `scripted_tier` still exists for legacy escalator_chain call sites
    (cook_compound_recipe etc.). For threshold-mode call sites (harvest v3),
    `scripted_success` decides the outcome: True → callback with
    success=True, False → success=False. `scripted_tier` also drives the
    reported chain score for chain-mode paths that read `result.score`.
    """

    def __init__(self, scripted_tier: int = 5, scripted_success: bool | None = None):
        self.tier = scripted_tier
        self.success = (scripted_tier > 0) if scripted_success is None else scripted_success
        self.last_quiz_kwargs: dict | None = None

    def start_quiz(self, **kwargs):
        self.last_quiz_kwargs = kwargs
        callback = kwargs['callback']

        class _Result:
            success = self.success
            score = self.tier if self.success else 0
            correct = self.tier if self.success else 0
            asked = 5
        callback(_Result())


class MockCorpse:
    """Minimal corpse shape for harvest_corpse."""
    def __init__(self, monster_id: str, name: str = None, harvest_tier: int = 1):
        self.monster_id = monster_id
        self.name = name or monster_id.replace('_', ' ').title()
        self.harvest_tier = harvest_tier
        self.x = 0
        self.y = 0


# ---------------------------------------------------------------------------
# Harvest path
# ---------------------------------------------------------------------------

def test_harvest_wrong_answer_ruins_corpse():
    """Harvest v3 (2026-09-01): a wrong quiz answer ruins the corpse.
    No ingredients, no additional debuff — losing the corpse IS the cost."""
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    corpse = MockCorpse('giant_rat', harvest_tier=3)
    quiz = MockQuizEngine(scripted_success=False)
    out = {}
    def on_complete(ings, msg):
        out['ingredients'] = ings
        out['message'] = msg
    harvest_corpse(p, corpse, quiz, on_complete)
    assert out['ingredients'] == []
    assert 'ruined' in out['message'].lower() or 'botch' in out['message'].lower()


def test_harvest_tier_3_success_returns_2_assorted_plus_family():
    """T3 corpse (family-tier monster), right answer -> full T3 haul."""
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    corpse = MockCorpse('giant_rat', harvest_tier=3)  # beast family
    quiz = MockQuizEngine(scripted_success=True)
    out = {}
    def on_complete(ings, msg):
        out['ingredients'] = ings
        out['message'] = msg
    harvest_corpse(p, corpse, quiz, on_complete)
    names = [i.name for i in out['ingredients']]
    assert names.count('Assorted Monster Jerky') == 2
    assert names.count('Beast Meat') == 1


def test_harvest_tier_5_success_includes_prime_cut():
    """T5 corpse, right answer -> prime cut included."""
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    corpse = MockCorpse('giant_rat', harvest_tier=5)
    quiz = MockQuizEngine(scripted_success=True)
    out = {}
    def on_complete(ings, msg):
        out['ingredients'] = ings
        out['message'] = msg
    harvest_corpse(p, corpse, quiz, on_complete)
    ids = [i.id for i in out['ingredients']]
    assert 'giant_rat_prime' in ids


def test_harvest_tier_5_boss_success_includes_trophy():
    """Boss corpse at T5, right answer -> trophy ingredient."""
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    corpse = MockCorpse('abaddon_destroyer', harvest_tier=5)
    quiz = MockQuizEngine(scripted_success=True)
    out = {}
    def on_complete(ings, msg):
        out['ingredients'] = ings
        out['message'] = msg
    harvest_corpse(p, corpse, quiz, on_complete)
    ids = [i.id for i in out['ingredients']]
    assert 'abaddon_destroyer_trophy' in ids


def test_harvest_quiz_uses_threshold_one_question():
    """Harvest v3 (2026-09-01): threshold mode, 1 question, no chain."""
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    corpse = MockCorpse('giant_rat', harvest_tier=1)
    quiz = MockQuizEngine(scripted_success=True)
    harvest_corpse(p, corpse, quiz, lambda i, m: None)
    kw = quiz.last_quiz_kwargs
    assert kw['mode'] == 'threshold'
    assert kw['subject'] == 'animal'
    assert kw['total_qs'] == 1
    assert kw['threshold'] == 1
    assert 'max_chain' not in kw


def test_harvest_quiz_tier_matches_corpse_harvest_tier():
    """Quiz difficulty scales to the corpse's harvest_tier — the
    intrinsic 'richness of harvest' of the monster. A sphinx (T5) demands
    a T5 animal question; a bat (T1) a T1 question."""
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    for ht in (1, 2, 3, 4, 5):
        corpse = MockCorpse('giant_rat', harvest_tier=ht)
        quiz = MockQuizEngine(scripted_success=True)
        harvest_corpse(p, corpse, quiz, lambda i, m: None)
        assert quiz.last_quiz_kwargs['tier'] == ht, \
            f"harvest_tier={ht} must produce tier={ht}, got {quiz.last_quiz_kwargs['tier']}"


def test_harvest_quiz_tier_clamps_and_defaults():
    """harvest_tier outside [1,5] clamps to 1 (safe default)."""
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    for bad, expected in ((0, 1), (7, 5), (-3, 1)):
        corpse = MockCorpse('giant_rat', harvest_tier=bad)
        quiz = MockQuizEngine(scripted_success=True)
        harvest_corpse(p, corpse, quiz, lambda i, m: None)
        assert quiz.last_quiz_kwargs['tier'] == expected, \
            f"harvest_tier={bad} should clamp to tier={expected}, got {quiz.last_quiz_kwargs['tier']}"


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
    corpse = MockCorpse('giant_rat', harvest_tier=5)
    quiz_h = MockQuizEngine(scripted_success=True)
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
