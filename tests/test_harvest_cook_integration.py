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


def test_v265_harvest_gives_the_monsters_prime_at_any_tier():
    """v2.6.5: every successful harvest yields the monster's prime cut,
    regardless of harvest_tier (no more cumulative T1-T5 stack)."""
    from food_system import harvest_corpse
    from player import Player

    for ht in (1, 2, 3, 4, 5):
        p = Player()
        corpse = MockCorpse('giant_rat', harvest_tier=ht)
        quiz = MockQuizEngine(scripted_success=True)
        out = {}
        def on_complete(ings, msg):
            out['ingredients'] = ings
            out['message'] = msg
        harvest_corpse(p, corpse, quiz, on_complete)
        ids = [i.id for i in out['ingredients']]
        assert ids == ['giant_rat_prime'], f"harvest_tier={ht}: got {ids}"


def test_v265_low_tier_monsters_now_drop_their_own_prime():
    """The v2.6.5 bug fix: goblin (harvest_tier=1) never dropped goblin_prime
    under the old cumulative-T1-T5 harvest. Now it does."""
    from food_system import harvest_corpse
    from player import Player

    p = Player()
    corpse = MockCorpse('goblin', harvest_tier=1)
    quiz = MockQuizEngine(scripted_success=True)
    out = {}
    harvest_corpse(p, corpse, quiz, lambda ings, msg: out.update(ingredients=ings))
    ids = [i.id for i in out['ingredients']]
    assert ids == ['goblin_prime']


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
    # A deep creature (floor 80+), so its own floor band does not hold the
    # tier down: see test_harvest_is_never_harder_than_the_monsters_floor.
    for ht in (1, 2, 3, 4, 5):
        corpse = MockCorpse('arch_lich', harvest_tier=ht)
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
        corpse = MockCorpse('arch_lich', harvest_tier=bad)
        quiz = MockQuizEngine(scripted_success=True)
        harvest_corpse(p, corpse, quiz, lambda i, m: None)
        assert quiz.last_quiz_kwargs['tier'] == expected, \
            f"harvest_tier={bad} should clamp to tier={expected}, got {quiz.last_quiz_kwargs['tier']}"


# ---------------------------------------------------------------------------
# Cook path
# ---------------------------------------------------------------------------

def test_cook_family_recipe_restores_sp():
    """Cook a two-part dish (Goblin Gristle + Charybdis Spawn Shank): it
    restores SP and consumes exactly the dish's ingredients."""
    from food_system import load_ingredient_for, cook_compound_recipe, _raw_recipes
    from player import Player

    p = Player()
    p.sp = 100  # plenty of headroom

    recipe = {'id': 'dish_094', **_raw_recipes()['dish_094']}
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


def test_cook_a_special_dish_applies_its_power():
    """A Special dish (Gloom-Jelly on Toast) puts its timed power on the hero."""
    import kitchen
    from food_system import load_ingredient_for, cook_compound_recipe
    from player import Player

    p = Player()
    recipe = kitchen.recipe('cook_shade')
    for ing_id in recipe['ingredients']:
        p.add_to_inventory(load_ingredient_for(ing_id))
    quiz = MockQuizEngine(scripted_success=True)
    cook_compound_recipe(p, recipe, p.inventory, quiz, lambda msgs: None)
    assert p.has_effect(kitchen.dish_power(recipe)), p.status_effects


def test_cook_v3_uses_threshold_one_question():
    """Cook v3 (2026-09-01): threshold mode, 1 Q, no chain."""
    from food_system import load_ingredient_for, cook_compound_recipe, _raw_recipes
    from player import Player

    p = Player()
    recipe = {'id': 'dish_094', **_raw_recipes()['dish_094']}
    for ing_id in recipe['ingredients']:
        p.add_to_inventory(load_ingredient_for(ing_id))
    quiz = MockQuizEngine(scripted_success=True)
    cook_compound_recipe(p, recipe, p.inventory, quiz, lambda m: None)
    kw = quiz.last_quiz_kwargs
    assert kw['mode'] == 'threshold'
    assert kw['subject'] == 'cooking'
    assert kw['total_qs'] == 1
    assert kw['threshold'] == 1
    assert 'max_chain' not in kw


def test_cook_v3_tier_matches_the_dish_tier():
    """The cooking question's tier is the dish's tier: the band of its
    deepest ingredient (kitchen.dish_tier)."""
    import kitchen
    from food_system import load_ingredient_for, cook_compound_recipe
    from player import Player

    first_per_tier = {}
    for r in kitchen.book():
        if all(load_ingredient_for(i) is not None for i in r['ingredients']):
            first_per_tier.setdefault(kitchen.dish_tier(r), r)
    # the recipe book spans the whole tier ladder
    assert sorted(first_per_tier) == [1, 2, 3, 4, 5]

    for expected, recipe in sorted(first_per_tier.items()):
        p = Player()
        for ing_id in recipe['ingredients']:
            p.add_to_inventory(load_ingredient_for(ing_id))
        quiz = MockQuizEngine(scripted_success=True)
        cook_compound_recipe(p, recipe, p.inventory, quiz, lambda m: None)
        assert quiz.last_quiz_kwargs['tier'] == expected, \
            f"{recipe['id']} should ask tier {expected}, got {quiz.last_quiz_kwargs['tier']}"


def test_cook_v3_success_gives_peak_reward():
    """Cook v3: right answer -> T5 outcome regardless of Q tier."""
    from food_system import load_ingredient_for, cook_compound_recipe, _raw_recipes
    from player import Player

    p = Player()
    p.sp = 100
    recipe = {'id': 'dish_094', **_raw_recipes()['dish_094']}
    for ing_id in recipe['ingredients']:
        p.add_to_inventory(load_ingredient_for(ing_id))
    quiz = MockQuizEngine(scripted_success=True)
    cook_compound_recipe(p, recipe, p.inventory, quiz, lambda m: None)
    # An SP dish of two parts: far more than a ration.
    assert p.sp > 100, "success on family cook must restore SP"
    assert p.sp - 100 >= 40, f"expected meaningful SP gain, got +{p.sp - 100}"


def test_cook_v3_failure_ruins_and_consumes():
    """Cook v3: wrong answer -> ingredients consumed AND ruined."""
    from food_system import load_ingredient_for, cook_compound_recipe, _raw_recipes
    from player import Player
    from items import Ingredient

    p = Player()
    p.sp = 100
    recipe = {'id': 'dish_094', **_raw_recipes()['dish_094']}
    for ing_id in recipe['ingredients']:
        p.add_to_inventory(load_ingredient_for(ing_id))
    quiz = MockQuizEngine(scripted_success=False)
    out = {}
    cook_compound_recipe(p, recipe, p.inventory, quiz, lambda msgs: out.update(messages=msgs))
    # Ingredients consumed (even on failure — matches harvest v3 "resource loss IS the cost")
    assert len([i for i in p.inventory if isinstance(i, Ingredient)]) == 0
    # SP unchanged (no reward)
    assert p.sp == 100
    # Message reflects ruin
    assert out['messages'][0].startswith('You ruin the preparation')


def test_cook_consumes_inventory_even_on_ruin():
    """Even at T0 (ruined), the ingredients are still consumed — design intent.

    """
    from food_system import load_ingredient_for, cook_compound_recipe, _raw_recipes
    from player import Player

    p = Player()
    recipe = {'id': 'dish_094', **_raw_recipes()['dish_094']}
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

    # v2.6.5: harvest a giant_rat → get 1 giant_rat_prime (just the ingredient)
    corpse = MockCorpse('giant_rat', harvest_tier=1)
    quiz_h = MockQuizEngine(scripted_success=True)
    out_h = {}
    def on_harvest(ings, msg):
        out_h['ingredients'] = ings
        out_h['msg'] = msg
        for ing in ings:
            p.add_to_inventory(ing)
    harvest_corpse(p, corpse, quiz_h, on_harvest)
    assert len(out_h['ingredients']) == 1
    assert out_h['ingredients'][0].id == 'giant_rat_prime'

    # Cook the part on its own (its single dish)
    rid = 'cook_giant_rat'
    recipe = {'id': rid, **_raw_recipes()[rid]}
    quiz_c = MockQuizEngine(scripted_success=True)
    out_c = {}
    cook_compound_recipe(p, recipe, p.inventory, quiz_c,
                         lambda msgs: out_c.update(messages=msgs))

    # SP should be higher (Rat Rump Kebab: an SP dish)
    assert p.sp > 100


def test_harvest_is_never_harder_than_the_monsters_floor():
    """Monsters were re-seated by HP and their harvest tiers were not: 156
    creatures of floors 1 to 19 asked tier 3 to 5 animal questions."""
    from food_system import harvest_corpse, _monster_band_tier
    from player import Player

    assert _monster_band_tier('giant_rat') == 1
    assert _monster_band_tier('no_such_monster') == 5
    p = Player()
    for ht in (1, 3, 5):
        corpse = MockCorpse('giant_rat', harvest_tier=ht)
        quiz = MockQuizEngine(scripted_success=True)
        harvest_corpse(p, corpse, quiz, lambda i, m: None)
        assert quiz.last_quiz_kwargs['tier'] == 1


def test_a_monster_with_no_cut_of_its_own_still_feeds_the_pot():
    from food_system import _harvest_outcome_for_tier
    from food_system import load_ingredient_for
    got = _harvest_outcome_for_tier(2, 'bonnacon')
    assert len(got) == 1 and load_ingredient_for(got[0]) is not None
    boar = _harvest_outcome_for_tier(4, 'calydonian_boar')
    assert len(boar) == 1 and load_ingredient_for(boar[0]) is not None
    assert _harvest_outcome_for_tier(0, 'bonnacon') == []
